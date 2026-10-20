"use client";

import { useMemo } from "react";
import { ChartPanel } from "@/components/cards/chart-panel";
import { WhyThisMatters } from "@/components/cards/why-this-matters";
import { RankedBarChart } from "@/components/charts/analytics-charts";
import { PageHeader } from "@/components/layout/page-header";
import { PageDataState } from "@/components/layout/load-state";
import { DataTable, type TableColumn } from "@/components/tables/data-table";
import { rowSales, useDashboard } from "@/lib/dashboard-context";
import { formatNumber, formatPercent } from "@/lib/analytics-data";
import { useAnalytics } from "@/lib/use-analytics";
import type { MarketPower } from "@/lib/types";

const columns: TableColumn<MarketPower>[] = [
  { key: "market_power_rank", label: "Rank", align: "right" }, { key: "publisher", label: "Publisher" },
  { key: "publisher_archetype", label: "Archetype" }, { key: "market_power_index", label: "MPI", align: "right", format: (value) => formatNumber(value as number | null, 2) },
  { key: "sales_share", label: "Sales share", align: "right", format: (value) => formatPercent(value as number | null) },
  { key: "genre_leader_count", label: "Genre leaders", align: "right" },
  { key: "genre_diversity_score", label: "Genre diversity", align: "right", format: (value) => formatPercent(value as number | null) },
  { key: "regional_consistency_score", label: "Regional consistency", align: "right", format: (value) => formatPercent(value as number | null) },
  { key: "hit_rate", label: "Hit rate", align: "right", format: (value) => formatPercent(value as number | null) },
  { key: "available_component_count", label: "Components", align: "right" },
];

export function MarketPowerSection() {
  const dashboard = useDashboard();
  const index = useAnalytics("market_power_index");
  const publisherSet = useMemo(() => new Set(dashboard.records.filter((row) => rowSales(row, dashboard.filters.region) != null).map((row) => row.Publisher).filter((publisher): publisher is string => Boolean(publisher))), [dashboard.records, dashboard.filters.region]);
  const rows = useMemo(() => index.status === "success" ? index.data.filter((row) => publisherSet.has(row.publisher)) : [], [index, publisherSet]);
  return <>
    <PageHeader eyebrow="Python-derived · full-source metric" title="Market Power Index" description="Explore the precomputed publisher ranking while global filters select the publishers represented in the current catalogue view." />
    <PageDataState states={[dashboard.status, index]}>{index.status === "success" ? rows.length ? <>
      <div className="callout"><span className="callout-mark">i</span><p>The composite score and its components remain calculated on the full cleaned primary dataset. Global filters narrow the publisher cohort, but do not recalculate publisher scores or ranks.</p></div>
      <ChartPanel title="Publisher ranking" subtitle="Click a bar to focus other views on that publisher. Scores are unchanged by filters."><RankedBarChart data={rows.filter((row) => row.market_power_index != null).slice(0, 15).map((row) => ({ publisher: row.publisher, score: row.market_power_index }))} categoryKey="publisher" valueKey="score" color="var(--chart-4)" height={410} categoryLabel="Publisher" valueLabel="Market Power Index" selectedValue={dashboard.filters.publisher === "all" ? undefined : dashboard.filters.publisher} onSelect={(publisher) => dashboard.setFilter("publisher", dashboard.filters.publisher === publisher ? "all" : publisher)} /></ChartPanel>
      <WhyThisMatters>The components separate publisher scale, genre breadth, hit rate, and regional consistency. Reading them together helps explain a composite rank and makes its limitations visible.</WhyThisMatters>
      <DataTable rows={rows} columns={columns} title="Publisher scores and components" description="Full-source Python scores for publishers represented in the filtered record set. Expand a row to inspect all components and leader genres." pageSize={15} expandable />
      <p className="data-footnote">Archetypes are rule-based portfolio descriptions, not inferred classes or legal conclusions. Formula and denominators: reports/advanced-analysis.md.</p>
    </> : <div className="state-card">No publishers from the selected record scope have a Market Power Index row.</div> : null}</PageDataState>
  </>;
}
