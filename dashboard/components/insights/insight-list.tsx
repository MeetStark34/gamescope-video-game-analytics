import type { Insight } from "@/lib/types";

export function InsightList({ insights }: { insights: Insight[] }) {
  if (!insights.length) return <div className="state-card">No insight cards are available for this dataset.</div>;
  return (
    <div className="insight-grid">
      {insights.map((item, index) => (
        <article className={`insight-card insight-${index % 3}`} key={item.id}>
          <div className="insight-kicker">Python-computed insight</div>
          <h3>{item.title}</h3>
          <p>{item.text}</p>
          <div className="insight-meta"><span>{item.source}</span><span>Coverage: {item.coverage.toLocaleString()}</span></div>
        </article>
      ))}
    </div>
  );
}
