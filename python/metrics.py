"""Descriptive statistics and ranked game metrics for the primary dataset."""

from __future__ import annotations

import statistics
from typing import Any, Mapping

from .analytics_utils import as_number, category, rows_as_mappings


NUMERIC_FIELDS = ("Rank", "Year", "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales")


def descriptive_statistics(data: Any, fields: tuple[str, ...] = NUMERIC_FIELDS) -> dict[str, dict[str, Any]]:
    """Summarize numeric fields; empty and invalid values are excluded per field.

    Args:
        data: Iterable of mappings or a pandas DataFrame.
        fields: Numeric columns to summarize.

    Returns:
        A mapping from field name to count, missing/invalid count, min/max,
        mean, median, population standard deviation, and quartiles.
    """
    rows = rows_as_mappings(data)
    result: dict[str, dict[str, Any]] = {}
    for field in fields:
        values = [number for row in rows if (number := as_number(row.get(field))) is not None]
        if not values:
            result[field] = {"count": 0, "missing_or_invalid": len(rows), "min": None, "q1": None, "median": None, "q3": None, "max": None, "mean": None, "std_population": None}
            continue
        ordered = sorted(values)
        quartiles = statistics.quantiles(ordered, n=4, method="inclusive") if len(ordered) > 1 else [ordered[0], ordered[0], ordered[0]]
        result[field] = {
            "count": len(values), "missing_or_invalid": len(rows) - len(values),
            "min": ordered[0], "q1": quartiles[0], "median": statistics.median(ordered),
            "q3": quartiles[2], "max": ordered[-1], "mean": statistics.fmean(values),
            "std_population": statistics.pstdev(values) if len(values) > 1 else 0.0,
        }
    return result


def top_games(data: Any, limit: int = 10) -> list[dict[str, Any]]:
    """Return games ranked by `Global_Sales` without changing source rows."""
    if limit <= 0:
        return []
    ranked = []
    for row in rows_as_mappings(data):
        sales = as_number(row.get("Global_Sales"))
        if sales is None:
            continue
        item = {
            "name": category(row.get("Name")), "platform": category(row.get("Platform")),
            "year": row.get("Year"), "genre": category(row.get("Genre")),
            "publisher": category(row.get("Publisher")), "global_sales": sales,
        }
        ranked.append(item)
    ranked.sort(key=lambda item: (-item["global_sales"], item["name"] or "", item["platform"] or ""))
    for rank, row in enumerate(ranked[:limit], start=1):
        row["sales_rank"] = rank
    return ranked[:limit]
