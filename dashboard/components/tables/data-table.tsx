"use client";

import { Fragment, useMemo, useState } from "react";
import { ChevronDown, ChevronLeft, ChevronRight } from "lucide-react";
import { SearchBox } from "@/components/filters/search-box";
import { formatNumber } from "@/lib/analytics-data";

export type TableRow = Record<string, unknown>;
export type TableColumn<T extends object> = {
  key: keyof T & string;
  label: string;
  align?: "left" | "right";
  format?: (value: unknown, row: T) => string;
  sortValue?: (value: unknown, row: T) => string | number | null;
};

function displayValue(value: unknown): string {
  if (value == null || value === "") return "—";
  if (typeof value === "number") return formatNumber(value, value % 1 === 0 ? 0 : 2);
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return Object.entries(value as Record<string, unknown>)
    .map(([key, item]) => `${key}: ${typeof item === "number" ? formatNumber(item, 2) : String(item)}`).join(" · ");
  return String(value);
}

export function DataTable<T extends object>({ rows, columns, title, description, pageSize = 12, emptyMessage = "No matching records.", expandable = false }: {
  rows: T[];
  columns: Array<TableColumn<T>>;
  title: string;
  description?: string;
  pageSize?: number;
  emptyMessage?: string;
  expandable?: boolean;
}) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<string>(columns[0]?.key ?? "");
  const [descending, setDescending] = useState(true);
  const [page, setPage] = useState(0);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(() => new Set());
  const visible = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    const matched = normalized ? rows.filter((row) => columns.some(({ key }) => displayValue((row as TableRow)[key]).toLocaleLowerCase().includes(normalized))) : rows;
    const column = columns.find((item) => item.key === sortKey);
    if (!column) return matched;
    return [...matched].sort((a, b) => {
      const leftValue = (a as TableRow)[column.key];
      const rightValue = (b as TableRow)[column.key];
      const left = column.sortValue ? column.sortValue(leftValue, a) : leftValue as string | number | null;
      const right = column.sortValue ? column.sortValue(rightValue, b) : rightValue as string | number | null;
      if (left == null) return right == null ? 0 : 1;
      if (right == null) return -1;
      const cmp = typeof left === "number" && typeof right === "number" ? left - right : String(left).localeCompare(String(right));
      return descending ? -cmp : cmp;
    });
  }, [rows, columns, query, sortKey, descending]);
  const pageCount = Math.max(1, Math.ceil(visible.length / pageSize));
  const currentPage = Math.min(page, pageCount - 1);
  const pageRows = visible.slice(currentPage * pageSize, (currentPage + 1) * pageSize);

  function sortBy(key: string) {
    setPage(0);
    if (sortKey === key) setDescending((value) => !value);
    else { setSortKey(key); setDescending(true); }
  }

  function rowKey(row: T, index: number) {
    const source = row as TableRow;
    const identity = source.source_row ?? source._source_row ?? source.publisher ?? source.name ?? source.Name ?? source.platform ?? source.Platform ?? "row";
    return `${String(identity)}-${currentPage}-${index}`;
  }

  function toggleDetails(key: string) {
    setExpandedRows((previous) => {
      const next = new Set(previous);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  }

  return (
    <section className="panel table-panel">
      <div className="panel-heading table-heading">
        <div><h2>{title}</h2>{description ? <p>{description}</p> : null}</div>
        <div className="table-controls"><span className="result-count">{formatNumber(visible.length, 0)} records</span><SearchBox value={query} onChange={(value) => { setQuery(value); setPage(0); }} /></div>
      </div>
      {visible.length === 0 ? <div className="table-empty">{emptyMessage}</div> : (
        <div className="table-scroll">
          <table>
            <thead><tr>{columns.map((column) => (
              <th key={column.key} scope="col" className={column.align === "right" ? "numeric" : ""} aria-sort={sortKey === column.key ? (descending ? "descending" : "ascending") : "none"}>
                <button className="sort-button" type="button" onClick={() => sortBy(column.key)}>{column.label}<ChevronDown className={sortKey === column.key && !descending ? "sort-up" : ""} size={13} aria-hidden="true" /></button>
              </th>
            ))}{expandable ? <th scope="col"><span className="sr-only">Details</span></th> : null}</tr></thead>
            <tbody>{pageRows.map((row, index) => {
              const key = rowKey(row, index);
              const open = expandedRows.has(key);
              const visibleKeys = new Set<string>(columns.map((column) => column.key));
              const details = Object.entries(row as TableRow).filter(([field]) => !visibleKeys.has(field));
              return <Fragment key={key}>
                <tr>
                  {columns.map((column) => {
                    const value = (row as TableRow)[column.key];
                    return <td key={column.key} className={column.align === "right" ? "numeric" : ""}>{column.format ? column.format(value, row) : displayValue(value)}</td>;
                  })}
                  {expandable ? <td className="details-cell"><button className="details-button" type="button" aria-expanded={open} aria-label={`${open ? "Hide" : "Show"} details for ${displayValue((row as TableRow)[columns[0]?.key ?? "id"])}`} onClick={() => toggleDetails(key)}>{open ? "Hide" : "Details"}</button></td> : null}
                </tr>
                {expandable && open ? <tr className="details-row"><td colSpan={columns.length + 1}><dl>{(details.length ? details : Object.entries(row as TableRow)).map(([field, value]) => <div key={field}><dt>{field.replaceAll("_", " ")}</dt><dd>{displayValue(value)}</dd></div>)}</dl></td></tr> : null}
              </Fragment>;
            })}</tbody>
          </table>
        </div>
      )}
      {visible.length > pageSize ? (
        <div className="table-footer"><span>Showing {currentPage * pageSize + 1}–{Math.min((currentPage + 1) * pageSize, visible.length)} of {formatNumber(visible.length, 0)}</span>
          <div className="pager"><button aria-label="Previous page" disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)}><ChevronLeft size={16} /></button><span>{currentPage + 1} / {pageCount}</span><button aria-label="Next page" disabled={currentPage >= pageCount - 1} onClick={() => setPage(currentPage + 1)}><ChevronRight size={16} /></button></div>
        </div>
      ) : null}
    </section>
  );
}
