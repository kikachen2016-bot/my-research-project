import Link from 'next/link';
import { checkHealth } from '@/lib/api';

export default async function HomePage() {
  const health = await checkHealth().catch(() => ({ status: 'down' }));

  return (
    <div className="page-stack">
      <section className="hero card">
        <div>
          <div className="eyebrow">AI面接システム</div>
          <h1>AI音声面接</h1>
          <p>
            案件概要と履歴書をアップロードするだけで、AIがPM・テックリード・人事の視点から
            カスタム質問を生成。音声でリアルな面接練習ができます。
          </p>
        </div>
        <div className="hero-actions">
          <Link className="button primary" href="/ai-interview-voice">面接を始める</Link>
        </div>
      </section>

      <section className="stats-grid">
        <article className="card stat-card">
          <div className="meta-label">API 状態</div>
          <div className="stat-value">{health.status === 'ok' ? '正常' : '未接続'}</div>
        </article>
        <article className="card stat-card">
          <div className="meta-label">対応ファイル形式</div>
          <div className="stat-value small">TXT / PDF / Excel</div>
        </article>
        <article className="card stat-card">
          <div className="meta-label">フィードバック</div>
          <div className="stat-value small">BARS評価 + コーチングアドバイス</div>
        </article>
      </section>

      <section className="card">
        <div className="card-header">
          <h2>使い方</h2>
        </div>
        <ol style={{ margin: 0, paddingLeft: 20, lineHeight: 2 }}>
          <li>案件概要ファイル（TXT / PDF / Excel）をアップロード</li>
          <li>履歴書・職務経歴書をアップロード</li>
          <li>「面接を開始する」を押す</li>
          <li>AIの質問を聞いたら ▶ を押して回答開始、終わったら ■ を押して送信</li>
          <li>全5問が終わると BARS評価と面接コーチングアドバイスが表示されます</li>
        </ol>
      </section>
    </div>
  );
}
