'use client';

import { useEffect, useRef, useState } from 'react';
import { postAiInterviewTurn } from '@/lib/api';
import { AiInterviewMessage } from '@/lib/types';

const MAX_QUESTIONS = 5;

export default function AiInterviewPage() {
  const [messages, setMessages] = useState<AiInterviewMessage[]>([]);
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [questionNumber, setQuestionNumber] = useState(0);
  const [isFinal, setIsFinal] = useState(false);
  const [feedback, setFeedback] = useState('');
  const startedRef = useRef(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    void fetchNextTurn([]);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, feedback, loading]);

  async function fetchNextTurn(history: AiInterviewMessage[]) {
    setLoading(true);
    setError('');
    try {
      const res = await postAiInterviewTurn(history);
      setQuestionNumber(res.question_number);
      if (res.is_final) {
        setIsFinal(true);
        setFeedback(res.content);
      } else {
        setMessages([...history, { role: 'interviewer', content: res.content }]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI面接官との通信に失敗しました');
    } finally {
      setLoading(false);
    }
  }

  async function onSend() {
    if (!answer.trim() || loading || isFinal) return;
    const updated: AiInterviewMessage[] = [...messages, { role: 'candidate', content: answer.trim() }];
    setMessages(updated);
    setAnswer('');
    await fetchNextTurn(updated);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      void onSend();
    }
  }

  return (
    <div className="page-stack">
      <section className="card">
        <div className="card-header">
          <div>
            <div className="eyebrow">AI Interview（テスト版）</div>
            <h1>AI面接（テキスト）</h1>
          </div>
          <span className="pill">
            {isFinal
              ? '面接終了'
              : questionNumber > 0
                ? `質問 ${questionNumber} / ${MAX_QUESTIONS}`
                : '準備中...'}
          </span>
        </div>

        <div className="chat-thread">
          {messages.map((m, i) => (
            <div key={i} className={`chat-bubble ${m.role}`}>
              <div className="chat-bubble-label">{m.role === 'interviewer' ? '面接官（AI）' : 'あなた'}</div>
              <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{m.content}</p>
            </div>
          ))}

          {loading && !isFinal && (
            <div className="chat-bubble interviewer">
              <div className="chat-bubble-label">面接官（AI）</div>
              <p style={{ margin: 0 }}>入力中...</p>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {error && <p className="error-text">{error}</p>}

        {!isFinal && (
          <div className="form-grid" style={{ marginTop: 16 }}>
            <label>
              回答
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                onKeyDown={onKeyDown}
                rows={4}
                placeholder="回答を入力してください（Ctrl+Enterで送信）"
                disabled={loading || questionNumber === 0}
              />
            </label>
            <div className="button-row">
              <button
                className="button primary"
                type="button"
                onClick={() => void onSend()}
                disabled={loading || !answer.trim() || questionNumber === 0}
              >
                {loading ? '送信中...' : '回答を送信する'}
              </button>
            </div>
          </div>
        )}
      </section>

      {isFinal && (
        <section className="card">
          <div className="card-header">
            <div>
              <div className="eyebrow">Feedback</div>
              <h1>総合フィードバック</h1>
            </div>
          </div>
          <div className="summary-box">
            <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{feedback}</p>
          </div>
        </section>
      )}
    </div>
  );
}