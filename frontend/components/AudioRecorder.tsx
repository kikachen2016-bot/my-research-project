'use client';

import { useState, useRef, useEffect } from 'react';

interface AudioRecorderProps {
  onRecordingComplete: (blob: Blob, transcript: string) => void;
}

export default function AudioRecorder({ onRecordingComplete }: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [speechSupported, setSpeechSupported] = useState(true);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const finalTranscriptRef = useRef('');

  useEffect(() => {
    const SpeechRecognition =
      (window as typeof window & { SpeechRecognition?: typeof window.SpeechRecognition; webkitSpeechRecognition?: typeof window.SpeechRecognition }).SpeechRecognition ||
      (window as typeof window & { webkitSpeechRecognition?: typeof window.SpeechRecognition }).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  const startRecording = async () => {
    setLiveTranscript('');
    setFinalTranscript('');
    finalTranscriptRef.current = '';

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        stream.getTracks().forEach((t) => t.stop());

        const captured = finalTranscriptRef.current.trim();
        setFinalTranscript(captured);
        onRecordingComplete(blob, captured);
      };

      mediaRecorder.start();

      // --- Web Speech API 文字起こし ---
      const SpeechRecognitionCtor =
        (window as typeof window & { SpeechRecognition?: typeof window.SpeechRecognition; webkitSpeechRecognition?: typeof window.SpeechRecognition }).SpeechRecognition ||
        (window as typeof window & { webkitSpeechRecognition?: typeof window.SpeechRecognition }).webkitSpeechRecognition;

      if (SpeechRecognitionCtor) {
        const recognition = new SpeechRecognitionCtor();
        recognition.lang = 'ja-JP';
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onresult = (event: SpeechRecognitionEvent) => {
          let interim = '';
          let finalPart = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const t = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              finalPart += t;
            } else {
              interim += t;
            }
          }
          if (finalPart) {
            finalTranscriptRef.current += finalPart;
          }
          setLiveTranscript(finalTranscriptRef.current + interim);
        };

        recognition.onend = () => {
          // 録音中なら再スタート（継続文字起こし）
          if (mediaRecorderRef.current?.state === 'recording') {
            recognition.start();
          }
        };

        recognition.start();
        recognitionRef.current = recognition;
      }

      setIsRecording(true);
      setRecordingTime(0);
      setAudioUrl(null);

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error('録音の開始に失敗しました:', err);
      alert('マイクの使用が許可されていないか、利用できません。');
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div style={{
      background: 'var(--bg-secondary, #f9fafb)',
      padding: '1.5rem',
      borderRadius: '12px',
      border: '2px dashed var(--border-color, #e5e7eb)',
      textAlign: 'center'
    }}>
      {!speechSupported && (
        <p style={{ color: '#f59e0b', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
          ⚠️ このブラウザはリアルタイム文字起こしに非対応です（Chrome推奨）。録音は可能です。
        </p>
      )}

      <div style={{ display: 'flex', justifyContent: 'center' }}>
        {!isRecording ? (
          <button
            type="button"
            className="button primary"
            onClick={startRecording}
          >
            🎤 録音開始
          </button>
        ) : (
          <button
            type="button"
            className="button"
            onClick={stopRecording}
            style={{ background: '#ef4444', color: 'white', border: 'none' }}
          >
            ⏹️ 録音停止 ({formatTime(recordingTime)})
          </button>
        )}
      </div>

      {/* リアルタイム文字起こし表示 */}
      {(isRecording || finalTranscript) && (
        <div style={{
          marginTop: '1rem',
          padding: '0.75rem 1rem',
          background: '#fff',
          borderRadius: '8px',
          border: '1px solid #e5e7eb',
          textAlign: 'left',
          minHeight: '60px'
        }}>
          <p style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
            {isRecording ? '🔴 文字起こし中…' : '✅ 文字起こし完了'}
          </p>
          <p style={{ fontSize: '0.9rem', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
            {liveTranscript || finalTranscript || '（まだ音声が認識されていません）'}
          </p>
        </div>
      )}

      {audioUrl && !isRecording && (
        <div style={{ marginTop: '1rem' }}>
          <p style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>録音済みオーディオ:</p>
          <audio src={audioUrl} controls style={{ width: '100%', height: '40px' }} />
        </div>
      )}
    </div>
  );
}
