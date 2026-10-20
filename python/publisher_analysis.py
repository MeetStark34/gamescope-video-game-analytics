"""Publisher sales, genre dominance, and hit-genre calculations."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .analytics_utils import as_number, category, rows_as_mappings


def publisher_summary(data: Any) -> list[dict[str, Any]]:
    """Summarize publisher game counts, global sales, shares, and genre breadth.

    Nonblank literal labels such as `N/A` and `Unknown` are retained as distinct
    publisher categories; this function does not infer publisher identity.
    """
    totals: dict[str, float] = defaultdict(float)
    sale_counts: dict[str, int] = defaultdict(int)
    game_counts: dict[str, int] = defaultdict(int)
    genres: dict[str, set[str]] = defaultdict(set)
    all_sales = 0.0
    for row in rows_as_mappings(data):
        publisher = category(row.get("Publisher"))
        if not publisher:
            continue
        game_counts[publisher] += 1
        genre = category(row.get("Genre"))
        if genre:
            genres[publisher].add(genre)
        sales = as_number(row.get("Global_Sales"))
        if sales is not None:
            totals[publisher] += sales
            sale_counts[publisher] += 1
            all_sales += sales
    results = [
        {"publisher": publisher, "game_count": count, "games_with_sales": sale_counts[publisher],
         "genre_count": len(genres[publisher]), "genres": sorted(genres[publisher], key=str.casefold),
         "global_sales_total": totals[publisher],
         "global_sales_share": totals[publisher] / all_sales if all_sales else None}
        for publisher, count in game_counts.items()
    ]
    return sorted(results, key=lambda item: (-item["global_sales_total"], item["publisher"].casefold()))


def top_publishers(data: Any, limit: int = 10) -> list[dict[str, Any]]:
    """Return the top publishers by summed `Global_Sales`."""
    if limit <= 0:
        return []
    return publisher_summary(data)[:limit]


def publisher_genre_dominance(data: Any, threshold: float = 0.30) -> list[dict[str, Any]]:
    """Compute publisher genre shares and flag shares strictly above threshold."""
    publisher_genre: dict[tuple[str, str], float] = defaultdict(float)
    genre_total: dict[str, float] = defaultdict(float)
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in rows_as_mappings(data):
        publisher, genre = category(row.get("Publisher")), category(row.get("Genre"))
        sales = as_number(row.get("Global_Sales"))
        if not publisher or not genre or sales is None:
            continue
        publisher_genre[(publisher, genre)] += sales
        genre_total[genre] += sales
        counts[(publisher, genre)] += 1
    result = []
    for (publisher, genre), sales in publisher_genre.items():
        total = genre_total[genre]
        share = sales / total if total else None
        result.append({"publisher": publisher, "genre": genre, "games_with_sales": counts[(publisher, genre)],
                       "publisher_genre_sales": sales, "genre_total_sales": total,
                       "genre_market_share": share,
                       "is_genre_leader": share is not None and share > threshold,
                       "leader_threshold": threshold})
    return sorted(result, key=lambda item: (-(item["genre_market_share"] or 0.0), item["publisher"].casefold(), item["genre"].casefold()))
