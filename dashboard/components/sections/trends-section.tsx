"use client";

import { useMemo } from "react";
import { ChartPanel } from "@/components/cards/chart-panel";
import { WhyThisMatters } from "@/components/cards/why-this-matters";
import { DataTable, type TableColumn } from "@/components/tables/data-table";
import { PageHeader } from "@/components/layout/page-header";
import { PageDataState } from "@/components/layout/load-state";
import { TrendChart } from "@/components/charts/analytics-charts";
import { formatNumber } from "@/lib/analytics-data";
import { aggregateAnnual } from "@/lib/dashboard-data";
import { useDashboard } from "@/lib/dashboard-context";
import type { AnnualTrend } from "@/lib/types";

const columns: TableColumn<AnnualTrend>[] = [
  { key: "year", label: "Year", align: "right" }, { key: "games_released", label: "Game records", align: "right" },
  { key: "games_with_year_and_sales", label: "With year & sales", align: "right" },
  { key: "global_sales_total", label: "Selected-region sales", align: "right", format: (value) => formatNumber(value as number | null, 2) },
  { key: "global_sales_mean", label: "Mean sales / record", align: "right", format: (value) => formatNumber(value as number | null, 3) },
];

export function TrendsSection() {
  const dashboard = useDashboard();
  const annual = useMemo(() => aggregateAnnual(dashboard.records, dashboard.filters.region), [dashboard.records, dashboard.filters.region]);
  return <>
    <PageHeader eyebrow="Cleaned primary source · vgsales.csv" title="Market trends" description="Explore release activity and sales with the shared year, platform, genre, publisher, and region filters." />
    <PageDataState states={[dashboard.status]}>{dashboard.records.length ? <>
      <ChartPanel title={`Annual ${dashboard.filters.region.toLowerCase()} sales and releases`} subtitle="Select a year on the chart to focus all primary-source views on that year.">
        <TrendChart data={annual} salesLabel={`${dashboard.filters.region} sales`} onSelectYear={(year) => { dashboard.setYear("yearFrom", year); dashboard.setYear("yearTo", year); }} />
      </ChartPanel>
      <WhyThisMatters>Release counts and sales are separate measures. A year with many listed games may not have the highest summed sales; rows without a valid year cannot appear in this timeline.</WhyThisMatters>
      <DataTable rows={annual} columns={columns} title="Filtered annual trend detail" description={`${formatNumber(dashboard.summary.recordCount, 0)} cleaned records match the global filters.`} />
    </> : <div className="state-card">No records match the current filters. Adjust or reset the filters above.</div>}</PageDataState>
  </>;
}
