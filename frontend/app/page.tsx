import Link from 'next/link';
import { checkHealth, getSessions } from '@/lib/api';

export default async function HomePage() {
  const [sessions, health] = await Promise.all([
    getSessions().catch(() => []),
    checkHealth().catch(() => ({ status: 'down' })),
  ]);

  return (
    <div className="page-stack">
      <section className="hero card">
        <div>
          <div className="eyebrow">面談評価システム</div>
          <h1>外国人ITエンジニア面談力診断システム</h1>
          <p>
            面談全体をフェーズ別に評価し、合否判定と改善フィードバックを提供します。
          </p>
        </div>
        <div className="hero-actions">
          <Link className="button primary" href="/session/new">面談全体を診断する</Link>
          <Link className="button secondary" href="/criteria">評価基準を見る</Link>
        </div>
      </section>

      <section className="stats-grid">
        <article className="card stat-card">
          <div className="meta-label">API 状態</div>
          <div className="stat-value">{health.status === 'ok' ? '正常' : '未接続'}</div>
        </article>
        <article className="card stat-card">
          <div className="meta-label">面談診断件数</div>
          <div className="stat-value">{sessions.length}</div>
        </article>
        <article className="card stat-card">
          <div className="meta-label">対応フェーズ</div>
          <div className="stat-value small">自己紹介 / 技術質疑 / 条件確認 / 逆質問</div>
        </article>
      </section>

      <section className="card">
        <div className="card-header">
          <h2>過去の面談診断</h2>
          <Link href="/history">すべて見る</Link>
        </div>

        {sessions.length === 0 ? (
          <p className="empty">まだ診断データがありません。最初の1件を作成してください。</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>候補者</th>
                  <th>総合スコア</th>
                  <th>合否判定</th>
                  <th>日時</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {sessions.slice(0, 5).map((item) => (
                  <tr key={item.id}>
                    <td>{item.candidate_name}</td>
                    <td>{item.overall_score.toFixed(1)} / 5.0</td>
                    <td>{item.pass_decision}</td>
                    <td>{new Date(item.created_at).toLocaleString('ja-JP')}</td>
                    <td><Link href={`/session/${item.id}`}>詳細</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
