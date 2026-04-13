import { BarsCriterion } from '@/lib/types';

type Props = {
  criterion: BarsCriterion;
  currentLevel: number;
};

export default function BarsStageCard({ criterion, currentLevel }: Props) {
  const currentIndex = criterion.levels.findIndex((item) => item.level === currentLevel);
  const current = criterion.levels[currentIndex] || criterion.levels[0];
  const prev = criterion.levels[Math.max(0, currentIndex - 1)];
  const next = criterion.levels[Math.min(criterion.levels.length - 1, currentIndex + 1)];

  return (
    <section className="card stage-card">
      <div className="card-header">
        <h3>{criterion.label}</h3>
        <span className="pill">Level {currentLevel}</span>
      </div>

      <div className="stage-grid">
        <div className="stage-box substage">
          <div className="stage-title">前のステージ</div>
          <div className="stage-level">Level {prev.level}</div>
          <p>{prev.description}</p>
        </div>

        <div className="stage-box current-stage">
          <div className="stage-title">現在のステージ</div>
          <div className="stage-level">Level {current.level}</div>
          <p>{current.description}</p>
        </div>

        <div className="stage-box substage">
          <div className="stage-title">次のステージ</div>
          <div className="stage-level">Level {next.level}</div>
          <p>{next.description}</p>
        </div>
      </div>
    </section>
  );
}
