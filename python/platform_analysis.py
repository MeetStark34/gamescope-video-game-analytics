"""Platform counts, sales totals, and annual evolution."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .analytics_utils import as_number, as_year, category, rows_as_mappings


def platform_game_counts(data: Any) -> list[dict[str, Any]]:
    """Count listed game records by platform."""
    groups: dict[str, int] = defaultdict(int)
    for row in rows_as_mappings(data):
        platform = category(row.get("Platform"))
        if platform:
            groups[platform] += 1
    return [{"platform": platform, "game_count": count} for platform, count in sorted(groups.items(), key=lambda item: (-item[1], item[0].casefold()))]


def platform_global_sales(data: Any) -> list[dict[str, Any]]:
    """Sum valid global sales by platform and report sample counts."""
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows_as_mappings(data):
        platform, sales = category(row.get("Platform")), as_number(row.get("Global_Sales"))
        if platform and sales is not None:
            groups[platform].append(sales)
    total = sum(sum(values) for values in groups.values())
    result = []
    for platform, values in groups.items():
        sales = sum(values)
        result.append({"platform": platform, "games_with_sales": len(values), "global_sales_total": sales,
                       "global_sales_mean": sales / len(values), "global_sales_share": sales / total if total else None})
    return sorted(result, key=lambda row: (-row["global_sales_total"], row["platform"].casefold()))


def platform_evolution(data: Any) -> list[dict[str, Any]]:
    """Return one record per platform/year with record count and global sales."""
    counts: dict[tuple[str, int], int] = defaultdict(int)
    sales: dict[tuple[str, int], list[float]] = defaultdict(list)
    for row in rows_as_mappings(data):
        platform, year = category(row.get("Platform")), as_year(row.get("Year"))
        if not platform or year is None:
            continue
        key = (platform, year)
        counts[key] += 1
        value = as_number(row.get("Global_Sales"))
        if value is not None:
            sales[key].append(value)
    return [
        {"platform": platform, "year": year, "games_released": count,
         "games_with_sales": len(sales.get((platform, year), [])),
         "global_sales_total": sum(sales[(platform, year)]) if sales.get((platform, year)) else None}
        for (platform, year), count in sorted(counts.items(), key=lambda item: (item[0][0].casefold(), item[0][1]))
    ]
