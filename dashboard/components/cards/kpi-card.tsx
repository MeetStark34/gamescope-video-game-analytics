import type { ReactNode } from "react";

export function KpiCard({ label, value, note, icon, accent = "blue" }: {
  label: string;
  value: string;
  note?: string;
  icon?: ReactNode;
  accent?: "blue" | "orange" | "green" | "violet";
}) {
  return (
    <article className={`kpi-card accent-${accent}`}>
      <div className="kpi-top"><span>{label}</span>{icon ? <span className="kpi-icon">{icon}</span> : null}</div>
      <strong className="kpi-value">{value}</strong>
      {note ? <p className="kpi-note">{note}</p> : null}
    </article>
  );
}
