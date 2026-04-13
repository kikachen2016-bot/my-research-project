import Link from 'next/link';
import { getInterviews } from '@/lib/api';

export default async function HistoryPage() {
  const interviews = await getInterviews().catch(() => []);

  return (
    <div className="page-stack">
      <section className="card">
        <div className="card-header">
          <div>
            <div className="eyebrow">History</div>
            <h1>診断履歴</h1>
          </div>
          <Link className="button primary" href="/interview/new">新規診断</Link>
        </div>

        {interviews.length === 0 ? (
          <p className="empty">まだ診断履歴がありません。</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>候補者</th>
                  <th>質問</th>
                  <th>総合Level</th>
                  <th>日時</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {interviews.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td>{item.candidate_name}</td>
                    <td className="truncate">{item.question}</td>
                    <td><span className="pill">Level {item.overall_level}</span></td>
                    <td>{new Date(item.created_at).toLocaleString('ja-JP')}</td>
                    <td><Link href={`/interview/${item.id}`}>詳細</Link></td>
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
