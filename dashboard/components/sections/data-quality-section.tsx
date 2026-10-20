"use client";

import { AlertTriangle, Database, FileCheck2, Rows3 } from "lucide-react";
import { KpiCard } from "@/components/cards/kpi-card";
import { PageHeader } from "@/components/layout/page-header";
import { PageDataState } from "@/components/layout/load-state";
import { DataTable, type TableColumn } from "@/components/tables/data-table";
import { formatNumber } from "@/lib/analytics-data";
import { useAnalytics } from "@/lib/use-analytics";
import type { DashboardDataQuality, SourceDataQuality } from "@/lib/types";

type FieldCount = { source: string; field: string; count: number };
type SourceCounts = { source: string; original_rows: number; cleaned_rows: number; rows_removed: number; missing_value_total: number; exact_duplicate_groups_flagged: number; potential_duplicate_groups_flagged: number; transformation_events: number };
const missingColumns: TableColumn<FieldCount>[] = [
  { key: "source", label: "Source" }, { key: "field", label: "Cleaned field" }, { key: "count", label: "Missing values", align: "right", format: (value) => formatNumber(value as number, 0) },
];
const transformationColumns: TableColumn<FieldCount>[] = [
  { key: "source", label: "Source" }, { key: "field", label: "Field" }, { key: "count", label: "Logged cell transformations", align: "right", format: (value) => formatNumber(value as number, 0) },
];
const sourceColumns: TableColumn<SourceCounts>[] = [
  { key: "source", label: "Dataset" }, { key: "original_rows", label: "Original rows", align: "right", format: (value) => formatNumber(value as number, 0) },
  { key: "cleaned_rows", label: "Cleaned rows", align: "right", format: (value) => formatNumber(value as number, 0) },
  { key: "rows_removed", label: "Rows removed", align: "right", format: (value) => formatNumber(value as number, 0) },
  { key: "missing_value_total", label: "Missing values", align: "right", format: (value) => formatNumber(value as number, 0) },
  { key: "exact_duplicate_groups_flagged", label: "Exact duplicate groups", align: "right" },
  { key: "potential_duplicate_groups_flagged", label: "Potential duplicate groups", align: "right" },
  { key: "transformation_events", label: "Transformations", align: "right", format: (value) => formatNumber(value as number, 0) },
];

