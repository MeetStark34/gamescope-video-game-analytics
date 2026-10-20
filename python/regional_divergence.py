"""Game-level, genre-level, and temporal regional preference divergence."""

from __future__ import annotations

import itertools
import math
from collections import defaultdict
from typing import Any

from .analytics_utils import as_number, as_year, category, region_fields, rows_as_mappings


def _distribution_distance(left: dict[str, float], right: dict[str, float], regions: list[str]) -> float:
    """Total variation distance, bounded [0, 1], for two region distributions."""
    return 0.5 * sum(abs(left.get(region, 0.0) - right.get(region, 0.0)) for region in regions)


def regional_divergence_by_game(data: Any) -> list[dict[str, Any]]:
    """Compare a game's regional sales mix with the full dataset's regional mix.

    The divergence score is total variation distance (half the L1 distance).
    Rows with any missing region or zero total regional sales are ineligible.
    """
    rows = rows_as_mappings(data)
    regions = list(region_fields(rows[0]).keys()) if rows else []
    baseline_sales = {region: 0.0 for region in regions}
    for row in rows:
        values = region_fields(row)
        if all(values.get(region) is not None for region in regions):
            for region in regions:
                baseline_sales[region] += values[region] or 0.0
    baseline_total = sum(baseline_sales.values())
    baseline = {region: baseline_sales[region] / baseline_total for region in regions} if baseline_total else {}
    result = []
    for row in rows:
        values = region_fields(row)
        if not regions or any(values.get(region) is None for region in regions):
            continue
        total = sum(values[region] or 0.0 for region in regions)
        if total <= 0:
            continue
        proportions = {region: (values[region] or 0.0) / total for region in regions}
        result.append({
            "source_row": row.get("_source_row"), "name": category(row.get("Name")),
            "platform": category(row.get("Platform")), "year": as_year(row.get("Year")),
            "genre": category(row.get("Genre")), "global_sales": as_number(row.get("Global_Sales")),
            "regional_sales_total": total, "regional_divergence_score": _distribution_distance(proportions, baseline, regions),
            "regional_proportions": proportions, "baseline_regional_proportions": baseline,
            "dominant_region": min(regions, key=lambda region: (-proportions[region], region)),
            "dominant_region_share": max(proportions.values()),
            "cultural_specificity_score": 100 * (max(proportions.values()) - max(
                (share for region, share in proportions.items()
                 if region != min(regions, key=lambda key: (-proportions[key], key))), default=0.0
            )),
            "passes_cultural_outlier_screen": (
                max(proportions.values()) > 0.50
                and all(share < 0.10 for region, share in proportions.items()
                        if region != min(regions, key=lambda key: (-proportions[key], key)))
            ),
        })
    return sorted(result, key=lambda item: (-item["regional_divergence_score"], item["name"] or "", item["platform"] or ""))


def regional_favorites_by_year(data: Any) -> list[dict[str, Any]]:
    """Find each region's favorite genre per year by summed regional sales.

    Ties are resolved alphabetically by genre. Only rows with a valid year,
    genre, and value for that region contribute.
    """
    totals: dict[tuple[int, str, str], float] = defaultdict(float)
    regions: set[str] = set()
    for row in rows_as_mappings(data):
        year, genre = as_year(row.get("Year")), category(row.get("Genre"))
        if year is None or not genre:
            continue
        for region, sales in region_fields(row).items():
            regions.add(region)
            if sales is not None:
                totals[(year, region, genre)] += sales
    years = sorted({key[0] for key in totals})
    result = []
    for year in years:
        for region in sorted(regions):
            candidates = [(genre, sales) for (candidate_year, candidate_region, genre), sales in totals.items()
                          if candidate_year == year and candidate_region == region]
            if not candidates:
                continue
            genre, sales = min(candidates, key=lambda item: (-item[1], item[0].casefold()))
            result.append({"year": year, "region": region, "favorite_genre": genre,
                           "favorite_genre_sales": sales, "genres_with_sales": len(candidates)})
    return result


def regional_preference_stability(data: Any) -> list[dict[str, Any]]:
    """Score adjacent observed-year favorite-genre consistency per region.

    The stability index is the fraction of adjacent observed-year pairs with
    the same favorite genre. Years with no valid regional favorite are omitted;
    observed years need not be calendar-consecutive.
    """
    favorites = regional_favorites_by_year(data)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in favorites:
        grouped[item["region"]].append(item)
    result = []
    for region, items in grouped.items():
        items.sort(key=lambda item: item["year"])
        pairs = list(zip(items, items[1:]))
        stable_pairs = sum(left["favorite_genre"] == right["favorite_genre"] for left, right in pairs)
        result.append({"region": region, "observed_years": len(items), "adjacent_observed_year_pairs": len(pairs),
                       "same_favorite_pairs": stable_pairs,
                       "preference_stability_index": stable_pairs / len(pairs) if pairs else None,
                       "definition": "same favorite genre across adjacent observed years"})
    return sorted(result, key=lambda item: item["region"])


