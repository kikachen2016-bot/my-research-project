import { getCriteria } from '@/lib/api';

export default async function CriteriaPage() {
  const criteria = await getCriteria();

  return (
    <div className="page-stack">
      <section className="card">
        <div className="card-header">
          <div>
            <div className="eyebrow">BARS</div>
            <h1>評価基準一覧</h1>
          </div>
        </div>
        <p>現在のシステムで使用しているBARS評価基準です。</p>
      </section>

      {criteria.map((criterion) => (
        <section key={criterion.key} className="card">
          <div className="card-header">
            <h2>{criterion.label}</h2>
            <span className="pill">5段階</span>
          </div>
          <div className="criteria-grid">
            {criterion.levels.map((level) => (
              <div key={level.level} className="stage-box">
                <div className="stage-level">Level {level.level}</div>
                <p>{level.description}</p>
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
