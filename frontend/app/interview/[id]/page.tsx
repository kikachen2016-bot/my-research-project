import { getCriteria, getInterview } from '@/lib/api';

function normalizeCriterionLabel(label: string): string {
  return label.replace(/^[①②③④⑤⑥⑦⑧⑨⑩]\s*/, '');
}

export default async function InterviewResultPage({ params }: { params: { id: string } }) {
  const [detail, criteria] = await Promise.all([getInterview(params.id), getCriteria()]);

  const sortedFeedbacks = [...(detail.evaluation.criterion_feedbacks ?? [])].sort(
    (a, b) => a.score - b.score
  );

  const priorityFeedbacks = sortedFeedbacks.filter((item) => item.score <= 3);
  const goodFeedbacks = sortedFeedbacks.filter((item) => item.score >= 4);

  return (
    <div className="page-stack">
      <section className="card">
        <div className="card-header">
          <div>
            <div className="eyebrow">診断結果</div>
            <h1>{detail.candidate_name} さんの面談結果</h1>
          </div>
          <span className="level-badge">総合 Level {detail.overall_level}</span>
        </div>

        <div className="meta-grid">
          <div>
            <div className="meta-label">質問</div>
            <p>{detail.question}</p>
          </div>
          <div>
            <div className="meta-label">日時</div>
            <p>{new Date(detail.created_at).toLocaleString('ja-JP')}</p>
          </div>
        </div>

        <div className="summary-box">
          <h2>総評</h2>
          <p>{detail.summary_comment || detail.evaluation.summary_comment}</p>
          <ul>
            {detail.evaluation.advice.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <h2>この診断の見方</h2>
        </div>
        <div className="summary-box">
          <p>
            この診断では、各評価項目を <strong>Level1〜Level5</strong> の5段階で判定しています。
            Levelが高いほど、その項目がより安定してできている状態を表します。
          </p>
          <p>
            本画面では、<strong>Level4以上</strong> を「強みとして出ている項目」、
            <strong>Level3以下</strong> を「優先して改善したい項目」として整理しています。
          </p>
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <h2>強みとして出ている項目</h2>
        </div>

        <div className="page-stack">
          {goodFeedbacks.length > 0 ? (
            goodFeedbacks.map((item) => {
              const criterion = criteria.find((c) => c.key === item.key);
              const label = normalizeCriterionLabel(criterion?.label ?? item.key);

              return (
                <div key={item.key} className="stage-box">
                  <div className="card-header">
                    <h3>{label}</h3>
                    <span className="pill">Level {item.score}</span>
                  </div>

                  <div className="meta-label">現在の評価</div>
                  <p>{item.current_issue}</p>

                  <div className="meta-label">さらに伸ばすポイント</div>
                  <p>{item.feedback_comment}</p>

                  <div className="meta-label">次の一歩</div>
                  <p>{item.next_action}</p>

                  <div className="meta-label">より良い回答例</div>
                  <div className="summary-box">
                    <p>{item.improved_example}</p>
                  </div>
                </div>
              );
            })
          ) : (
            <p>該当する項目はありません。</p>
          )}
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <h2>優先して改善したい項目</h2>
        </div>

        <div className="page-stack">
          {priorityFeedbacks.length > 0 ? (
            priorityFeedbacks.map((item) => {
              const criterion = criteria.find((c) => c.key === item.key);
              const label = normalizeCriterionLabel(criterion?.label ?? item.key);

              return (
                <div key={item.key} className="stage-box">
                  <div className="card-header">
                    <h3>{label}</h3>
                    <span className="pill">Level {item.score}</span>
                  </div>

                  <div className="meta-label">できていないところ</div>
                  <p>{item.current_issue}</p>

                  <div className="meta-label">改善方法</div>
                  <p>{item.feedback_comment}</p>

                  <div className="meta-label">次回のアクション</div>
                  <p>{item.next_action}</p>

                  <div className="meta-label">改善後の回答例</div>
                  <div className="summary-box">
                    <p>{item.improved_example}</p>
                  </div>
                </div>
              );
            })
          ) : (
            <p>優先して改善が必要な項目はありません。</p>
          )}
        </div>
      </section>

      <section className="card">
        <h2>面談回答テキスト</h2>
        <pre className="transcript-box">{detail.transcript}</pre>
      </section>
    </div>
  );
}