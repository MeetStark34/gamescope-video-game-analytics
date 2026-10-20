"""Publisher genre-market shares and a documented Market Power Index.

The index is a descriptive, project-defined composite. It is not a causal
measure or an established industry standard; see ``reports/advanced-analysis.md``.
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Any

from .analytics_utils import as_number, category, rows_as_mappings


COMPONENTS = (
    "sales_share",
    "genre_leadership_coverage",
    "genre_diversity_score",
    "regional_consistency_score",
    "hit_rate",
)
REGION_COLUMNS = ("NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales")
MAX_FOUR_REGION_POPULATION_STD = math.sqrt(3.0) / 4.0


def publisher_genre_market_shares(data: Any, leader_threshold: float = 0.30) -> list[dict[str, Any]]:
    """Return publisher sales share within every genre and >30% leader flags.

    Sales denominators use all rows with valid publisher, genre, and
    ``Global_Sales``. Repeated records are retained and represent source rows.
    """
    totals: dict[str, float] = defaultdict(float)
    publisher_totals: dict[tuple[str, str], float] = defaultdict(float)
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in rows_as_mappings(data):
        publisher, genre = category(row.get("Publisher")), category(row.get("Genre"))
        sales = as_number(row.get("Global_Sales"))
        if not genre or sales is None:
            continue
        totals[genre] += sales
        if not publisher:
            continue
        publisher_totals[(publisher, genre)] += sales
        counts[(publisher, genre)] += 1
    records = []
    for (publisher, genre), sales in publisher_totals.items():
        denominator = totals[genre]
        share = sales / denominator if denominator else None
        records.append({
            "publisher": publisher,
            "genre": genre,
            "publisher_genre_sales": sales,
            "genre_total_sales": denominator,
            "genre_market_share": share,
            "games_with_sales": counts[(publisher, genre)],
            "leader_threshold": leader_threshold,
            "is_genre_leader": share is not None and share > leader_threshold,
        })
    return sorted(records, key=lambda item: (
        item["genre"].casefold(), -(item["genre_market_share"] or 0.0), item["publisher"].casefold()
    ))


def _archetype(leader_count: int, genre_count: int, total_genres: int) -> str:
    """Classify portfolios using explicit breadth and leadership cutoffs."""
    breadth = genre_count / total_genres if total_genres else 0.0
    broad_cutoff = 0.5  # at least half of observed genres
    if leader_count >= 2 and breadth >= broad_cutoff:
        return "Diversified Genre Leader"
    if leader_count >= 1 and genre_count <= 2:
        return "Genre Specialist"
    if breadth >= broad_cutoff:
        return "Diversified Publisher"
    if leader_count >= 1:
        return "Genre Leader"
    return "No 30% Genre Leadership Flag"


def market_power_index(data: Any, leader_threshold: float = 0.30) -> list[dict[str, Any]]:
    """Calculate ranked publisher components and the equal-weight 0–100 MPI.

    Each component is normalized to [0, 1]. The final score is their
    arithmetic mean times 100; available components are averaged if a
    component cannot be computed and the available-component count is kept.
    Equal weighting is a transparent neutral baseline: the specification gives
    no evidence for privileging one dimension, and all component scales are
    normalized. Component scores are returned so alternative weights can be
    evaluated without recomputing the underlying measures.

    ``sales_share`` is the publisher's share of all valid global sales
    attributed to nonblank publisher labels. Genre leadership coverage is the
    fraction of represented genres where publisher share is strictly greater
    than ``leader_threshold``.
    Genre diversity is portfolio genres divided by all represented genres.
    Regional consistency is one minus the normalized population standard
    deviation of four regional sales proportions (all four columns required
    per record). Hit rate is the fraction of publisher records above their
    genre's median ``Global_Sales``. All records are retained as records;
    duplicate game editions are not deduplicated.
    """
    rows = rows_as_mappings(data)
    by_genre: dict[str, list[float]] = defaultdict(list)
    publisher_sales: dict[str, float] = defaultdict(float)
    publisher_valid_sales_count: dict[str, int] = defaultdict(int)
    publisher_rows: dict[str, int] = defaultdict(int)
    publisher_genres: dict[str, set[str]] = defaultdict(set)
    complete_region_sales: dict[str, dict[str, float]] = defaultdict(lambda: {key: 0.0 for key in REGION_COLUMNS})
    complete_region_counts: dict[str, int] = defaultdict(int)
    incomplete_region_counts: dict[str, int] = defaultdict(int)
    hit_pairs: dict[str, list[tuple[str, float]]] = defaultdict(list)
    total_sales = 0.0
    all_genres: set[str] = set()

    for row in rows:
        publisher, genre = category(row.get("Publisher")), category(row.get("Genre"))
        sales = as_number(row.get("Global_Sales"))
        if genre:
            all_genres.add(genre)
            if sales is not None:
                by_genre[genre].append(sales)
        if not publisher:
            continue
        publisher_rows[publisher] += 1
        if genre:
            publisher_genres[publisher].add(genre)
        if sales is not None:
            publisher_sales[publisher] += sales
            publisher_valid_sales_count[publisher] += 1
            total_sales += sales
            if genre:
                hit_pairs[publisher].append((genre, sales))
        region_values = [as_number(row.get(field)) for field in REGION_COLUMNS]
        if all(value is not None for value in region_values):
            complete_region_counts[publisher] += 1
            for field, value in zip(REGION_COLUMNS, region_values):
                complete_region_sales[publisher][field] += value or 0.0
        else:
            incomplete_region_counts[publisher] += 1

    genre_medians = {genre: statistics.median(values) for genre, values in by_genre.items() if values}
    genre_shares = publisher_genre_market_shares(rows, leader_threshold)
    shares_by_publisher: dict[str, list[dict[str, Any]]] = defaultdict(list)
    leadership: dict[str, set[str]] = defaultdict(set)
    for item in genre_shares:
        shares_by_publisher[item["publisher"]].append(item)
        if item["is_genre_leader"]:
            leadership[item["publisher"]].add(item["genre"])

    total_genres = len(all_genres)
    output = []
    for publisher, record_count in publisher_rows.items():
        hits = [(genre, sales) for genre, sales in hit_pairs[publisher] if genre in genre_medians]
        hit_rate = sum(sales > genre_medians[genre] for genre, sales in hits) / len(hits) if hits else None
        genre_count = len(publisher_genres[publisher])
        diversity = genre_count / total_genres if total_genres else None
        region_counts = complete_region_sales[publisher]
        region_total = sum(region_counts.values())
        if complete_region_counts[publisher] and region_total > 0:
            proportions = [region_counts[key] / region_total for key in REGION_COLUMNS]
            region_std = statistics.pstdev(proportions)
            consistency = max(0.0, min(1.0, 1 - region_std / MAX_FOUR_REGION_POPULATION_STD))
        else:
            proportions, consistency = [], None
        sales_share = publisher_sales[publisher] / total_sales if total_sales else None
        leadership_coverage = len(leadership[publisher]) / total_genres if total_genres else None
        component_values = {
            "sales_share": sales_share,
            "genre_leadership_coverage": leadership_coverage,
            "genre_diversity_score": diversity,
            "regional_consistency_score": consistency,
            "hit_rate": hit_rate,
        }
        available = [value for value in component_values.values() if value is not None]
        score = (100 * sum(available) / len(available)) if available else None
        output.append({
            "publisher": publisher,
            "game_record_count": record_count,
            "games_with_global_sales": publisher_valid_sales_count[publisher],
            "games_in_hit_rate_denominator": len(hits),
            "genre_count": genre_count,
            "total_genres_in_source": total_genres,
            "genre_leader_count": len(leadership[publisher]),
            "genre_leaders": sorted(leadership[publisher], key=str.casefold),
            "genre_market_shares": [
                {"genre": item["genre"], "share": item["genre_market_share"], "is_leader": item["is_genre_leader"]}
                for item in shares_by_publisher[publisher]
            ],
            "regional_complete_records": complete_region_counts[publisher],
            "regional_incomplete_records": incomplete_region_counts[publisher],
            "regional_sales_proportions": dict(zip(REGION_COLUMNS, proportions)) if proportions else None,
            **component_values,
            "available_component_count": len(available),
            "market_power_index": score,
            "formula_version": "mpi_equal_weight_arithmetic_v2",
            "publisher_archetype": _archetype(len(leadership[publisher]), genre_count, total_genres),
        })
    output.sort(key=lambda item: (
        item["market_power_index"] is None,
        -(item["market_power_index"] or 0.0),
        item["publisher"].casefold(),
    ))
    for rank, item in enumerate(output, 1):
        item["market_power_rank"] = rank if item["market_power_index"] is not None else None
    return output
