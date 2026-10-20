"use client";

import { useMemo } from "react";
import { Database, Gamepad2, Globe2, Trophy } from "lucide-react";
import { ChartPanel } from "@/components/cards/chart-panel";
import { KpiCard } from "@/components/cards/kpi-card";
import { WhyThisMatters } from "@/components/cards/why-this-matters";
import { TrendChart, RankedBarChart } from "@/components/charts/analytics-charts";
import { InsightList } from "@/components/insights/insight-list";
import { PageHeader } from "@/components/layout/page-header";
import { PageDataState } from "@/components/layout/load-state";
import { DataTable, type TableColumn } from "@/components/tables/data-table";
import { formatNumber } from "@/lib/analytics-data";
import { aggregateAnnual, topGameRecords } from "@/lib/dashboard-data";
import { useDashboard } from "@/lib/dashboard-context";
import { useAnalytics } from "@/lib/use-analytics";
import type { TopGame } from "@/lib/types";

const gameColumns: TableColumn<TopGame>[] = [
  { key: "sales_rank", label: "Rank", align: "right" }, { key: "name", label: "Game" },
  { key: "platform", label: "Platform" }, { key: "genre", label: "Genre" },
  { key: "year", label: "Year", align: "right" },
  { key: "global_sales", label: "Selected-region sales", align: "right", format: (value) => formatNumber(value as number, 2) },
];

export function OverviewSection() {
  const dashboard = useDashboard();
  const manifest = useAnalytics("dashboard_manifest");
  const stats = useAnalytics("descriptive_statistics");
  const insights = useAnalytics("insights");
  const trends = useMemo(() => aggregateAnnual(dashboard.records, dashboard.filters.region), [dashboard.records, dashboard.filters.region]);
  const games = useMemo(() => topGameRecords(dashboard.records, dashboard.filters.region), [dashboard.records, dashboard.filters.region]);
  const genreCount = new Set(dashboard.records.map((row) => row.Genre).filter(Boolean)).size;
  return <>
    <PageHeader eyebrow="Global video game sales intelligence" title="The market, at a glance" description="A source-aware view of sales, release activity, and the publishers and genres shaping the games business." />
    <PageDataState states={[dashboard.status, manifest, stats, insights]}>
      {manifest.status === "success" && stats.status === "success" && insights.status === "success" ? dashboard.records.length ? <>
        <div className="kpi-grid">
          <KpiCard label="Filtered game records" value={formatNumber(dashboard.summary.recordCount, 0)} note="Cleaned primary rows in this view" icon={<Database size={17} />} />
          <KpiCard label="Genres in view" value={formatNumber(genreCount, 0)} note="Distinct cleaned genre labels" icon={<Gamepad2 size={17} />} accent="orange" />
          <KpiCard label={`${dashboard.filters.region} sales`} value={formatNumber(dashboard.summary.salesTotal, 2)} note={`${formatNumber(dashboard.summary.gamesWithSales, 0)} records with reported sales`} icon={<Globe2 size={17} />} accent="green" />
          <KpiCard label="Top scoped seller" value={games[0]?.name ?? "—"} note={`${formatNumber(games[0]?.global_sales, 2)} reported sales in selected region`} icon={<Trophy size={17} />} accent="violet" />
        </div>
        <div className="content-grid content-grid-wide">
          <ChartPanel title="Sales & release momentum" subtitle={`Annual ${dashboard.filters.region.toLowerCase()} sales and release records. Select a year to narrow this view.`}>
            <TrendChart data={trends} salesLabel={`${dashboard.filters.region} sales`} onSelectYear={(year) => { dashboard.setYear("yearFrom", year); dashboard.setYear("yearTo", year); }} />
          </ChartPanel>
          <section className="panel panel-note"><div className="note-icon"><Globe2 size={19} /></div><p className="eyebrow">Dataset scope</p><h2>One primary source, clearly labeled</h2><p>The required assignment analyses use vgsales.csv. The separate vgchartz dataset appears only in Advanced Analysis, with its own coverage and definitions.</p><span className="updated-label">Analytics refreshed {new Date(manifest.data.generated_at).toLocaleString()}</span></section>
        </div>
        <WhyThisMatters>Viewing releases and sales together helps distinguish catalogue volume from sales volume. This chart uses the current filters; the Python insight cards below remain full-source reference metrics.</WhyThisMatters>
        <section className="section-block"><div className="section-heading"><div><p className="eyebrow">Full-source reference</p><h2>Python-computed insights</h2></div></div><InsightList insights={insights.data} /></section>
        <div className="content-grid content-grid-wide">
          <ChartPanel title="Highest-selling game records" subtitle={`Top rows by ${dashboard.filters.region} sales. Select a bar to search its title.`}>
            <RankedBarChart data={games.slice(0, 8).map((item) => ({ label: `${item.name ?? "Unknown"} · ${item.platform ?? "—"}`, sales: item.global_sales }))} categoryKey="label" valueKey="sales" height={310} categoryLabel="Game" valueLabel="Sales" onSelect={(label) => { const selected = games.find((item) => `${item.name ?? "Unknown"} · ${item.platform ?? "—"}` === label); if (selected?.name) dashboard.setFilter("search", selected.name); }} />
          </ChartPanel>
          <DataTable rows={games} columns={gameColumns} title="Top scoped games" description="Sorted from cleaned rows after applying the current filters." pageSize={10} expandable />
        </div>
        <WhyThisMatters>A top ranking identifies the largest recorded sales totals in this view. It does not describe the typical game or explain why a title sold well.</WhyThisMatters>
        <p className="data-footnote">Sales use the source-reported units. Year charts omit rows without a valid year; {formatNumber(stats.data.Year?.missing_or_invalid ?? 0, 0)} full-source primary records have a missing or invalid year.</p>
      </> : <div className="state-card">No cleaned game records match the current filters. Adjust or reset the filters above.</div> : null}
    </PageDataState>
  </>;
}
