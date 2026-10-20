"use client";

import { useMemo } from "react";
import { ChartPanel } from "@/components/cards/chart-panel";
import { KpiCard } from "@/components/cards/kpi-card";
import { WhyThisMatters } from "@/components/cards/why-this-matters";
import { AffinityHeatmap, RankedBarChart } from "@/components/charts/analytics-charts";
import { PageHeader } from "@/components/layout/page-header";
import { PageDataState } from "@/components/layout/load-state";
import { DataTable, type TableColumn } from "@/components/tables/data-table";
import { formatNumber } from "@/lib/analytics-data";
import { topConcentrated } from "@/lib/dashboard-data";
import { useDashboard } from "@/lib/dashboard-context";
import { useAnalytics } from "@/lib/use-analytics";
import type { DivergenceGame } from "@/lib/types";

const columns: TableColumn<DivergenceGame>[] = [
  { key: "name", label: "Game" }, { key: "platform", label: "Platform" }, { key: "year", label: "Year", align: "right" },
  { key: "genre", label: "Genre" }, { key: "dominant_region", label: "Largest region" },
  { key: "dominant_region_share", label: "Dominant share", align: "right", format: (value) => `${formatNumber((value as number) * 100, 1)}%` },
  { key: "regional_divergence_score", label: "Divergence", align: "right", format: (value) => formatNumber(value as number, 3) },
  { key: "cultural_specificity_score", label: "Specificity", align: "right", format: (value) => formatNumber(value as number, 1) },
  { key: "passes_cultural_outlier_screen", label: "Outlier screen" },
];

export function DivergenceSection() {
  const dashboard = useDashboard();
  const divergence = useAnalytics("regional_divergence_by_game");
  const outliers = useAnalytics("cultural_outliers");
  const affinity = useAnalytics("genre_region_affinity");
  const sourceRows = useMemo(() => new Set(dashboard.records.map((row) => String(row.source_row))), [dashboard.records]);
  const filtered = useMemo(() => divergence.status === "success" ? divergence.data.filter((row) => sourceRows.has(String(row.source_row)) && (dashboard.filters.region === "Global" || row.dominant_region === dashboard.filters.region)) : [], [divergence, sourceRows, dashboard.filters.region]);
  const filteredOutliers = useMemo(() => outliers.status === "success" ? outliers.data.filter((row) => sourceRows.has(String(row.source_row)) && (dashboard.filters.region === "Global" || row.dominant_region === dashboard.filters.region)) : [], [outliers, sourceRows, dashboard.filters.region]);
  const concentration = useMemo(() => topConcentrated(filtered, 12), [filtered]);
  const scopedAffinity = useMemo(() => affinity.status === "success" ? affinity.data.filter((row) => (dashboard.filters.genre === "all" || row.genre === dashboard.filters.genre) && (dashboard.filters.region === "Global" || row.region === dashboard.filters.region)) : [], [affinity, dashboard.filters.genre, dashboard.filters.region]);
  return <>
    <PageHeader eyebrow="Python-derived · primary source" title="Regional Preference Divergence" description="Inspect concentrated regional sales mixes and cultural outlier candidates within the current cleaned-record filter scope." />
    <PageDataState states={[dashboard.status, divergence, outliers, affinity]}>{divergence.status === "success" && outliers.status === "success" && affinity.status === "success" ? <>
      <div className="callout"><span className="callout-mark">i</span><p>Divergence is total variation distance from the full-source regional baseline. The cultural outlier screen describes concentrated reported sales; it does not establish cultural cause.</p></div>
      <div className="kpi-grid kpi-grid-compact">
        <KpiCard label="Eligible filtered records" value={formatNumber(filtered.length, 0)} note="Full-source divergence metrics matched to current filters" />
        <KpiCard label="Filtered cultural outliers" value={formatNumber(filteredOutliers.length, 0)} note="Passing the documented concentration screen" accent="orange" />
        <KpiCard label="Highest divergence" value={formatNumber(filtered[0]?.regional_divergence_score ?? null, 3)} note="Maximum total variation distance in this view" accent="violet" />
      </div>
      <ChartPanel title="Most regionally concentrated games" subtitle="Ranked by dominant-region sales share. Click a bar to select that game’s dominant region.">
        <RankedBarChart data={concentration.map((row) => ({ game: `${row.name ?? "Unknown title"} · ${row.platform ?? "—"}`, concentration: row.dominant_region_share }))} categoryKey="game" valueKey="concentration" categoryLabel="Game" valueLabel="Dominant-region share" onSelect={(game) => { const selected = concentration.find((row) => `${row.name ?? "Unknown title"} · ${row.platform ?? "—"}` === game); if (selected) dashboard.setFilter("region", selected.dominant_region as typeof dashboard.filters.region); }} />
      </ChartPanel>
      <WhyThisMatters>Concentration highlights titles whose reported sales depend heavily on one region. Checking the game, platform, and genre details helps distinguish a data pattern from a causal explanation.</WhyThisMatters>
      <div className="content-grid">
        <ChartPanel title="Python-derived genre-region affinity" subtitle="Full-source ratios narrowed by selected genre or region; values are not recomputed for other filters."><AffinityHeatmap data={scopedAffinity} /></ChartPanel>
        <DataTable rows={filteredOutliers} columns={columns} title="Cultural outlier candidates" description="This table uses the separate Python output for records that pass the documented screen." pageSize={10} expandable />
      </div>
      <DataTable rows={concentration} columns={columns} title="Regional concentration explorer" description={`${formatNumber(filtered.length, 0)} eligible rows in current scope. Expand a row for all regional shares and baseline proportions.`} pageSize={15} expandable />
    </> : <div className="state-card">No eligible regional records match these filters.</div>}</PageDataState>
  </>;
}
