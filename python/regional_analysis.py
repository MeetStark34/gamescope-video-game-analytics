"""Regional sales comparison and genre preference metrics for vgsales."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .analytics_utils import as_number, category, region_fields, rows_as_mappings


def regional_sales_comparison(data: Any) -> list[dict[str, Any]]:
    """Summarize sales by source-defined region; missing values are excluded."""
    totals: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for row in rows_as_mappings(data):
        for region, sales in region_fields(row).items():
            if sales is not None:
                totals[region] += sales
                counts[region] += 1
    overall = sum(totals.values())
    return [
        {"region": region, "sales_records": counts[region], "sales_total": totals[region],
         "sales_mean": totals[region] / counts[region] if counts[region] else None,
         "share_of_reported_regional_sales": totals[region] / overall if overall else None}
        for region in totals
    ]


def regional_genre_preferences(data: Any) -> list[dict[str, Any]]:
    """Return each genre's regional mix and index against the overall mix.

    An index greater than 1 means that region contributes a larger share of
    the genre's sales than it contributes to all reported regional sales.
    """
    genre_region: dict[tuple[str, str], float] = defaultdict(float)
    region_total: dict[str, float] = defaultdict(float)
    genres: set[str] = set()
    for row in rows_as_mappings(data):
        genre = category(row.get("Genre"))
        if not genre:
            continue
        genres.add(genre)
        for region, sales in region_fields(row).items():
            if sales is not None:
                genre_region[(genre, region)] += sales
                region_total[region] += sales
    overall_total = sum(region_total.values())
    output = []
    for genre in sorted(genres, key=str.casefold):
        genre_total = sum(genre_region[(genre, region)] for region in region_total)
        for region in region_total:
            sales = genre_region[(genre, region)]
            genre_share = sales / genre_total if genre_total else None
            baseline = region_total[region] / overall_total if overall_total else None
            output.append({
                "genre": genre, "region": region, "regional_sales": sales,
                "genre_region_share": genre_share, "overall_region_share": baseline,
                "affinity_index": genre_share / baseline if genre_share is not None and baseline else None,
                "genre_sales_total_all_regions": genre_total,
            })
    return output
