"use client";

import { useMemo } from "react";
import { ChartPanel } from "@/components/cards/chart-panel";
import { WhyThisMatters } from "@/components/cards/why-this-matters";
import { PageHeader } from "@/components/layout/page-header";
import { PageDataState } from "@/components/layout/load-state";
import { RankedBarChart, PlatformTrendChart } from "@/components/charts/analytics-charts";
import { DataTable, type TableColumn } from "@/components/tables/data-table";
import { formatNumber } from "@/lib/analytics-data";
import { aggregateBy, aggregatePlatformEvolution } from "@/lib/dashboard-data";
import { useDashboard } from "@/lib/dashboard-context";

type PlatformRow = { platform: string; game_count: number; games_with_sales: number; global_sales_total: number; global_sales_mean: number | null; global_sales_share: number | null };
const columns: TableColumn<PlatformRow>[] = [
  { key: "platform", label: "Platform" }, { key: "game_count", label: "Game records", align: "right" },
  { key: "games_with_sales", label: "Records with sales", align: "right" },
  { key: "global_sales_total", label: "Selected-region sales", align: "right", format: (value) => formatNumber(value as number, 2) },
  { key: "global_sales_mean", label: "Mean sales", align: "right", format: (value) => formatNumber(value as number | null, 3) },
];

export function PlatformsSection() {
  const dashboard = useDashboard();
  const sales = useMemo(() => aggregateBy(dashboard.records, "Platform", dashboard.filters.region).map((row) => ({ platform: row.label, game_count: row.game_count, games_with_sales: row.games_with_sales, global_sales_total: row.global_sales_total, global_sales_mean: row.global_sales_mean, global_sales_share: row.global_sales_share })), [dashboard.records, dashboard.filters.region]);
  const selectedPlatform = dashboard.filters.platform === "all" ? sales[0]?.platform : dashboard.filters.platform;
  const evolution = useMemo(() => selectedPlatform ? aggregatePlatformEvolution(dashboard.records, dashboard.filters.region, selectedPlatform) : [], [dashboard.records, dashboard.filters.region, selectedPlatform]);
  return <>
    <PageHeader eyebrow="Cleaned primary source · vgsales.csv" title="Platform analysis" description="Compare selected-region sales and catalogue volume. Select a platform in the chart to cross-filter other views." />
    <PageDataState states={[dashboard.status]}>{dashboard.records.length ? <>
      <div className="content-grid">
        <ChartPanel title="Leading platforms by selected-region sales" subtitle="Click a bar to filter every primary-source view by platform."><RankedBarChart data={sales.slice(0, 14).map((row) => ({ platform: row.platform, sales: row.global_sales_total }))} categoryKey="platform" valueKey="sales" categoryLabel="Platform" valueLabel="Sales" selectedValue={dashboard.filters.platform === "all" ? undefined : dashboard.filters.platform} onSelect={(value) => dashboard.setFilter("platform", dashboard.filters.platform === value ? "all" : value)} /></ChartPanel>
        <ChartPanel title={selectedPlatform ? `${selectedPlatform} over time` : "Platform activity over time"} subtitle="Yearly releases and sales for the leading platform in the current view, or the selected platform.">
          {evolution.length ? <PlatformTrendChart data={evolution} /> : <div className="chart-empty">No platform-year records match these filters.</div>}
        </ChartPanel>
      </div>
      <WhyThisMatters>Platform sales totals combine catalogue size and performance. The yearly series shows when releases and sales are observed, while the source does not describe the full lifecycle of every platform.</WhyThisMatters>
      <DataTable rows={sales} columns={columns} title="Filtered platform sales and volume" description={`${formatNumber(dashboard.summary.recordCount, 0)} cleaned records match the global filters.`} expandable />
    </> : <div className="state-card">No records match the current filters. Adjust or reset the filters above.</div>}</PageDataState>
  </>;
}
