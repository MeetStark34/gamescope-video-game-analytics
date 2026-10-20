"use client";

import { useMemo } from "react";
import { ChartPanel } from "@/components/cards/chart-panel";
import { WhyThisMatters } from "@/components/cards/why-this-matters";
import { RegionalSalesChart, AffinityHeatmap, YearDivergenceChart } from "@/components/charts/analytics-charts";
import { PageHeader } from "@/components/layout/page-header";
import { PageDataState } from "@/components/layout/load-state";
import { DataTable, type TableColumn } from "@/components/tables/data-table";
import { useDashboard } from "@/lib/dashboard-context";
import { aggregateRegions } from "@/lib/dashboard-data";
import { formatNumber, formatPercent } from "@/lib/analytics-data";
import { useAnalytics } from "@/lib/use-analytics";
import type { RegionalSales, RegionalStability, RegionalYearDivergence, GenreAffinity } from "@/lib/types";

const regionColumns: TableColumn<RegionalSales>[] = [
  { key: "region", label: "Region" }, { key: "sales_records", label: "Records with sales", align: "right" },
  { key: "sales_total", label: "Sales", align: "right", format: (value) => formatNumber(value as number, 2) },
  { key: "sales_mean", label: "Mean per record", align: "right", format: (value) => formatNumber(value as number | null, 3) },
  { key: "share_of_reported_regional_sales", label: "Share of regional total", align: "right", format: (value) => formatPercent(value as number | null) },
];
const divergenceColumns: TableColumn<RegionalYearDivergence>[] = [
  { key: "year", label: "Year", align: "right" }, { key: "regions_compared", label: "Regions compared", align: "right" },
  { key: "mean_pairwise_divergence", label: "Mean pairwise distance", align: "right", format: (value) => formatNumber(value as number | null, 3) },
];
const stabilityColumns: TableColumn<RegionalStability>[] = [
  { key: "region", label: "Region" }, { key: "observed_years", label: "Observed years", align: "right" },
  { key: "adjacent_observed_year_pairs", label: "Year pairs", align: "right" }, { key: "same_favorite_pairs", label: "Same favorite", align: "right" },
  { key: "preference_stability_index", label: "Stability", align: "right", format: (value) => formatPercent(value as number | null) },
];

export function RegionsSection() {
  const dashboard = useDashboard();
  const affinity = useAnalytics("genre_region_affinity");
  const annual = useAnalytics("regional_preference_divergence_by_year");
  const stability = useAnalytics("regional_preference_stability");
  const regional = useMemo(() => aggregateRegions(dashboard.records), [dashboard.records]);
  const filteredAnnual = useMemo(() => annual.status === "success" ? annual.data.filter((row) => (dashboard.filters.yearFrom == null || row.year >= dashboard.filters.yearFrom) && (dashboard.filters.yearTo == null || row.year <= dashboard.filters.yearTo)) : [], [annual, dashboard.filters.yearFrom, dashboard.filters.yearTo]);
  const filteredAffinity = useMemo(() => affinity.status === "success" ? affinity.data.filter((row) => (dashboard.filters.genre === "all" || row.genre === dashboard.filters.genre) && (dashboard.filters.region === "Global" || row.region === dashboard.filters.region)) : [], [affinity, dashboard.filters.genre, dashboard.filters.region]);
  const filteredStability = useMemo(() => stability.status === "success" ? stability.data.filter((row) => dashboard.filters.region === "Global" || row.region === dashboard.filters.region) : [], [stability, dashboard.filters.region]);
  return <>
    <PageHeader eyebrow="Cleaned primary source · vgsales.csv" title="Regional intelligence" description="Compare source-reported regional sales in the filtered catalogue, with Python-derived preference metrics shown at their full-source scope." />
    <PageDataState states={[dashboard.status, affinity, annual, stability]}>{affinity.status === "success" && annual.status === "success" && stability.status === "success" && dashboard.records.length ? <>
      <div className="content-grid">
        <ChartPanel title="Regional sales in the current view" subtitle="Click a region to change the selected sales measure across the dashboard."><RegionalSalesChart data={regional} selectedRegion={dashboard.filters.region === "Global" ? undefined : dashboard.filters.region} onSelect={(region) => dashboard.setFilter("region", dashboard.filters.region === region ? "Global" : region as typeof dashboard.filters.region)} /></ChartPanel>
        <div className="panel panel-copy"><p className="eyebrow">Region scope</p><h2>Source definitions remain distinct</h2><p>Europe here is `EU_Sales`; the supplemental dataset uses PAL. Regional totals change with year, platform, genre, publisher, and search filters.</p><div className="inline-stat"><span>Matched records</span><b>{formatNumber(dashboard.summary.recordCount, 0)}</b></div></div>
      </div>
      <WhyThisMatters>Regional sales describe the source’s recorded estimates, not market-normalized performance. Comparing regional totals within the same filtered catalogue keeps the displayed scope explicit.</WhyThisMatters>
      <DataTable rows={regional} columns={regionColumns} title="Filtered regional totals" description="Totals include rows with valid values for each region; missing values remain excluded." />
      <DataTable rows={filteredStability} columns={stabilityColumns} title="Python-derived regional preference stability" description="Full-source favorite-genre stability. Region selection narrows the rows; other global filters do not recalculate this metric." expandable />
      <ChartPanel title="Python-derived genre affinity" subtitle="Full-source affinity values, narrowed by selected genre or region; not recomputed from the current row filters."><AffinityHeatmap data={filteredAffinity} /></ChartPanel>
      <div className="content-grid">
        <ChartPanel title="Regional genre divergence over time" subtitle="Full-source pairwise distance between regional genre mixes. Select a year to narrow the dashboard."><YearDivergenceChart data={filteredAnnual} onSelectYear={(year) => { dashboard.setYear("yearFrom", year); dashboard.setYear("yearTo", year); }} /></ChartPanel>
        <DataTable rows={filteredAnnual} columns={divergenceColumns} title="Yearly divergence values" description="Precomputed total-variation distances from the full source." expandable />
      </div>
    </> : dashboard.records.length === 0 ? <div className="state-card">No records match the current filters. Adjust or reset the filters above.</div> : null}</PageDataState>
  </>;
}
