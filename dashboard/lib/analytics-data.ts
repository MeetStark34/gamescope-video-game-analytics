import type { AnalyticsDataMap, AnalyticsKey } from "@/lib/types";

export type DataStatus<T> =
  | { status: "loading"; data: null; error: null }
  | { status: "success"; data: T; error: null }
  | { status: "error"; data: null; error: string };

export async function fetchAnalytics<K extends AnalyticsKey>(key: K, signal?: AbortSignal): Promise<AnalyticsDataMap[K]> {
  const response = await fetch(`/data/analytics/${key}.json`, { signal, cache: "force-cache" });
  if (!response.ok) {
    throw new Error(`Analytics file “${key}” could not be loaded (${response.status}). Run the dashboard sync step and retry.`);
  }
  return (await response.json()) as AnalyticsDataMap[K];
}

export const formatNumber = (value: number | null | undefined, digits = 1) =>
  value == null || !Number.isFinite(value)
    ? "—"
    : new Intl.NumberFormat("en-US", { maximumFractionDigits: digits }).format(value);

export const formatPercent = (value: number | null | undefined, digits = 1) =>
  value == null || !Number.isFinite(value) ? "—" : `${(value * 100).toFixed(digits)}%`;

export const formatDecimal = (value: number | null | undefined, digits = 2) =>
  value == null || !Number.isFinite(value) ? "—" : value.toFixed(digits);
