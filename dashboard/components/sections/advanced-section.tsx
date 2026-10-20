"use client";

import { ChartPanel } from "@/components/cards/chart-panel";
import { WhyThisMatters } from "@/components/cards/why-this-matters";
import { KpiCard } from "@/components/cards/kpi-card";
import { CriticSalesScatter, RankedBarChart, TrendChart } from "@/components/charts/analytics-charts";
import { PageHeader } from "@/components/layout/page-header";
import { PageDataState } from "@/components/layout/load-state";
import { DataTable, type TableColumn } from "@/components/tables/data-table";
import { formatDecimal, formatNumber, formatPercent } from "@/lib/analytics-data";
import { useAnalytics } from "@/lib/use-analytics";
import type { CompanyPerformance, CriticScoreBand, VgPlatformLifecycle } from "@/lib/types";

const bandColumns: TableColumn<CriticScoreBand>[] = [
  { key: "score_band", label: "Critic score band" },
  { key: "record_count", label: "Paired records", align: "right" },
  { key: "mean_total_sales", label: "Mean sales", align: "right", format: (v) => formatNumber(v as number | null, 3) },
  { key: "median_total_sales", label: "Median sales", align: "right", format: (v) => formatNumber(v as number | null, 3) },
];
const publisherColumns: TableColumn<CompanyPerformance>[] = [
  { key: "publisher", label: "Publisher" }, { key: "release_records", label: "Records", align: "right" },
  { key: "records_with_sales", label: "With sales", align: "right" },
  { key: "total_sales", label: "Summed sales", align: "right", format: (v) => formatNumber(v as number, 2) },
  { key: "mean_critic_score", label: "Mean critic score", align: "right", format: (v) => formatNumber(v as number | null, 2) },
  { key: "developer_count", label: "Developers", align: "right" },
];
const developerColumns: TableColumn<CompanyPerformance>[] = [
  { key: "developer", label: "Developer" }, { key: "release_records", label: "Records", align: "right" },
  { key: "records_with_sales", label: "With sales", align: "right" },
  { key: "total_sales", label: "Summed sales", align: "right", format: (v) => formatNumber(v as number, 2) },
  { key: "mean_critic_score", label: "Mean critic score", align: "right", format: (v) => formatNumber(v as number | null, 2) },
  { key: "console_count", label: "Consoles", align: "right" },
];
const lifecycleColumns: TableColumn<VgPlatformLifecycle>[] = [
  { key: "console", label: "Console" }, { key: "first_observed_release_year", label: "First year", align: "right" },
  { key: "last_observed_release_year", label: "Last year", align: "right" },
  { key: "observed_active_year_count", label: "Active years", align: "right" },
  { key: "peak_sales_year", label: "Peak sales year", align: "right" },
  { key: "peak_annual_sales", label: "Peak annual sales", align: "right", format: (v) => formatNumber(v as number | null, 2) },
];

