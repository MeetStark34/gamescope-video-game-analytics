"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { fetchAnalytics, type DataStatus } from "@/lib/analytics-data";
import type { PrimaryDashboardRecord } from "@/lib/types";
import { scopedSales, summarizeRecords, type RegionScope } from "@/lib/dashboard-data";

export type DashboardFilters = {
  yearFrom: number | null;
  yearTo: number | null;
  platform: string;
  genre: string;
  publisher: string;
  region: RegionScope;
  search: string;
};
type FilterKey = keyof DashboardFilters;
type DashboardContextValue = {
  status: DataStatus<PrimaryDashboardRecord[]>;
  sourceRecords: PrimaryDashboardRecord[];
  records: PrimaryDashboardRecord[];
  filters: DashboardFilters;
  options: { years: number[]; platforms: string[]; genres: string[]; publishers: string[] };
  summary: ReturnType<typeof summarizeRecords>;
  setFilter: <K extends FilterKey>(key: K, value: DashboardFilters[K]) => void;
  setYear: (key: "yearFrom" | "yearTo", value: number | null) => void;
  clearFilters: () => void;
  retry: () => void;
  hasActiveFilters: boolean;
};

const initialFilters: DashboardFilters = {
  yearFrom: null, yearTo: null, platform: "all", genre: "all", publisher: "all", region: "Global", search: "",
};
const DashboardContext = createContext<DashboardContextValue | null>(null);

export function DashboardProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const needsDashboardData = pathname !== "/advanced" && pathname !== "/data-quality";
  const [status, setStatus] = useState<DataStatus<PrimaryDashboardRecord[]>>({ status: "loading", data: null, error: null });
  const [revision, setRevision] = useState(0);
  const [filters, setFilters] = useState(initialFilters);
  const cachedRecords = useRef<PrimaryDashboardRecord[] | null>(null);
  useEffect(() => {
    if (!needsDashboardData) return;
    if (cachedRecords.current) {
      setStatus({ status: "success", data: cachedRecords.current, error: null });
      return;
    }
    const controller = new AbortController();
    setStatus({ status: "loading", data: null, error: null });
    fetchAnalytics("dashboard_primary_records", controller.signal)
      .then((data) => { cachedRecords.current = data; setStatus({ status: "success", data, error: null }); })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setStatus({ status: "error", data: null, error: error instanceof Error ? error.message : "Primary records could not be loaded." });
      });
    return () => controller.abort();
  }, [revision, needsDashboardData]);

  const sourceRecords = status.status === "success" ? status.data : [];
  const options = useMemo(() => ({
    years: [...new Set(sourceRecords.map((row) => row.Year).filter((year): year is number => year != null))].sort((a, b) => a - b),
    platforms: unique(sourceRecords.map((row) => row.Platform)),
    genres: unique(sourceRecords.map((row) => row.Genre)),
    publishers: unique(sourceRecords.map((row) => row.Publisher)),
  }), [sourceRecords]);
  const records = useMemo(() => {
    const term = filters.search.trim().toLocaleLowerCase();
    return sourceRecords.filter((row) =>
      (filters.yearFrom == null || (row.Year != null && row.Year >= filters.yearFrom)) &&
      (filters.yearTo == null || (row.Year != null && row.Year <= filters.yearTo)) &&
      (filters.platform === "all" || row.Platform === filters.platform) &&
      (filters.genre === "all" || row.Genre === filters.genre) &&
      (filters.publisher === "all" || row.Publisher === filters.publisher) &&
      (!term || [row.Name, row.Publisher, row.Platform].some((value) => value?.toLocaleLowerCase().includes(term))),
    );
  }, [sourceRecords, filters]);
  const summary = useMemo(() => summarizeRecords(records, filters.region), [records, filters.region]);
  const setFilter = useCallback(<K extends FilterKey,>(key: K, value: DashboardFilters[K]) => {
    setFilters((previous) => ({ ...previous, [key]: value }) as DashboardFilters);
  }, []);
  const setYear = useCallback((key: "yearFrom" | "yearTo", value: number | null) => {
    setFilters((previous) => {
      const next = { ...previous, [key]: value };
      if (next.yearFrom != null && next.yearTo != null && next.yearFrom > next.yearTo) {
        if (key === "yearFrom") next.yearTo = value;
        else next.yearFrom = value;
      }
      return next;
    });
  }, []);
  const clearFilters = useCallback(() => setFilters(initialFilters), []);
  const retry = useCallback(() => { cachedRecords.current = null; setRevision((value) => value + 1); }, []);
  const hasActiveFilters = filters.yearFrom != null || filters.yearTo != null || filters.platform !== "all" || filters.genre !== "all" || filters.publisher !== "all" || filters.region !== "Global" || Boolean(filters.search.trim());

  return <DashboardContext.Provider value={{ status, sourceRecords, records, filters, options, summary, setFilter, setYear, clearFilters, retry, hasActiveFilters }}>{children}</DashboardContext.Provider>;
}

export function useDashboard() {
  const value = useContext(DashboardContext);
  if (!value) throw new Error("useDashboard must be used inside DashboardProvider");
  return value;
}

export function rowSales(record: PrimaryDashboardRecord, region: RegionScope) { return scopedSales(record, region); }

function unique(values: Array<string | null>): string[] {
  return [...new Set(values.filter((value): value is string => value != null && value.trim() !== ""))].sort((a, b) => a.localeCompare(b));
}
