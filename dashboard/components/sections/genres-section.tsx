"use client";

import { useMemo } from "react";
import { ChartPanel } from "@/components/cards/chart-panel";
import { WhyThisMatters } from "@/components/cards/why-this-matters";
import { RankedBarChart, AffinityHeatmap } from "@/components/charts/analytics-charts";
import { PageHeader } from "@/components/layout/page-header";
import { PageDataState } from "@/components/layout/load-state";
import { DataTable, type TableColumn } from "@/components/tables/data-table";
import { formatNumber, formatPercent } from "@/lib/analytics-data";
import { aggregateBy } from "@/lib/dashboard-data";
import { useDashboard } from "@/lib/dashboard-context";
import { useAnalytics } from "@/lib/use-analytics";

type GenreRow = { genre: string; game_count: number; games_with_sales: number; global_sales_total: number; global_sales_mean: number | null; global_sales_share: number | null };
const columns: TableColumn<GenreRow>[] = [
  { key: "genre", label: "Genre" }, { key: "game_count", label: "Game records", align: "right" },
  { key: "games_with_sales", label: "Records with sales", align: "right" },
  { key: "global_sales_total", label: "Selected-region sales", align: "right", format: (value) => formatNumber(value as number, 2) },
  { key: "global_sales_mean", label: "Mean sales", align: "right", format: (value) => formatNumber(value as number | null, 3) },
  { key: "global_sales_share", label: "View sales share", align: "right", format: (value) => formatPercent(value as number | null) },
];

export function GenresSection() {
  const dashboard = useDashboard();
  const affinity = useAnalytics("genre_region_affinity");
  const sales = useMemo(() => aggregateBy(dashboard.records, "Genre", dashboard.filters.region).map(({ label, ...row }) => ({ genre: label, ...row })), [dashboard.records, dashboard.filters.region]);
  const scopedAffinity = useMemo(() => affinity.status === "success" ? affinity.data.filter((row) => (dashboard.filters.genre === "all" || row.genre === dashboard.filters.genre) && (dashboard.filters.region === "Global" || row.region === dashboard.filters.region)) : [], [affinity, dashboard.filters.genre, dashboard.filters.region]);
  return <>
    <PageHeader eyebrow="Cleaned primary source · vgsales.csv" title="Genre analysis" description="Compare catalogue volume and selected-region sales within the current global filter scope." />
    <PageDataState states={[dashboard.status, affinity]}>{affinity.status === "success" && dashboard.records.length ? <>
      <div className="content-grid">
        <ChartPanel title="Records by genre" subtitle="Select a bar to cross-filter the dashboard by genre."><RankedBarChart data={sales.map((row) => ({ genre: row.genre, records: row.game_count }))} categoryKey="genre" valueKey="records" categoryLabel="Genre" valueLabel="Game records" selectedValue={dashboard.filters.genre === "all" ? undefined : dashboard.filters.genre} onSelect={(value) => dashboard.setFilter("genre", dashboard.filters.genre === value ? "all" : value)} /></ChartPanel>
        <ChartPanel title={`${dashboard.filters.region} sales by genre`} subtitle="Sales totals are refreshed from cleaned rows after global filters are applied."><RankedBarChart data={sales.map((row) => ({ genre: row.genre, sales: row.global_sales_total }))} categoryKey="genre" valueKey="sales" color="var(--chart-2)" categoryLabel="Genre" valueLabel="Sales" selectedValue={dashboard.filters.genre === "all" ? undefined : dashboard.filters.genre} onSelect={(value) => dashboard.setFilter("genre", dashboard.filters.genre === value ? "all" : value)} /></ChartPanel>
      </div>
      <WhyThisMatters>Catalogue share and sales share answer different questions. This filtered comparison can reveal when a genre’s record count and selected-region sales move differently.</WhyThisMatters>
      <ChartPanel title="Python-derived regional genre affinity" subtitle="These ratios are precomputed from the full source, then narrowed by selected genre or region. They are not recomputed for the current row filters."><AffinityHeatmap data={scopedAffinity} /></ChartPanel>
      <DataTable rows={sales} columns={columns} title="Filtered genre detail" description={`${formatNumber(dashboard.summary.recordCount, 0)} cleaned records match the current filters.`} />
    </> : dashboard.records.length === 0 ? <div className="state-card">No records match the current filters. Adjust or reset the filters above.</div> : null}</PageDataState>
  </>;
}