export function DataQualitySection() {
  const quality = useAnalytics("dashboard_data_quality");
  const manifest = useAnalytics("dashboard_manifest");
  return <>
    <PageHeader eyebrow="Raw → cleaned → derived" title="Data quality & provenance" description="Inspect original and cleaned row counts, field missingness, duplicate candidates, and transformations recorded by the Python cleaning pipeline." />
    <PageDataState states={[quality, manifest]}>{quality.status === "success" && manifest.status === "success" ? <>
      <div className="kpi-grid">
        <KpiCard label="Original source rows" value={formatNumber(quality.data.original_rows, 0)} note="Raw vgsales.csv records" icon={<Database size={17} />} />
        <KpiCard label="Cleaned rows" value={formatNumber(quality.data.cleaned_rows, 0)} note="vgsales_clean.csv · all rows retained" icon={<Rows3 size={17} />} accent="green" />
        <KpiCard label="Missing field values" value={formatNumber(quality.data.missing_value_total, 0)} note="Counted in cleaned primary fields" icon={<AlertTriangle size={17} />} accent="orange" />
        <KpiCard label="Logged transformations" value={formatNumber(quality.data.transformation_events, 0)} note={`${formatNumber(quality.data.rows_with_transformations, 0)} source rows affected`} icon={<FileCheck2 size={17} />} accent="violet" />
      </div>
      <div className="lineage-grid" aria-label="Data stages">
        <article><span>01 · Raw data</span><h2>vgsales.csv</h2><p>{formatNumber(quality.data.original_rows, 0)} source rows. The source file remains unchanged.</p></article>
        <span className="lineage-arrow" aria-hidden="true">→</span>
        <article><span>02 · Cleaned data</span><h2>vgsales_clean.csv</h2><p>{formatNumber(quality.data.cleaned_rows, 0)} rows. Nulls, text, and duplicate flags are preserved by policy.</p></article>
        <span className="lineage-arrow" aria-hidden="true">→</span>
        <article><span>03 · Derived metrics</span><h2>Python analytics</h2><p>{formatNumber(manifest.data.exported_files, 0)} dashboard outputs. Rankings and indices retain their documented scope.</p></article>
      </div>
      <div className="callout"><span className="callout-mark">i</span><p>{quality.data.duplicate_policy} Missing values are not imputed; literal labels such as Unknown remain distinct from blanks. The vgchartz source is inspected separately on Advanced Analysis.</p></div>
      <DataTable rows={sourceRows(quality.data)} columns={sourceColumns} title="Source-to-cleaned row comparison" description="Counts are read from the actual Python cleaning summary for both datasets; candidate duplicates were retained." pageSize={4} />
      <div className="content-grid">
        <DataTable rows={missingRows(quality.data)} columns={missingColumns} title="Missing values by cleaned field" description="Blank cleaned values counted directly from each processed CSV." pageSize={12} />
        <DataTable rows={transformationRows(quality.data)} columns={transformationColumns} title="Documented transformations" description="Cell-level changes recorded in the Python cleaning log, grouped by source and field." pageSize={12} />
      </div>
      <div className="quality-summary-grid">
        <section className="panel panel-copy"><p className="eyebrow">Duplicate handling</p><h2>Flagged, never silently removed</h2><p>{formatNumber(quality.data.exact_duplicate_groups_flagged, 0)} exact duplicate groups and {formatNumber(quality.data.potential_duplicate_groups_flagged, 0)} potential game-key groups were flagged. {formatNumber(quality.data.duplicate_rows_flagged, 0)} rows were included in those candidate flags.</p><p className="small-note">Rows removed: {formatNumber(quality.data.rows_removed, 0)}. Candidate groups can represent ports, editions, or source repeats.</p></section>
        <section className="panel panel-copy"><p className="eyebrow">Cleaning rules</p><h2>Preserve meaning where uncertain</h2><p>{quality.data.categorical_policy}</p><p className="small-note">{quality.data.missing_policy}</p></section>
      </div>
    </> : null}</PageDataState>
  </>;
}

function missingRows(data: DashboardDataQuality): FieldCount[] {
  const primary = Object.entries(data.missing_values_by_field).map(([field, count]) => ({ source: "vgsales.csv", field, count }));
  const advanced = Object.entries(data.advanced_source?.missing_values_by_field ?? {}).map(([field, count]) => ({ source: "vgchartz-2024.csv", field, count }));
  return [...primary, ...advanced];
}
function transformationRows(data: DashboardDataQuality): FieldCount[] {
  const primary = Object.entries(data.transformations_by_field).map(([field, count]) => ({ source: "vgsales.csv", field, count }));
  const advanced = Object.entries(data.advanced_source?.transformations_by_field ?? {}).map(([field, count]) => ({ source: "vgchartz-2024.csv", field, count }));
  return [...primary, ...advanced].sort((a, b) => b.count - a.count);
}
function sourceRows(data: DashboardDataQuality): SourceCounts[] {
  const sources: SourceDataQuality[] = [data];
  if (data.advanced_source) sources.push(data.advanced_source);
  return sources.map((row) => ({
    source: row.source_dataset, original_rows: row.original_rows, cleaned_rows: row.cleaned_rows, rows_removed: row.rows_removed,
    missing_value_total: row.missing_value_total, exact_duplicate_groups_flagged: row.exact_duplicate_groups_flagged,
    potential_duplicate_groups_flagged: row.potential_duplicate_groups_flagged, transformation_events: row.transformation_events,
  }));
}
