import { getSession } from '@/lib/api';
import { PhaseScoreResult, TurnResult } from '@/lib/types';

const PHASE_LABELS: Record<string, string> = {
  self_intro: '自己紹介',
  technical_qa: '技術質疑',
  condition_check: '条件確認',
  reverse_question: '逆質問',
  other: 'その他',
};

const PHASE_ORDER = ['self_intro', 'technical_qa', 'condition_check', 'reverse_question', 'other'];

function DecisionBadge({ decision }: { decision: string }) {
  const classMap: Record<string, string> = {
    '合格可能性：高': 'decision-badge pass',
    '合格可能性：中': 'decision-badge mid',
    '合格可能性：低': 'decision-badge warn',
    '合格不可': 'decision-badge fail',
  };
  return (
    <span className={classMap[decision] ?? 'decision-badge mid'}>{decision}</span>
  );
}

function ScoreBar({ score }: { score: number }) {
  const pct = ((score - 1) / 4) * 100;
  const color = score >= 3.5 ? '#22c55e' : score >= 2.5 ? '#f59e0b' : '#ef4444';
  return (
    <div className="score-bar-wrap">
      <div className="score-bar-track">
        <div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="score-bar-label">{score.toFixed(1)}</span>
    </div>
  );
}

function PhaseCard({ ps }: { ps: PhaseScoreResult }) {
  return (
    <div className="phase-score-card">
      <div className="phase-label">{PHASE_LABELS[ps.phase] ?? ps.phase}</div>
      <ScoreBar score={ps.score} />
      {ps.feedback && <p className="phase-feedback">{ps.feedback}</p>}
    </div>
  );
}

function TurnCard({ turn }: { turn: TurnResult }) {
  return (
    <div className="turn-result-card">
      <div className="turn-result-header">
        <span className="turn-number">ターン {turn.turn_index + 1}</span>
        <span className="pill">{PHASE_LABELS[turn.phase] ?? turn.phase}</span>
        <span className="phase-score-pill">フェーズスコア {turn.phase_score.toFixed(1)}</span>
      </div>

      <div className="turn-qa">
        <div className="meta-label">質問</div>
        <p>{turn.question}</p>
        <div className="meta-label" style={{ marginTop: 8 }}>回答</div>
        <pre className="answer-box">{turn.answer}</pre>
      </div>

      <div className="turn-scores">
        <div className="score-item">
          <span className="meta-label">日本語明瞭さ</span>
          <span className="score-value">{turn.jp_clarity.toFixed(1)}</span>
        </div>
        <div className="score-item">
          <span className="meta-label">論理性</span>
          <span className="score-value">{turn.logical.toFixed(1)}</span>
        </div>
        <div className="score-item">
          <span className="meta-label">技術の深さ</span>
          <span className="score-value">{turn.technical.toFixed(1)}</span>
        </div>
      </div>

      {turn.feedback && (
        <div className="summary-box" style={{ marginTop: 12 }}>
          <p>{turn.feedback}</p>
        </div>
      )}
    </div>
  );
}

export default async function SessionResultPage({ params }: { params: { id: string } }) {
  const detail = await getSession(params.id);

  const sortedPhaseScores = [...detail.phase_scores].sort(
    (a, b) => PHASE_ORDER.indexOf(a.phase) - PHASE_ORDER.indexOf(b.phase)
  );

  return (
    <div className="page-stack">
      {/* ヘッダー */}
      <section className="card">
        <div className="card-header">
          <div>
            <div className="eyebrow">面談全体診断結果</div>
            <h1>{detail.candidate_name} さんの面談結果</h1>
          </div>
          <DecisionBadge decision={detail.pass_decision} />
        </div>

        <div className="meta-grid">
          <div>
            <div className="meta-label">総合スコア</div>
            <div className="stat-value">
              {detail.overall_score.toFixed(1)}
              <span style={{ fontSize: 18, fontWeight: 400 }}> / 5.0</span>
            </div>
          </div>
          <div>
            <div className="meta-label">日時</div>
            <p>{new Date(detail.created_at).toLocaleString('ja-JP')}</p>
          </div>
        </div>

        {detail.summary_comment && (
          <div className="summary-box">
            <h2>総評</h2>
            <p>{detail.summary_comment}</p>
          </div>
        )}
      </section>

      {/* 致命傷アラート */}
      {detail.fatal_flaw_triggered && (
        <section className="card fatal-flaw-alert">
          <h2>致命傷が検出されました</h2>
          <p>{detail.fatal_flaw_reason}</p>
        </section>
      )}

      {/* フェーズ別スコア */}
      <section className="card">
        <div className="card-header">
          <h2>フェーズ別スコア</h2>
        </div>
        <div className="phase-score-grid">
          {sortedPhaseScores.map((ps) => (
            <PhaseCard key={ps.phase} ps={ps} />
          ))}
        </div>
      </section>

      {/* ターン詳細 */}
      <section className="card">
        <div className="card-header">
          <h2>ターン詳細</h2>
          <span className="meta-label">{detail.turns.length} ターン</span>
        </div>
        <div className="page-stack">
          {detail.turns.map((turn) => (
            <TurnCard key={turn.turn_index} turn={turn} />
          ))}
        </div>
      </section>
    </div>
  );
}