def regional_preference_divergence_by_year(data: Any) -> list[dict[str, Any]]:
    """Quantify yearly pairwise regional genre-mix distance using TV distance."""
    totals: dict[tuple[int, str, str], float] = defaultdict(float)
    regions: set[str] = set()
    for row in rows_as_mappings(data):
        year, genre = as_year(row.get("Year")), category(row.get("Genre"))
        if year is None or not genre:
            continue
        for region, sales in region_fields(row).items():
            regions.add(region)
            if sales is not None:
                totals[(year, region, genre)] += sales
    result = []
    years = sorted({key[0] for key in totals})
    region_list = sorted(regions)
    for year in years:
        distributions: dict[str, dict[str, float]] = {}
        for region in region_list:
            values = {genre: value for (y, r, genre), value in totals.items() if y == year and r == region}
            total = sum(values.values())
            if total:
                distributions[region] = {genre: value / total for genre, value in values.items()}
        distances = []
        for left_region, right_region in itertools.combinations(sorted(distributions), 2):
            genres = sorted(set(distributions[left_region]) | set(distributions[right_region]))
            distance = _distribution_distance(distributions[left_region], distributions[right_region], genres)
            distances.append({"region_a": left_region, "region_b": right_region, "total_variation_distance": distance})
        result.append({"year": year, "pairwise_region_distances": distances,
                       "mean_pairwise_divergence": sum(x["total_variation_distance"] for x in distances) / len(distances) if distances else None,
                       "regions_compared": len(distributions)})
    return result


def cultural_outliers(data: Any) -> list[dict[str, Any]]:
    """Flag games with >50% in one region and <10% in each other region.

    The custom cultural-specificity score is the dominant-region share minus
    the largest other-region share, expressed on a 0-100 scale.
    """
    result = []
    for item in regional_divergence_by_game(data):
        if item["passes_cultural_outlier_screen"]:
            result.append(item)
    return sorted(result, key=lambda item: (-item["cultural_specificity_score"], item["name"] or ""))


def genre_region_affinity(data: Any) -> list[dict[str, Any]]:
    """Calculate continuous genre-region affinity and relative index labels.

    Affinity is (genre sales in region / all regional sales for that genre)
    divided by (all genre sales in region / all regional sales). Values above
    1 are over-indexed; values below 1 are under-indexed. The exact baseline
    is 1, so no arbitrary threshold band is applied.
    """
    genre_region: dict[tuple[str, str], float] = defaultdict(float)
    region_totals: dict[str, float] = defaultdict(float)
    genres: set[str] = set()
    regions: set[str] = set()
    for row in rows_as_mappings(data):
        genre = category(row.get("Genre"))
        if not genre:
            continue
        genres.add(genre)
        for region, value in region_fields(row).items():
            regions.add(region)
            if value is not None:
                genre_region[(genre, region)] += value
                region_totals[region] += value
    overall_total = sum(region_totals.values())
    result = []
    for genre in sorted(genres, key=str.casefold):
        genre_total = sum(genre_region[(genre, region)] for region in regions)
        for region in sorted(regions):
            sales = genre_region[(genre, region)]
            genre_share = sales / genre_total if genre_total else None
            regional_baseline = region_totals[region] / overall_total if overall_total else None
            index = genre_share / regional_baseline if genre_share is not None and regional_baseline else None
            is_baseline = index is not None and math.isclose(index, 1.0, rel_tol=1e-12, abs_tol=1e-12)
            result.append({
                "genre": genre, "region": region, "regional_sales": sales,
                "genre_region_share": genre_share,
                "overall_region_sales_share": regional_baseline,
                "affinity_index": index,
                "index_class": "at_baseline" if is_baseline else
                               "over_indexed" if index is not None and index > 1 else
                               "under_indexed" if index is not None and index < 1 else
                               "unavailable",
            })
    return result


def regional_preference_changes(data: Any) -> list[dict[str, Any]]:
    """Return regional genre shares and deltas versus the prior observed year.

    This emits a long table by region/year/genre. No gaps are interpolated;
    changes compare consecutive available observations, which may skip years.
    """
    totals: dict[tuple[int, str, str], float] = defaultdict(float)
    regions: set[str] = set()
    for row in rows_as_mappings(data):
        year, genre = as_year(row.get("Year")), category(row.get("Genre"))
        if year is None or not genre:
            continue
        for region, value in region_fields(row).items():
            regions.add(region)
            if value is not None:
                totals[(year, region, genre)] += value
    years = sorted({key[0] for key in totals})
    result = []
    for region in sorted(regions):
        prior_shares: dict[str, float] | None = None
        prior_year: int | None = None
        for year in years:
            genre_sales = {genre: value for (y, r, genre), value in totals.items()
                           if y == year and r == region}
            total = sum(genre_sales.values())
            if not total:
                continue
            shares = {genre: value / total for genre, value in genre_sales.items()}
            favorite = min(shares, key=lambda genre: (-shares[genre], genre.casefold()))
            for genre in sorted(set(shares) | set(prior_shares or {}), key=str.casefold):
                current = shares.get(genre, 0.0)
                previous = prior_shares.get(genre, 0.0) if prior_shares is not None else None
                result.append({
                    "region": region, "year": year, "genre": genre,
                    "regional_genre_sales": genre_sales.get(genre, 0.0),
                    "regional_genre_share": current,
                    "previous_observed_year": prior_year,
                    "previous_observed_genre_share": previous,
                    "share_change": current - previous if previous is not None else None,
                    "favorite_genre": favorite,
                    "favorite_changed": (favorite != min(prior_shares, key=lambda g: (-prior_shares[g], g.casefold())))
                                        if prior_shares else None,
                })
            prior_shares, prior_year = shares, year
    return result
