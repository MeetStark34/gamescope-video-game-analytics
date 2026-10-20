import type { ReactNode } from "react";

export function ChartPanel({ title, subtitle, children, className = "" }: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel chart-panel ${className}`}>
      <div className="panel-heading"><div><h2>{title}</h2>{subtitle ? <p>{subtitle}</p> : null}</div></div>
      <div className="chart-wrap">{children}</div>
    </section>
  );
}
