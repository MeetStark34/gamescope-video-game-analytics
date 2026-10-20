import type { PrimaryDashboardRecord, RegionalSales, AnnualTrend, TopGame } from "@/lib/types";

export type RegionScope = "Global" | "North America" | "Europe" | "Japan" | "Other";
export type ScopedGroup = {
  label: string;
  game_count: number;
  games_with_sales: number;
  global_sales_total: number;
  global_sales_mean: number | null;
  global_sales_share: number | null;
};

const regionFields: Record<RegionScope, keyof PrimaryDashboardRecord | null> = {
  Global: "Global_Sales",
  "North America": "NA_Sales",
  Europe: "EU_Sales",
  Japan: "JP_Sales",
  Other: "Other_Sales",
};

export function scopedSales(record: PrimaryDashboardRecord, region: RegionScope): number | null {
  const field = regionFields[region];
  return field ? record[field] as number | null : null;
}

export function summarizeRecords(records: PrimaryDashboardRecord[], region: RegionScope) {
  let salesCount = 0;
  let salesTotal = 0;
  for (const record of records) {
    const value = scopedSales(record, region);
    if (value != null && Number.isFinite(value)) { salesCount += 1; salesTotal += value; }
  }
  return {
    recordCount: records.length,
    gamesWithSales: salesCount,
    salesTotal,
    salesMean: salesCount ? salesTotal / salesCount : null,
  };
}

export function aggregateBy(
  records: PrimaryDashboardRecord[],
  field: "Genre" | "Platform" | "Publisher",
  region: RegionScope,
): ScopedGroup[] {
  const groups = new Map<string, { count: number; salesCount: number; salesTotal: number }>();
  for (const record of records) {
    const label = record[field] ?? "Missing";
    const group = groups.get(label) ?? { count: 0, salesCount: 0, salesTotal: 0 };
    group.count += 1;
    const value = scopedSales(record, region);
    if (value != null && Number.isFinite(value)) { group.salesCount += 1; group.salesTotal += value; }
    groups.set(label, group);
  }
  const totalSales = [...groups.values()].reduce((sum, group) => sum + group.salesTotal, 0);
  return [...groups.entries()].map(([label, group]) => ({
    label,
    game_count: group.count,
    games_with_sales: group.salesCount,
    global_sales_total: group.salesTotal,
    global_sales_mean: group.salesCount ? group.salesTotal / group.salesCount : null,
    global_sales_share: totalSales ? group.salesTotal / totalSales : null,
  })).sort((a, b) => b.global_sales_total - a.global_sales_total || a.label.localeCompare(b.label));
}

export function aggregateAnnual(records: PrimaryDashboardRecord[], region: RegionScope): AnnualTrend[] {
  const groups = new Map<number, { releases: number; salesCount: number; salesTotal: number }>();
  for (const record of records) {
    if (record.Year == null) continue;
    const group = groups.get(record.Year) ?? { releases: 0, salesCount: 0, salesTotal: 0 };
    group.releases += 1;
    const value = scopedSales(record, region);
    if (value != null && Number.isFinite(value)) { group.salesCount += 1; group.salesTotal += value; }
    groups.set(record.Year, group);
  }
  return [...groups.entries()].sort(([a], [b]) => a - b).map(([year, group]) => ({
    year,
    games_released: group.releases,
    games_with_year_and_sales: group.salesCount,
    global_sales_total: group.salesCount ? group.salesTotal : null,
    global_sales_mean: group.salesCount ? group.salesTotal / group.salesCount : null,
  }));
}

export function aggregatePlatformEvolution(records: PrimaryDashboardRecord[], region: RegionScope, platform: string): Array<{ platform: string; year: number; games_released: number; games_with_sales: number; global_sales_total: number | null }> {
  const groups = new Map<number, { count: number; salesCount: number; salesTotal: number }>();
  for (const record of records) {
    if (record.Platform !== platform || record.Year == null) continue;
    const group = groups.get(record.Year) ?? { count: 0, salesCount: 0, salesTotal: 0 };
    group.count += 1;
    const value = scopedSales(record, region);
    if (value != null && Number.isFinite(value)) { group.salesCount += 1; group.salesTotal += value; }
    groups.set(record.Year, group);
  }
  return [...groups.entries()].sort(([a], [b]) => a - b).map(([year, group]) => ({ platform, year, games_released: group.count, games_with_sales: group.salesCount, global_sales_total: group.salesCount ? group.salesTotal : null }));
}

export function topGameRecords(records: PrimaryDashboardRecord[], region: RegionScope, limit = 10): TopGame[] {
  return records.filter((record) => scopedSales(record, region) != null).map((record) => ({
    name: record.Name,
    platform: record.Platform,
    year: record.Year,
    genre: record.Genre,
    publisher: record.Publisher,
    global_sales: scopedSales(record, region) ?? 0,
    sales_rank: record.Rank ?? Number.MAX_SAFE_INTEGER,
    source_row: record.source_row,
    duplicate_status: record.duplicate_status,
    sales_by_region: { north_america: record.NA_Sales, europe: record.EU_Sales, japan: record.JP_Sales, other: record.Other_Sales },
  })).sort((a, b) => b.global_sales - a.global_sales || a.sales_rank - b.sales_rank).slice(0, limit)
    .map((game, index) => ({ ...game, sales_rank: index + 1 }));
}

export function aggregateRegions(records: PrimaryDashboardRecord[]): RegionalSales[] {
  const regions: Array<{ label: Exclude<RegionScope, "Global">; field: keyof PrimaryDashboardRecord }> = [
    { label: "North America", field: "NA_Sales" }, { label: "Europe", field: "EU_Sales" },
    { label: "Japan", field: "JP_Sales" }, { label: "Other", field: "Other_Sales" },
  ];
  const values = regions.map(({ label, field }) => {
    let recordsWithSales = 0; let salesTotal = 0;
    for (const record of records) {
      const value = record[field] as number | null;
      if (value != null && Number.isFinite(value)) { recordsWithSales += 1; salesTotal += value; }
    }
    return { region: label, sales_records: recordsWithSales, sales_total: salesTotal, sales_mean: recordsWithSales ? salesTotal / recordsWithSales : null, share_of_reported_regional_sales: null as number | null };
  });
  const total = values.reduce((sum, item) => sum + item.sales_total, 0);
  return values.map((item) => ({ ...item, share_of_reported_regional_sales: total ? item.sales_total / total : null }));
}

export function topConcentrated<T extends { dominant_region_share: number; regional_divergence_score: number }>(rows: T[], limit = 12): T[] {
  return [...rows].sort((a, b) => b.dominant_region_share - a.dominant_region_share || b.regional_divergence_score - a.regional_divergence_score).slice(0, limit);
}
