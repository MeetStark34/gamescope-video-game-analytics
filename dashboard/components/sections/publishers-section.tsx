"use client";

import { useMemo } from "react";
import { ChartPanel } from "@/components/cards/chart-panel";
import { WhyThisMatters } from "@/components/cards/why-this-matters";
import { RankedBarChart } from "@/components/charts/analytics-charts";
import { PageHeader } from "@/components/layout/page-header";
import { PageDataState } from "@/components/layout/load-state";
import { DataTable, type TableColumn } from "@/components/tables/data-table";
import { useDashboard } from "@/lib/dashboard-context";
import { aggregateBy } from "@/lib/dashboard-data";
import { formatNumber, formatPercent } from "@/lib/analytics-data";
import { useAnalytics } from "@/lib/use-analytics";
import type { PublisherSummary, PublisherGenreShare } from "@/lib/types";

const columns: TableColumn<PublisherSummary>[] = [
  { key: "publisher", label: "Publisher" }, { key: "game_count", label: "Game records", align: "right" },
  { key: "genre_count", label: "Genres", align: "right" }, { key: "genres", label: "Genre footprint" },
  { key: "global_sales_total", label: "Selected-region sales", align: "right", format: (value) => formatNumber(value as number, 2) },
  { key: "global_sales_share", label: "View sales share", align: "right", format: (value) => formatPercent(value as number | null) },
];
const genreColumns: TableColumn<PublisherGenreShare>[] = [
  { key: "publisher", label: "Publisher" }, { key: "genre", label: "Genre" },
  { key: "games_with_sales", label: "Records", align: "right" },
  { key: "publisher_genre_sales", label: "Publisher genre sales", align: "right", format: (value) => formatNumber(value as number, 2) },
  { key: "genre_market_share", label: "Genre market share", align: "right", format: (value) => formatPercent(value as number | null) },
  { key: "is_genre_leader", label: ">30% leader" },
];

export function PublishersSection() {
  const dashboard = useDashboard();
  const genreShares = useAnalytics("publisher_genre_market_shares");
  const publishers = useMemo(() => {
    const groups = aggregateBy(dashboard.records, "Publisher", dashboard.filters.region);
    const salesTotal = groups.reduce((sum, row) => sum + row.global_sales_total, 0);
    const genreSets = new Map<string, Set<string>>();
    for (const item of dashboard.records) {
      const publisher = item.Publisher ?? "Missing";
      const genres = genreSets.get(publisher) ?? new Set<string>();
      if (item.Genre) genres.add(item.Genre);
      genreSets.set(publisher, genres);
    }
    return groups.map((row): PublisherSummary => {
      const genres = [...(genreSets.get(row.label) ?? [])].sort();
      return { publisher: row.label, game_count: row.game_count, games_with_sales: row.games_with_sales, genre_count: genres.length, genres, global_sales_total: row.global_sales_total, global_sales_share: salesTotal ? row.global_sales_total / salesTotal : null };
    });
  }, [dashboard.records, dashboard.filters.region]);
  const focusedPublishers = useMemo(() => {
    if (dashboard.filters.publisher !== "all") return [dashboard.filters.publisher];
    return publishers.slice(0, 12).map((row) => row.publisher);
  }, [dashboard.filters.publisher, publishers]);
  const focusedShares = useMemo(() => genreShares.status === "success" ? genreShares.data.filter((row) => focusedPublishers.includes(row.publisher) && (dashboard.filters.genre === "all" || row.genre === dashboard.filters.genre)) : [], [genreShares, focusedPublishers, dashboard.filters.genre]);
  return <>
    <PageHeader eyebrow="Cleaned primary source · vgsales.csv" title="Publisher intelligence" description="Explore publisher sales and portfolio breadth in the selected view; inspect full-source genre leadership for focused publishers." />
    <PageDataState states={[dashboard.status, genreShares]}>{genreShares.status === "success" && dashboard.records.length ? <>
      <ChartPanel title="Publishers by selected-region sales" subtitle="Click a bar to focus the entire dashboard on that publisher."><RankedBarChart data={publishers.slice(0, 12).map((row) => ({ publisher: row.publisher, sales: row.global_sales_total }))} categoryKey="publisher" valueKey="sales" height={370} categoryLabel="Publisher" valueLabel="Sales" selectedValue={dashboard.filters.publisher === "all" ? undefined : dashboard.filters.publisher} onSelect={(value) => dashboard.setFilter("publisher", dashboard.filters.publisher === value ? "all" : value)} /></ChartPanel>
      <WhyThisMatters>Publisher sales totals reflect both the number of releases and their recorded sales. Portfolio breadth helps put a publisher’s total in context; it does not by itself measure profitability or market control.</WhyThisMatters>
      <DataTable rows={publishers} columns={columns} title="Filtered publisher portfolio" description={`${formatNumber(dashboard.summary.recordCount, 0)} cleaned records match the global filters. Use the publisher filter or chart to inspect genre breakdowns.`} />
      <DataTable rows={focusedShares} columns={genreColumns} title="Python-derived publisher genre market shares" description={dashboard.filters.publisher === "all" ? "Full-source genre shares for the leading 12 publishers in this filtered view. Shares are not recalculated for year/platform/region selections." : "Full-source Python market-share output for the selected publisher; strict leadership threshold is greater than 30%."} pageSize={15} expandable />
    </> : dashboard.records.length === 0 ? <div className="state-card">No records match the current filters. Adjust or reset the filters above.</div> : null}</PageDataState>
  </>;
}
