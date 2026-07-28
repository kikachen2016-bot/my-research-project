'use client';

import { useEffect, useRef, useState } from 'react';
import { postAiInterviewTurn } from '@/lib/api';
import type { AiInterviewMessage } from '@/lib/types';

const MAX_QUESTIONS = 5;
const MAX_RETRIES = 3;

type Phase = 'idle' | 'loading' | 'speaking' | 'listening' | 'done';

export default function AiInterviewVoicePage() {
  const [messages, setMessages] = useState<AiInterviewMessage[]>([]);
  const [phase, setPhase] = useState<Phase>('idle');
  const [error, setError] = useState('');
  const [questionNumber, setQuestionNumber] = useState(0);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [feedback, setFeedback] = useState('');

  // Mutable refs — avoid stale closures in async callbacks
  const messagesRef = useRef<AiInterviewMessage[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const ttsResolveRef = useRef<(() => void) | null>(null);
  const retryCountRef = useRef(0);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Function refs break the circular dependency between fetchAndPlay ↔ startMic
  const fetchAndPlayRef = useRef<(h: AiInterviewMessage[]) => Promise<void>>(async () => {});
  const startMicRef = useRef<() => void>(() => {});

  messagesRef.current = messages;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, feedback, phase, liveTranscript]);

  useEffect(() => {
    return () => {
      audioRef.current?.pause();
      recognitionRef.current?.abort();
      window.speechSynthesis?.cancel();
    };
  }, []);

  // ---------------------------------------------------------------------------
  // TTS: OpenAI audio (base64 MP3) → fallback to Web Speech API
  // ---------------------------------------------------------------------------
  async function playTts(content: string, audioBase64: string): Promise<void> {
    return new Promise((resolve) => {
      ttsResolveRef.current = resolve;

      const done = () => {
        if (ttsResolveRef.current === resolve) {
          ttsResolveRef.current = null;
          resolve();
        }
      };

      if (audioBase64) {
        const audio = new Audio(`data:audio/mpeg;base64,${audioBase64}`);
        audioRef.current = audio;
        audio.onended = done;
        audio.onerror = () => speakWebSpeech(content, done);
        audio.play().catch(() => speakWebSpeech(content, done));
      } else {
        speakWebSpeech(content, done);
      }
    });
  }

  function speakWebSpeech(text: string, onEnd: () => void) {
    const synth = window.speechSynthesis;
    if (!synth) { onEnd(); return; }
    synth.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = 'ja-JP';
    u.rate = 0.9;
    u.onend = onEnd;
    u.onerror = onEnd;
    const doSpeak = () => synth.speak(u);
    if (synth.getVoices().length > 0) doSpeak();
    else synth.addEventListener('voiceschanged', doSpeak, { once: true });
  }

  function skipSpeech() {
    audioRef.current?.pause();
    audioRef.current = null;
    window.speechSynthesis?.cancel();
    const res = ttsResolveRef.current;
    ttsResolveRef.current = null;
    res?.();
  }

  // ---------------------------------------------------------------------------
  // STT: Web Speech API (Chrome推奨)
  // Auto-sends recognized text; retries silently if no speech detected
  // ---------------------------------------------------------------------------
  function startMic() {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const Ctor: (new () => SpeechRecognition) | undefined =
      (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;
    if (!Ctor) {
      setError('このブラウザは音声認識に対応していません。Google Chromeをご利用ください。');
      return;
    }

    const rec = new Ctor();
    rec.lang = 'ja-JP';
    rec.continuous = false;
    rec.interimResults = true;

    let gotFinal = false;
    let accFinal = '';
    let errorFired = false;

    rec.onresult = (e) => {
      let final = '';
      let interim = '';
      for (let i = 0; i < e.results.length; i++) {
        if (e.results[i].isFinal) final += e.results[i][0].transcript;
        else interim += e.results[i][0].transcript;
      }
      if (final) { accFinal = final; gotFinal = true; }
      setLiveTranscript(final || interim);
    };

    rec.onerror = (e) => {
      errorFired = true;
      if (e.error !== 'no-speech' && e.error !== 'aborted') {
        setError(`音声認識エラー: ${e.error}`);
      }
    };

    rec.onend = () => {
      if (errorFired) {
        if (retryCountRef.current < MAX_RETRIES) {
          retryCountRef.current++;
          setTimeout(() => startMicRef.current(), 600);
        } else {
          retryCountRef.current = 0;
          setError('マイクのアクセス許可を確認し、ページを再読み込みしてください。');
        }
        return;
      }
      if (gotFinal && accFinal.trim()) {
        retryCountRef.current = 0;
        setLiveTranscript('');
        const updated: AiInterviewMessage[] = [
          ...messagesRef.current,
          { role: 'candidate', content: accFinal.trim() },
        ];
        setMessages(updated);
        void fetchAndPlayRef.current(updated);
      } else {
        // No speech detected — retry silently
        if (retryCountRef.current < MAX_RETRIES) {
          retryCountRef.current++;
          setTimeout(() => startMicRef.current(), 300);
        } else {
          retryCountRef.current = 0;
          setError('音声が認識されませんでした。マイクに向かって話してください。');
        }
      }
    };

    recognitionRef.current = rec;
    setLiveTranscript('');
    setError('');
    rec.start();
    setPhase('listening');
  }

  // ---------------------------------------------------------------------------
  // Core conversation loop: fetch next turn → play TTS → start mic → repeat
  // ---------------------------------------------------------------------------
  async function fetchAndPlay(history: AiInterviewMessage[]) {
    setPhase('loading');
    setError('');
    try {
      const res = await postAiInterviewTurn(history, true);
      setQuestionNumber(res.question_number);

      if (res.is_final) {
        setFeedback(res.content);
        setPhase('speaking');
        await playTts(res.content, res.audio_base64);
        setPhase('done');
      } else {
        const updated = [...history, { role: 'interviewer' as const, content: res.content }];
        setMessages(updated);
        setPhase('speaking');
        await playTts(res.content, res.audio_base64);
        await new Promise<void>((r) => setTimeout(r, 100));
        startMicRef.current();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI面接官との通信に失敗しました');
      setPhase('idle');
    }
  }

  // Always keep refs pointing to latest function versions
  fetchAndPlayRef.current = fetchAndPlay;
  startMicRef.current = startMic;

  function handleStart() {
    retryCountRef.current = 0;
    void fetchAndPlay([]);
  }

  const currentQuestion =
    messages.length > 0 && messages[messages.length - 1].role === 'interviewer'
      ? messages[messages.length - 1].content
      : '';

  return (
    <div className="page-stack">
      {/* Header */}
      <section className="card">
        <div className="card-header">
          <div>
            <div className="eyebrow">AI Interview Voice（テスト版）</div>
            <h1>AI面接（音声）</h1>
          </div>
          <span className="pill">
            {phase === 'idle' && '未開始'}
            {phase === 'done' && '面接終了'}
            {phase !== 'idle' && phase !== 'done' && (
              questionNumber > 0 ? `質問 ${questionNumber} / ${MAX_QUESTIONS}` : '準備中...'
            )}
          </span>
        </div>
        <p style={{ color: 'var(--muted)', margin: 0, fontSize: 14 }}>
          ※ Google Chrome推奨。マイクのアクセス許可が必要です。
        </p>
      </section>

      {/* Interaction area */}
      <section className="card">
        {currentQuestion && (
          <div style={{ marginBottom: phase === 'speaking' ? 6 : 20 }}>
            <div className="meta-label">面接官の質問</div>
            <div className="chat-bubble interviewer" style={{ maxWidth: '100%' }}>
              <div className="chat-bubble-label">面接官（AI）</div>
              <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{currentQuestion}</p>
            </div>
            {/* speaking 中はバナーを出さず、小さなスキップだけ */}
            {phase === 'speaking' && (
              <div style={{ textAlign: 'right', marginTop: 6 }}>
                <button
                  className="button secondary"
                  style={{ fontSize: 12, padding: '4px 10px', borderRadius: 8 }}
                  onClick={skipSpeech}
                >
                  スキップ
                </button>
              </div>
            )}
          </div>
        )}

        {/* ステータスエリア — speaking 中は表示しない */}
        {phase !== 'speaking' && (
          <div className="voice-status-area">
            {phase === 'idle' && (
              <div style={{ textAlign: 'center' }}>
                <p style={{ color: 'var(--muted)', marginBottom: 20, fontSize: 15 }}>
                  ボタンを押すと面接練習が始まります
                </p>
                <button
                  className="button primary"
                  style={{ padding: '16px 40px', fontSize: 16, borderRadius: 16 }}
                  onClick={handleStart}
                >
                  面接を開始する
                </button>
              </div>
            )}

            {phase === 'loading' && (
              <div className="voice-status">
                <div className="voice-spinner" />
                <span style={{ color: 'var(--muted)', fontSize: 14 }}>少々お待ちください...</span>
              </div>
            )}

            {phase === 'listening' && (
              <div style={{ textAlign: 'center' }}>
                <div className="mic-pulse-ring">
                  <MicIcon />
                </div>
                <p style={{ color: 'var(--muted)', margin: '14px 0', fontSize: 15 }}>
                  聞いています... 回答を話してください
                </p>
                {liveTranscript && (
                  <div className="voice-transcript" style={{ textAlign: 'left', maxWidth: 480, margin: '0 auto' }}>
                    {liveTranscript}
                  </div>
                )}
              </div>
            )}

            {phase === 'done' && (
              <div className="voice-status">
                <span style={{ fontWeight: 700, fontSize: 16 }}>
                  面接が終了しました。お疲れ様でした！
                </span>
              </div>
            )}
          </div>
        )}

        {error && <p className="error-text" style={{ marginTop: 12 }}>{error}</p>}
        <div ref={bottomRef} />
      </section>

      {/* BARS Feedback */}
      {feedback && (
        <section className="card">
          <div className="card-header">
            <div>
              <div className="eyebrow">Feedback</div>
              <h2 style={{ margin: 0 }}>総合フィードバック（BARS評価）</h2>
            </div>
          </div>
          <div className="summary-box">
            <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{feedback}</p>
          </div>
        </section>
      )}

      {/* Conversation history */}
      {messages.length > 0 && (
        <section className="card">
          <div className="card-header">
            <h2 style={{ margin: 0 }}>会話履歴</h2>
          </div>
          <div className="chat-thread">
            {messages.map((m, i) => (
              <div key={i} className={`chat-bubble ${m.role}`}>
                <div className="chat-bubble-label">
                  {m.role === 'interviewer' ? '面接官（AI）' : 'あなた'}
                </div>
                <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{m.content}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function MicIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" width="36" height="36" aria-hidden="true">
      <path d="M12 15c1.66 0 3-1.34 3-3V6c0-1.66-1.34-3-3-3S9 4.34 9 6v6c0 1.66 1.34 3 3 3zm5.91-3c-.49 0-.9.36-.98.85C16.52 15.2 14.47 17 12 17s-4.52-1.8-4.93-4.15c-.08-.49-.49-.85-.98-.85-.61 0-1.09.54-1 1.14.49 3 2.89 5.35 5.91 5.78V21c0 .55.45 1 1 1s1-.45 1-1v-2.08c3.02-.43 5.42-2.78 5.91-5.78.1-.6-.39-1.14-1-1.14z" />
    </svg>
  );
}
