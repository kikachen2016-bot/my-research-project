'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getApiBase } from '@/lib/api-base';
import AudioRecorder from '@/components/AudioRecorder';

const DEFAULT_QUESTION = 'これまでの開発経験を教えてください。';
const DEFAULT_TRANSCRIPT = 'JavaとSpring Bootを使った社内業務システム開発を担当しました。要件整理から実装、テストまで関わり、レスポンス改善ではSQL見直しで処理時間を約40%短縮しました。';

export default function NewInterviewPage() {
  const router = useRouter();
  const apiUrl = useMemo(() => getApiBase(), []);
  const [candidateName, setCandidateName] = useState('');
  const [question, setQuestion] = useState(DEFAULT_QUESTION);
  const [transcript, setTranscript] = useState(DEFAULT_TRANSCRIPT);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioTranscript, setAudioTranscript] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [inputType, setInputType] = useState<'text' | 'audio'>('text');

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      let res;
      if (inputType === 'text') {
        res = await fetch(`${apiUrl}/interviews/evaluate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ candidate_name: candidateName, question, transcript }),
        });
      } else {
        // 音声→文字起こし済みテキストを使って通常の評価エンドポイントに送信
        if (!audioTranscript) throw new Error('音声が録音されていないか、文字起こしに失敗しました');

        res = await fetch(`${apiUrl}/interviews/evaluate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_name: candidateName,
            question,
            transcript: audioTranscript,
          }),
        });
      }

      if (!res.ok) {
        const text = await res.text().catch(() => '');
        throw new Error(text || '診断に失敗しました');
      }

      const data = await res.json();
      router.push(`/interview/${data.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : '診断に失敗しました');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-stack">
      <section className="card">
        <div className="card-header">
          <div>
            <div className="eyebrow">New Evaluation</div>
            <h1>新規面談診断</h1>
          </div>
          <span className="pill">{inputType === 'text' ? 'テキスト入力' : '音声入力/Whisper'}</span>
        </div>

        <div className="tabs" style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', borderBottom: '1px solid #e5e7eb' }}>
          <button 
            className={`tab ${inputType === 'text' ? 'active' : ''}`}
            onClick={() => setInputType('text')}
            style={{ 
              padding: '0.5rem 1rem', 
              border: 'none', 
              background: 'none', 
              cursor: 'pointer',
              borderBottom: inputType === 'text' ? '2px solid var(--primary-color, #2563eb)' : 'none',
              fontWeight: inputType === 'text' ? 'bold' : 'normal'
            }}
          >
            テキスト入力
          </button>
          <button 
            className={`tab ${inputType === 'audio' ? 'active' : ''}`}
            onClick={() => setInputType('audio')}
            style={{ 
              padding: '0.5rem 1rem', 
              border: 'none', 
              background: 'none', 
              cursor: 'pointer',
              borderBottom: inputType === 'audio' ? '2px solid var(--primary-color, #2563eb)' : 'none',
              fontWeight: inputType === 'audio' ? 'bold' : 'normal'
            }}
          >
            音声録音で診断
          </button>
        </div>

        <form onSubmit={onSubmit} className="form-grid">
          <label>
            候補者名
            <input value={candidateName} onChange={(e) => setCandidateName(e.target.value)} placeholder="例：Chen" required />
          </label>

          <label>
            面談質問
            <textarea value={question} onChange={(e) => setQuestion(e.target.value)} rows={3} required />
          </label>

          {inputType === 'text' ? (
            <label>
              文字起こし結果 / 回答テキスト
              <textarea value={transcript} onChange={(e) => setTranscript(e.target.value)} rows={10} required />
            </label>
          ) : (
            <div className="audio-section" style={{ margin: '1rem 0' }}>
              <p style={{ marginBottom: '0.5rem', fontWeight: 'bold' }}>回答を録音（ブラウザ文字起こし）</p>
              <AudioRecorder onRecordingComplete={(blob, transcript) => {
                setAudioBlob(blob);
                setAudioTranscript(transcript);
              }} />
              <p className="text-sm color-muted" style={{ marginTop: '0.5rem' }}>
                ※録音終了後に文字起こしを確認し、「BARS診断を実行」を押してください。
              </p>
            </div>
          )}

          <div className="helper-box">
            <strong>送信先:</strong> {apiUrl}/interviews/evaluate
          </div>

          {error ? <p className="error-text">{error}</p> : null}

          <div className="button-row">
            <button className="button primary" type="submit" disabled={loading || (inputType === 'audio' && !audioTranscript)}>
              {loading ? '解析・診断中...' : 'BARS診断を実行'}
            </button>
            <button className="button secondary" type="button" onClick={() => {
              setCandidateName('Test Engineer');
              setQuestion(DEFAULT_QUESTION);
              setTranscript(DEFAULT_TRANSCRIPT);
            }}>
              サンプルを再入力
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
