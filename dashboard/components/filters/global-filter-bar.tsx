"use client";

import { RotateCcw } from "lucide-react";
import { usePathname } from "next/navigation";
import { FilterSelect } from "@/components/filters/filter-select";
import { SearchBox } from "@/components/filters/search-box";
import { useDashboard } from "@/lib/dashboard-context";
import { formatNumber } from "@/lib/analytics-data";
import type { RegionScope } from "@/lib/dashboard-data";

const regions: RegionScope[] = ["Global", "North America", "Europe", "Japan", "Other"];

export function GlobalFilterBar() {
  const pathname = usePathname();
  const dashboard = useDashboard();
  if (pathname === "/advanced" || pathname === "/data-quality") return null;
  const { filters, options, status } = dashboard;
  return (
    <section className="global-filter-bar" aria-label="Global filters">
      <div className="global-filter-heading">
        <div><span className="scope-dot" aria-hidden="true" /><strong>Explore this view</strong><span className="filter-source">Primary · vgsales.csv</span></div>
        <div className="filter-summary" role="status" aria-live="polite">
          {status.status === "loading" ? "Loading records…" : status.status === "error" ? "Filters unavailable" : <>{formatNumber(dashboard.summary.recordCount, 0)} of {formatNumber(dashboard.sourceRecords.length, 0)} games <span className="filter-summary-divider">·</span> {formatNumber(dashboard.summary.salesTotal, 2)} {filters.region} sales</>}
          {dashboard.hasActiveFilters ? <button className="reset-filters" type="button" onClick={dashboard.clearFilters}><RotateCcw size={13} /> Reset filters</button> : null}
        </div>
      </div>
      {status.status === "error" ? <div className="filter-error" role="alert"><span>{status.error}</span><button type="button" onClick={dashboard.retry}>Retry</button></div> : status.status === "loading" ? <div className="filter-loading" role="status">Preparing the cleaned primary records for filtering…</div> : (
        <div className="global-filter-controls">
          <div className="filter-range">
            <FilterSelect label="Year from" value={filters.yearFrom == null ? "all" : String(filters.yearFrom)} options={["all", ...options.years.map(String)]} onChange={(value) => dashboard.setYear("yearFrom", value === "all" ? null : Number(value))} />
            <span className="range-separator" aria-hidden="true">to</span>
            <FilterSelect label="Year to" value={filters.yearTo == null ? "all" : String(filters.yearTo)} options={["all", ...options.years.map(String)]} onChange={(value) => dashboard.setYear("yearTo", value === "all" ? null : Number(value))} />
          </div>
          <FilterSelect label="Platform" value={filters.platform} options={["all", ...options.platforms]} onChange={(value) => dashboard.setFilter("platform", value)} />
          <FilterSelect label="Genre" value={filters.genre} options={["all", ...options.genres]} onChange={(value) => dashboard.setFilter("genre", value)} />
          <FilterSelect label="Publisher" value={filters.publisher} options={["all", ...options.publishers]} onChange={(value) => dashboard.setFilter("publisher", value)} />
          <FilterSelect label="Sales region" value={filters.region} options={regions} onChange={(value) => dashboard.setFilter("region", value as RegionScope)} />
          <SearchBox value={filters.search} onChange={(value) => dashboard.setFilter("search", value)} label="Search games, publishers and platforms" placeholder="Games, publishers, platforms" />
        </div>
      )}
      {pathname === "/market-power" ? <p className="filter-scope-note">Market Power scores remain full-source Python metrics; filters narrow the publisher and genre context where available.</p> : null}
    </section>
  );
}
