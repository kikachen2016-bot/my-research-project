'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getApiBase } from '@/lib/api-base';

type TurnDraft = {
  phase: string;
  question: string;
  answer: string;
};

const PHASES = [
  { value: 'self_intro', label: '自己紹介' },
  { value: 'technical_qa', label: '技術質疑' },
  { value: 'condition_check', label: '条件確認' },
  { value: 'reverse_question', label: '逆質問' },
  { value: 'other', label: 'その他' },
];

const PRESET_QUESTIONS: Record<string, string[]> = {
  self_intro: [
    '自己紹介をお願いします。',
    '簡単にこれまでの経歴を教えてください。',
    '現職での役割と主な業務内容を教えてください。',
  ],
  technical_qa: [
    'これまでの開発経験を教えてください。',
    '得意な技術スタックと、その経験年数を教えてください。',
    '直近のプロジェクトで担当した内容と成果を教えてください。',
    'チーム開発での役割（リーダー経験など）を教えてください。',
    '今後伸ばしていきたいスキルはありますか？',
  ],
  condition_check: [
    '希望年収を教えてください。',
    '入社可能時期はいつ頃ですか？',
    'リモートワークや出社頻度について希望はありますか？',
    '転職理由を教えてください。',
  ],
  reverse_question: [
    '弊社についてご質問はありますか？',
    '入社後のキャリアパスについて聞きたいことはありますか？',
    'チームの雰囲気や文化について質問はありますか？',
  ],
  other: [
    'その他、確認しておきたいことはありますか？',
    '強みと弱みを教えてください。',
    '5年後のキャリアビジョンを教えてください。',
  ],
};

function getDefaultQuestion(phase: string): string {
  return PRESET_QUESTIONS[phase]?.[0] ?? '';
}

const DEFAULT_TURNS: TurnDraft[] = [
  { phase: 'self_intro', question: getDefaultQuestion('self_intro'), answer: '' },
  { phase: 'technical_qa', question: getDefaultQuestion('technical_qa'), answer: '' },
];

export default function NewSessionPage() {
  const router = useRouter();
  const apiUrl = useMemo(() => getApiBase(), []);
  const [candidateName, setCandidateName] = useState('');
  const [turns, setTurns] = useState<TurnDraft[]>(DEFAULT_TURNS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function addTurn() {
    const phase = 'technical_qa';
    setTurns((prev) => [...prev, { phase, question: getDefaultQuestion(phase), answer: '' }]);
  }

  function changePhase(index: number, newPhase: string) {
    setTurns((prev) =>
      prev.map((t, i) =>
        i === index ? { ...t, phase: newPhase, question: getDefaultQuestion(newPhase) } : t
      )
    );
  }

  function rotateQuestion(index: number) {
    const phase = turns[index].phase;
    const presets = PRESET_QUESTIONS[phase] ?? [];
    if (presets.length <= 1) return;
    const current = turns[index].question;
    const currentIdx = presets.indexOf(current);
    const nextIdx = (currentIdx + 1) % presets.length;
    updateTurn(index, 'question', presets[nextIdx]);
  }

  function removeTurn(index: number) {
    setTurns((prev) => prev.filter((_, i) => i !== index));
  }

  function updateTurn(index: number, field: keyof TurnDraft, value: string) {
    setTurns((prev) =>
      prev.map((t, i) => (i === index ? { ...t, [field]: value } : t))
    );
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch(`${apiUrl}/sessions/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_name: candidateName, turns }),
      });

      if (!res.ok) {
        const text = await res.text().catch(() => '');
        throw new Error(text || '診断に失敗しました');
      }

      const data = await res.json();
      router.push(`/session/${data.id}`);
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
            <div className="eyebrow">Full Interview</div>
            <h1>面談全体診断</h1>
          </div>
          <span className="pill">複数ターン対応</span>
        </div>

        <form onSubmit={onSubmit} className="form-grid">
          <label>
            候補者名
            <input
              value={candidateName}
              onChange={(e) => setCandidateName(e.target.value)}
              placeholder="例：Chen"
              required
            />
          </label>

          <div className="turns-header">
            <h2>面談ターン</h2>
            <span className="meta-label">{turns.length} ターン</span>
          </div>

          {turns.map((turn, i) => (
            <div key={i} className="turn-card">
              <div className="turn-card-header">
                <span className="turn-number">ターン {i + 1}</span>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <select
                    value={turn.phase}
                    onChange={(e) => changePhase(i, e.target.value)}
                    className="phase-select"
                  >
                    {PHASES.map((p) => (
                      <option key={p.value} value={p.value}>
                        {p.label}
                      </option>
                    ))}
                  </select>
                  {turns.length > 1 && (
                    <button
                      type="button"
                      className="button secondary remove-btn"
                      onClick={() => removeTurn(i)}
                    >
                      削除
                    </button>
                  )}
                </div>
              </div>

              <label>
                質問
                <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                  <textarea
                    value={turn.question}
                    onChange={(e) => updateTurn(i, 'question', e.target.value)}
                    rows={2}
                    placeholder="面接官の質問を入力してください"
                    required
                    style={{ flex: 1 }}
                  />
                  {(PRESET_QUESTIONS[turn.phase]?.length ?? 0) > 1 && (
                    <button
                      type="button"
                      className="button secondary"
                      onClick={() => rotateQuestion(i)}
                      style={{ whiteSpace: 'nowrap', marginTop: 2 }}
                    >
                      別の質問
                    </button>
                  )}
                </div>
              </label>

              <label>
                回答
                <textarea
                  value={turn.answer}
                  onChange={(e) => updateTurn(i, 'answer', e.target.value)}
                  rows={4}
                  placeholder="候補者の回答を入力してください"
                  required
                />
              </label>
            </div>
          ))}

          <button type="button" className="button secondary add-turn-btn" onClick={addTurn}>
            ＋ ターンを追加
          </button>

          {error && <p className="error-text">{error}</p>}

          <div className="button-row">
            <button className="button primary" type="submit" disabled={loading}>
              {loading ? '診断中...' : '面談全体を診断する'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
