import { getPreparation } from '@/lib/api';
import { ExpectedQuestion, ReverseQuestion } from '@/lib/types';

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="card">
      <div className="card-header">
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function IntroBlock({ label, text }: { label: string; text: string }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div className="meta-label" style={{ marginBottom: 6 }}>{label}</div>
      <div className="summary-box">
        <p style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{text}</p>
      </div>
    </div>
  );
}

function BulletList({ items }: { items: string[] }) {
  if (items.length === 0) return <p className="empty">なし</p>;
  return (
    <ul style={{ paddingLeft: 20, margin: 0 }}>
      {items.map((item, i) => (
        <li key={i} style={{ marginBottom: 6 }}>{item}</li>
      ))}
    </ul>
  );
}

function QuestionCard({ q, index }: { q: ExpectedQuestion; index: number }) {
  return (
    <div className="turn-result-card">
      <div className="turn-result-header">
        <span className="turn-number">Q{index + 1}</span>
      </div>

      <p style={{ fontWeight: 600, marginBottom: 12 }}>{q.question}</p>

      <div style={{ marginBottom: 10 }}>
        <div className="meta-label">出題意図</div>
        <p style={{ margin: '4px 0 0' }}>{q.intent}</p>
      </div>

      <div style={{ marginBottom: 10 }}>
        <div className="meta-label">回答のポイント</div>
        <ul style={{ paddingLeft: 20, margin: '4px 0 0' }}>
          {q.answer_points.map((pt, i) => (
            <li key={i} style={{ marginBottom: 4 }}>{pt}</li>
          ))}
        </ul>
      </div>

      {q.caution && (
        <div className="summary-box" style={{ marginTop: 8 }}>
          <div className="meta-label" style={{ marginBottom: 4 }}>注意</div>
          <p style={{ margin: 0 }}>{q.caution}</p>
        </div>
      )}
    </div>
  );
}

function ReverseQuestionCard({ q }: { q: ReverseQuestion }) {
  return (
    <div className="turn-result-card">
      <p style={{ fontWeight: 600, marginBottom: 8 }}>{q.question}</p>
      <div className="meta-label">聞く目的</div>
      <p style={{ margin: '4px 0 0' }}>{q.purpose}</p>
    </div>
  );
}

export default async function PreparationResultPage({ params }: { params: { id: string } }) {
  const prep = await getPreparation(params.id);
  const r = prep.result_json;

  return (
    <div className="page-stack">
      <section className="card">
        <div className="card-header">
          <div>
            <div className="eyebrow">面談前準備シート</div>
            <h1>準備シート #{prep.id}</h1>
          </div>
        </div>
      </section>

      <SectionCard title="自己紹介">
        <IntroBlock label="1分版" text={r.one_minute_intro} />
        <IntroBlock label="3分版" text={r.three_minute_intro} />
      </SectionCard>

      <SectionCard title="マッチポイント">
        <BulletList items={r.matching_points} />
      </SectionCard>

      <SectionCard title="注意点">
        <BulletList items={r.risk_points} />
      </SectionCard>

      <SectionCard title="想定質問">
        {r.expected_questions.length === 0 ? (
          <p className="empty">質問なし</p>
        ) : (
          <div className="page-stack">
            {r.expected_questions.map((q, i) => (
              <QuestionCard key={i} q={q} index={i} />
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="逆質問">
        {r.reverse_questions.length === 0 ? (
          <p className="empty">逆質問なし</p>
        ) : (
          <div className="page-stack">
            {r.reverse_questions.map((q, i) => (
              <ReverseQuestionCard key={i} q={q} />
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="面談前アドバイス">
        <div className="summary-box">
          <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{r.preparation_advice}</p>
        </div>
      </SectionCard>
    </div>
  );
}
