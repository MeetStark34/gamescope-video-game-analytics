"""Genre frequency and sales summaries."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .analytics_utils import as_number, category, rows_as_mappings


def genre_frequency(data: Any) -> list[dict[str, Any]]:
    """Count rows by genre, retaining source labels and excluding blank labels."""
    counts: dict[str, int] = defaultdict(int)
    for row in rows_as_mappings(data):
        genre = category(row.get("Genre"))
        if genre:
            counts[genre] += 1
    return [{"genre": genre, "game_count": count} for genre, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold()))]


def genre_global_sales(data: Any) -> list[dict[str, Any]]:
    """Aggregate valid global sales by genre with explicit sample sizes."""
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows_as_mappings(data):
        genre, sales = category(row.get("Genre")), as_number(row.get("Global_Sales"))
        if genre and sales is not None:
            groups[genre].append(sales)
    total = sum(sum(values) for values in groups.values())
    result = []
    for genre, values in groups.items():
        sales = sum(values)
        result.append({"genre": genre, "games_with_sales": len(values), "global_sales_total": sales,
                       "global_sales_mean": sales / len(values), "global_sales_share": sales / total if total else None})
    return sorted(result, key=lambda row: (-row["global_sales_total"], row["genre"].casefold()))