export function AdvancedSection() {
  const profile = useAnalytics("vgchartz_profile");
  const association = useAnalytics("critic_score_sales_association");
  const points = useAnalytics("critic_score_sales_points");
  const publishers = useAnalytics("vgchartz_publisher_performance");
  const developers = useAnalytics("vgchartz_developer_performance");
  const companyPairs = useAnalytics("vgchartz_publisher_developer_performance");
  const lifecycle = useAnalytics("vgchartz_platform_lifecycle");
  const recent = useAnalytics("vgchartz_recent_industry_trends_annual");
  const months = useAnalytics("vgchartz_release_by_month");
  const dates = useAnalytics("vgchartz_release_date_trends");
  return <>
    <PageHeader eyebrow="Supplemental dataset · vgchartz-2024.csv" title="Advanced analysis" description="Ratings, companies, console evolution, and release timing from the supplemental source, kept separate from assignment results." />
    <PageDataState states={[profile, association, points, publishers, developers, companyPairs, lifecycle, recent, months, dates]}>
      {profile.status === "success" && association.status === "success" && points.status === "success" && publishers.status === "success" && developers.status === "success" && companyPairs.status === "success" && lifecycle.status === "success" && recent.status === "success" && months.status === "success" && dates.status === "success" ? <>
        <div className="callout"><span className="callout-mark">i</span><p>These tables use vgchartz-2024.csv only. Associations are descriptive: critic scores and sales may be missing non-randomly, and correlation does not establish causation.</p></div>
        <div className="kpi-grid">
          <KpiCard label="Supplemental records" value={formatNumber(profile.data.row_count, 0)} note="Kept separate from vgsales.csv" />
          <KpiCard label="Paired rating & sales" value={formatNumber(association.data.eligible_pair_count, 0)} note={`${formatPercent(association.data.eligible_pair_percent == null ? null : association.data.eligible_pair_percent / 100)} of all source records`} accent="orange" />
          <KpiCard label="Pearson · raw sales" value={formatDecimal(association.data.critic_score_sales_pearson_r, 3)} note="Linear correlation, eligible pairs only" accent="green" />
          <KpiCard label="Spearman · ranks" value={formatDecimal(association.data.critic_score_sales_spearman_rho, 3)} note="Rank association, eligible pairs only" accent="violet" />
        </div>
        <div className="content-grid">
          <ChartPanel title="Critic score and sales" subtitle="Each point is one game-console record with both valid values."><CriticSalesScatter data={points.data} /></ChartPanel>
          <ChartPanel title="Rating bands" subtitle="One-point score ranges; sample count and medians are shown below."><RankedBarChart data={association.data.critic_score_bands.filter((row) => row.record_count > 0).map((row) => ({ band: row.score_band, sales: row.median_total_sales ?? 0 }))} categoryKey="band" valueKey="sales" color="var(--chart-2)" horizontal={false} height={280} /></ChartPanel>
        </div>
        <WhyThisMatters>The association describes records with both values present. Coverage and the rating-band summaries make that selection visible; differences should not be read as a causal effect of ratings on sales.</WhyThisMatters>
        <DataTable rows={association.data.critic_score_bands} columns={bandColumns} title="Critic score band detail" description="Means and medians are calculated only from eligible pairs." pageSize={10} expandable />
        <ChartPanel title="Recent observed release-year window" subtitle={`The prepared window is ${recent.data[0]?.year ?? "—"}–${recent.data.at(-1)?.year ?? "—"}; years follow source release dates.`}>
          <TrendChart data={recent.data} salesKey="total_sales" countKey="release_records" salesLabel="Total sales" countLabel="Release records" />
        </ChartPanel>
        <div className="content-grid">
          <ChartPanel title="Release timing by month" subtitle="Valid ISO dates; January 1 dates remain included but may be imprecise."><RankedBarChart data={months.data.map((row) => ({ month: new Intl.DateTimeFormat("en", { month: "short" }).format(new Date(2020, row.month - 1, 1)), releases: row.release_records }))} categoryKey="month" valueKey="releases" horizontal={false} height={280} /></ChartPanel>
          <div className="panel panel-copy date-note"><p className="eyebrow">Date quality</p><h2>{formatNumber(dates.data.valid_iso_release_dates, 0)} valid release dates</h2><p>{formatNumber(dates.data.missing_or_invalid_release_dates, 0)} records have no usable release date. {formatNumber(dates.data.jan_1_possible_imprecise_dates, 0)} dates fall on January 1 and are flagged as possibly year-only estimates.</p><p className="small-note">{dates.data.date_precision_note}</p></div>
        </div>
        <WhyThisMatters>Release timing can change the mix of records observed in recent years. The source’s date completeness and possible year-only dates should be considered when reading the trend.</WhyThisMatters>
        <ChartPanel title="Developer performance" subtitle="Leading developers by summed sales from the supplemental source; record coverage is shown in the table.">
          <RankedBarChart data={developers.data.slice(0, 12).map((row) => ({ developer: row.developer ?? "Unknown", sales: row.total_sales }))} categoryKey="developer" valueKey="sales" categoryLabel="Developer" valueLabel="Summed sales" />
        </ChartPanel>
        <WhyThisMatters>Developer totals reflect the source’s observed releases and sales coverage. They are descriptive comparisons across literal source labels, not an estimate of developer quality or causal impact.</WhyThisMatters>
        <DataTable rows={lifecycle.data} columns={lifecycleColumns} title="Console evolution" description="Observed life span and peak annual sales by console; console labels are not mapped to primary Platform labels." expandable />
        <DataTable rows={publishers.data} columns={publisherColumns} title="Supplemental publisher performance" description="Literal publisher names, sales coverage, critic-score coverage, and developer breadth." expandable />
        <DataTable rows={developers.data} columns={developerColumns} title="Developer performance detail" description="Literal developer labels; Unknown remains distinct from a blank value." expandable />
        <DataTable rows={companyPairs.data} columns={[
          { key: "publisher", label: "Publisher" }, { key: "developer", label: "Developer" },
          { key: "release_records", label: "Records", align: "right" },
          { key: "total_sales", label: "Summed sales", align: "right", format: (v) => formatNumber(v as number, 2) },
          { key: "mean_critic_score", label: "Mean critic score", align: "right", format: (v) => formatNumber(v as number | null, 2) },
        ]} title="Publisher and developer combinations" description="Literal label pairs aggregated from the supplemental source; no entity matching was applied." expandable />
      </> : null}
    </PageDataState>
  </>;
}
