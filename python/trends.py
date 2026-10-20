"""Annual release and sales trends for `vgsales.csv`."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .analytics_utils import as_number, as_year, rows_as_mappings


def games_released_per_year(data: Any) -> list[dict[str, Any]]:
    """Count records by valid integer year; invalid/missing years are skipped."""
    counts: dict[int, int] = defaultdict(int)
    for row in rows_as_mappings(data):
        year = as_year(row.get("Year"))
        if year is not None:
            counts[year] += 1
    return [{"year": year, "games_released": counts[year]} for year in sorted(counts)]


def global_sales_by_year(data: Any) -> list[dict[str, Any]]:
    """Aggregate valid `Global_Sales` records by valid year."""
    values: dict[int, list[float]] = defaultdict(list)
    for row in rows_as_mappings(data):
        year, sales = as_year(row.get("Year")), as_number(row.get("Global_Sales"))
        if year is not None and sales is not None:
            values[year].append(sales)
    return [
        {"year": year, "games_with_year_and_sales": len(sales), "global_sales_total": sum(sales), "global_sales_mean": sum(sales) / len(sales)}
        for year, sales in sorted(values.items()) if sales
    ]


def annual_trends(data: Any) -> list[dict[str, Any]]:
    """Join release counts and sales summaries by year using in-memory results."""
    counts = {row["year"]: row["games_released"] for row in games_released_per_year(data)}
    sales = {row["year"]: row for row in global_sales_by_year(data)}
    return [
        {"year": year, "games_released": counts.get(year, 0),
         "games_with_year_and_sales": sales.get(year, {}).get("games_with_year_and_sales", 0),
         "global_sales_total": sales.get(year, {}).get("global_sales_total"),
         "global_sales_mean": sales.get(year, {}).get("global_sales_mean")}
        for year in sorted(set(counts) | set(sales))
    ]
