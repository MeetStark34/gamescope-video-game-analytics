"""Supplemental, vgchartz-only analyses for ratings, companies, and dates.

No functions in this module merge the 2024 data with ``vgsales.csv``. All
results expose their eligible sample counts because both critic-score and
sales coverage are incomplete in this source.
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from datetime import date
from typing import Any

from .analytics_utils import as_number, category, rows_as_mappings


def _parse_iso_date(value: Any) -> date | None:
    """Parse only strict ISO calendar dates, preserving missing/imprecise as unavailable."""
    text = category(value)
    if not text:
        return None
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.isoformat() == text else None


def _rank(values: list[float]) -> list[float]:
    """Return average ranks for ties, with ranks starting at one."""
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        stop = start + 1
        while stop < len(order) and values[order[stop]] == values[order[start]]:
            stop += 1
        average_rank = ((start + 1) + stop) / 2
        for position in order[start:stop]:
            ranks[position] = average_rank
        start = stop
    return ranks


def _correlation(left: list[float], right: list[float]) -> float | None:
    """Pearson correlation with constant/undersized input guarded as null."""
    if len(left) < 2 or len(left) != len(right):
        return None
    mean_left, mean_right = statistics.fmean(left), statistics.fmean(right)
    covariance = sum((x - mean_left) * (y - mean_right) for x, y in zip(left, right))
    variance_left = sum((x - mean_left) ** 2 for x in left)
    variance_right = sum((y - mean_right) ** 2 for y in right)
    denominator = math.sqrt(variance_left * variance_right)
    return covariance / denominator if denominator else None


def critic_score_sales_association(data: Any) -> dict[str, Any]:
    """Describe critic-score/global-sales association, not a causal effect.

    Eligible pairs have a numeric critic score in [0, 10] and nonnegative
    ``total_sales``. Reports Pearson and Spearman coefficients, plus Pearson
    for log1p sales to show sensitivity to the sales distribution's scale.
    The equal-width 1-point rating bands are descriptive, not rating tiers.
    """
    rows = rows_as_mappings(data)
    scores: list[float] = []
    sales: list[float] = []
    missing_score = missing_sales = invalid_score = invalid_sales = negative_sales = 0
    unparseable_score = unparseable_sales = 0
    bands: dict[int, list[float]] = defaultdict(list)
    points: list[dict[str, Any]] = []
    for row in rows:
        score, amount = as_number(row.get("critic_score")), as_number(row.get("total_sales"))
        raw_score, raw_sales = category(row.get("critic_score")), category(row.get("total_sales"))
        if raw_score is None:
            missing_score += 1
        elif score is None:
            unparseable_score += 1
        elif score < 0 or score > 10:
            invalid_score += 1
        if raw_sales is None:
            missing_sales += 1
        elif amount is None:
            unparseable_sales += 1
        elif amount < 0:
            negative_sales += 1
            invalid_sales += 1
        if score is not None and not 0 <= score <= 10:
            continue
        if amount is not None and amount < 0:
            continue
        if score is None or amount is None:
            continue
        scores.append(score)
        sales.append(amount)
        band = min(int(score), 9)  # score 10 belongs to the final [9, 10] interval
        bands[band].append(amount)
        points.append({
            "title": category(row.get("title")), "console": category(row.get("console")),
            "critic_score": score, "total_sales": amount,
            "release_date": category(row.get("release_date")),
        })
    rank_corr = _correlation(_rank(scores), _rank(sales))
    band_summary = []
    for band in range(10):
        values = bands.get(band, [])
        band_summary.append({
            "score_band": f"[{band}, {band + 1}{']' if band == 9 else ')'}",
            "score_lower": band, "score_upper": band + 1,
            "upper_inclusive": band == 9, "record_count": len(values),
            "mean_total_sales": statistics.fmean(values) if values else None,
            "median_total_sales": statistics.median(values) if values else None,
        })
    n = len(scores)
    return {
        "source_dataset": "vgchartz-2024.csv",
        "eligible_pair_count": n,
        "source_row_count": len(rows),
        "eligible_pair_percent": (100 * n / len(rows)) if rows else None,
        "critic_score_valid_range": [0, 10],
        "critic_score_sales_pearson_r": _correlation(scores, sales),
        "critic_score_sales_spearman_rho": rank_corr,
        "critic_score_log1p_sales_pearson_r": _correlation(scores, [math.log1p(value) for value in sales]),
        "missing_critic_score_count": missing_score,
        "missing_total_sales_count": missing_sales,
        "unparseable_critic_score_count": unparseable_score,
        "unparseable_total_sales_count": unparseable_sales,
        "invalid_critic_score_count": invalid_score,
        "invalid_total_sales_count": invalid_sales,
        "negative_total_sales_count": negative_sales,
        "critic_score_bands": band_summary,
        "paired_points": points,
        "interpretation": "Association only; incomplete coverage, selection, and confounding prevent causal conclusions.",
    }


def publisher_performance(data: Any) -> list[dict[str, Any]]:
    """Summarize vgchartz publisher sales, ratings, catalogue and coverage."""
    groups: dict[str, dict[str, Any]] = defaultdict(lambda: {"records": 0, "sales": [], "scores": [], "developers": set(), "consoles": set(), "genres": set()})
    for row in rows_as_mappings(data):
        publisher = category(row.get("publisher"))
        if not publisher:
            continue
        item = groups[publisher]
        item["records"] += 1
        sales, score = as_number(row.get("total_sales")), as_number(row.get("critic_score"))
        if sales is not None and sales >= 0:
            item["sales"].append(sales)
        if score is not None and 0 <= score <= 10:
            item["scores"].append(score)
        for field, dest in (("developer", "developers"), ("console", "consoles"), ("genre", "genres")):
            value = category(row.get(field))
            if value:
                item[dest].add(value)
    result = []
    all_sales = sum(sum(item["sales"]) for item in groups.values())
    for publisher, item in groups.items():
        total = sum(item["sales"])
        result.append({
            "publisher": publisher, "release_records": item["records"],
            "records_with_sales": len(item["sales"]), "records_with_critic_score": len(item["scores"]),
            "total_sales": total, "sales_share": total / all_sales if all_sales else None,
            "mean_sales": statistics.fmean(item["sales"]) if item["sales"] else None,
            "median_sales": statistics.median(item["sales"]) if item["sales"] else None,
            "mean_critic_score": statistics.fmean(item["scores"]) if item["scores"] else None,
            "median_critic_score": statistics.median(item["scores"]) if item["scores"] else None,
            "developer_count": len(item["developers"]), "console_count": len(item["consoles"]),
            "genre_count": len(item["genres"]),
        })
    return sorted(result, key=lambda item: (-item["total_sales"], item["publisher"].casefold()))


def developer_performance(data: Any) -> list[dict[str, Any]]:
    """Summarize sales and critic scores by literal developer label.

    Placeholder labels such as ``Unknown`` remain distinct from empty values;
    this module does not infer company aliases or normalize identities.
    """
    groups: dict[str, dict[str, Any]] = defaultdict(lambda: {"records": 0, "sales": [], "scores": [], "publishers": set(), "consoles": set(), "genres": set()})
    for row in rows_as_mappings(data):
        developer = category(row.get("developer"))
        if not developer:
            continue
        item = groups[developer]
        item["records"] += 1
        sales, score = as_number(row.get("total_sales")), as_number(row.get("critic_score"))
        if sales is not None and sales >= 0:
            item["sales"].append(sales)
        if score is not None and 0 <= score <= 10:
            item["scores"].append(score)
        for field, dest in (("publisher", "publishers"), ("console", "consoles"), ("genre", "genres")):
            value = category(row.get(field))
            if value:
                item[dest].add(value)
    result = []
    for developer, item in groups.items():
        total = sum(item["sales"])
        result.append({
            "developer": developer, "release_records": item["records"],
            "records_with_sales": len(item["sales"]), "records_with_critic_score": len(item["scores"]),
            "total_sales": total, "mean_sales": statistics.fmean(item["sales"]) if item["sales"] else None,
            "median_sales": statistics.median(item["sales"]) if item["sales"] else None,
            "mean_critic_score": statistics.fmean(item["scores"]) if item["scores"] else None,
            "median_critic_score": statistics.median(item["scores"]) if item["scores"] else None,
            "publisher_count": len(item["publishers"]), "console_count": len(item["consoles"]),
            "genre_count": len(item["genres"]),
        })
    return sorted(result, key=lambda item: (-item["total_sales"], item["developer"].casefold()))


def publisher_developer_performance(data: Any) -> list[dict[str, Any]]:
    """Aggregate supplemental sales/ratings by literal publisher/developer pair."""
    groups: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {"records": 0, "sales": [], "scores": []})
    for row in rows_as_mappings(data):
        publisher, developer = category(row.get("publisher")), category(row.get("developer"))
        if not publisher or not developer:
            continue
        item = groups[(publisher, developer)]
        item["records"] += 1
        sales, score = as_number(row.get("total_sales")), as_number(row.get("critic_score"))
        if sales is not None and sales >= 0:
            item["sales"].append(sales)
        if score is not None and 0 <= score <= 10:
            item["scores"].append(score)
    result = []
    for (publisher, developer), item in groups.items():
        result.append({
            "publisher": publisher, "developer": developer, "release_records": item["records"],
            "records_with_sales": len(item["sales"]), "records_with_critic_score": len(item["scores"]),
            "total_sales": sum(item["sales"]),
            "mean_critic_score": statistics.fmean(item["scores"]) if item["scores"] else None,
        })
    return sorted(result, key=lambda item: (-item["total_sales"], item["publisher"].casefold(), item["developer"].casefold()))


def platform_evolution(data: Any) -> dict[str, list[dict[str, Any]]]:
    """Return console-by-release-year activity and console lifecycle summaries."""
    groups: dict[tuple[str, int], dict[str, Any]] = defaultdict(lambda: {"records": 0, "sales": []})
    console_years: dict[str, set[int]] = defaultdict(set)
    for row in rows_as_mappings(data):
        console = category(row.get("console"))
        release = _parse_iso_date(row.get("release_date"))
        if not console or not release:
            continue
        key = (console, release.year)
        groups[key]["records"] += 1
        console_years[console].add(release.year)
        sales = as_number(row.get("total_sales"))
        if sales is not None and sales >= 0:
            groups[key]["sales"].append(sales)
    annual = []
    yearly_sales: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for (console, year), item in sorted(groups.items()):
        total = sum(item["sales"])
        annual.append({"console": console, "year": year, "release_records": item["records"],
                       "records_with_sales": len(item["sales"]), "total_sales": total if item["sales"] else None})
        if item["sales"]:
            yearly_sales[console].append((year, total))
    lifecycle = []
    for console, years in console_years.items():
        series = yearly_sales.get(console, [])
        peak = max(series, key=lambda pair: pair[1]) if series else (None, None)
        lifecycle.append({"console": console, "first_observed_release_year": min(years),
                          "last_observed_release_year": max(years), "observed_active_year_count": len(years),
                          "peak_sales_year": peak[0], "peak_annual_sales": peak[1]})
    lifecycle.sort(key=lambda item: (item["first_observed_release_year"], item["console"].casefold()))
    return {"console_year": annual, "console_lifecycle": lifecycle}


def release_date_trends(data: Any) -> dict[str, Any]:
    """Summarize year, quarter, month and weekday patterns in valid dates.

    Jan 1 dates remain in counts and sales but are flagged as a possible
    imprecise-date convention; the audit found year clusters at Jan 1 and
    therefore daily precision should not be assumed from ISO syntax alone.
    """
    rows = rows_as_mappings(data)
    by_year: dict[int, dict[str, Any]] = defaultdict(lambda: {"records": 0, "sales": []})
    by_quarter: dict[int, dict[str, Any]] = defaultdict(lambda: {"records": 0, "sales": []})
    by_month: dict[int, dict[str, Any]] = defaultdict(lambda: {"records": 0, "sales": []})
    by_weekday: dict[int, dict[str, Any]] = defaultdict(lambda: {"records": 0, "sales": []})
    valid_dates = jan1 = 0
    for row in rows:
        release = _parse_iso_date(row.get("release_date"))
        if release is None:
            continue
        valid_dates += 1
        jan1 += release.month == 1 and release.day == 1
        sales = as_number(row.get("total_sales"))
        fields = ((by_year[release.year], release.year), (by_quarter[(release.month - 1)//3 + 1], (release.month - 1)//3 + 1),
                  (by_month[release.month], release.month), (by_weekday[release.weekday()], release.weekday()))
        for group, _key in fields:
            group["records"] += 1
            if sales is not None and sales >= 0:
                group["sales"].append(sales)
    def records(groups: dict[int, dict[str, Any]], key_name: str, labels: dict[int, str] | None = None) -> list[dict[str, Any]]:
        output = []
        for key, item in sorted(groups.items()):
            total = sum(item["sales"])
            output.append({key_name: key, **({"label": labels[key]} if labels else {}),
                           "release_records": item["records"], "records_with_sales": len(item["sales"]),
                           "total_sales": total if item["sales"] else None,
                           "mean_sales": statistics.fmean(item["sales"]) if item["sales"] else None})
        return output
    return {
        "source_dataset": "vgchartz-2024.csv", "source_rows": len(rows),
        "valid_iso_release_dates": valid_dates,
        "missing_or_invalid_release_dates": len(rows) - valid_dates,
        "jan_1_possible_imprecise_dates": jan1,
        "date_precision_note": "ISO date parsing validates calendar form, not whether month/day are source-observed; Jan 1 clusters may represent year-only precision.",
        "by_year": records(by_year, "year"),
        "by_quarter": records(by_quarter, "quarter", {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}),
        "by_month": records(by_month, "month"),
        "by_weekday": records(by_weekday, "weekday", {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}),
    }


def recent_industry_trends(data: Any, recent_years: int = 10) -> dict[str, Any]:
    """Describe the trailing observed release-year window (default ten years).

    The window ends at the latest valid release year in the source rather than
    the machine's current year. This makes runs deterministic and avoids
    mislabeling absent future years as zero releases.
    """
    rows = rows_as_mappings(data)
    if recent_years <= 0:
        return {"window_years": recent_years, "window_start": None, "window_end": None, "annual": []}
    groups: dict[int, dict[str, Any]] = defaultdict(lambda: {"records": 0, "sales": [], "consoles": set(), "publishers": set(), "developers": set()})
    observed_years = []
    for row in rows:
        release = _parse_iso_date(row.get("release_date"))
        if release is None:
            continue
        year = release.year
        observed_years.append(year)
        item = groups[year]
        item["records"] += 1
        sales = as_number(row.get("total_sales"))
        if sales is not None and sales >= 0:
            item["sales"].append(sales)
        for field, key in (("console", "consoles"), ("publisher", "publishers"), ("developer", "developers")):
            value = category(row.get(field))
            if value:
                item[key].add(value)
    if not observed_years:
        return {"source_dataset": "vgchartz-2024.csv", "window_years": recent_years, "window_start": None, "window_end": None, "annual": []}
    end = max(observed_years)
    start = end - recent_years + 1
    annual = []
    previous: dict[str, Any] | None = None
    for year in range(start, end + 1):
        item = groups.get(year)
        if item is None:
            continue
        current = {
            "year": year, "release_records": item["records"], "records_with_sales": len(item["sales"]),
            "total_sales": sum(item["sales"]) if item["sales"] else None,
            "mean_sales": statistics.fmean(item["sales"]) if item["sales"] else None,
            "median_sales": statistics.median(item["sales"]) if item["sales"] else None,
            "console_count": len(item["consoles"]), "publisher_count": len(item["publishers"]),
            "developer_count": len(item["developers"]),
            "previous_observed_year": previous["year"] if previous else None,
            "release_record_change_percent": 100 * (item["records"] - previous["release_records"]) / previous["release_records"] if previous and previous["release_records"] else None,
            "sales_change_percent": 100 * (sum(item["sales"]) - previous["total_sales"]) / previous["total_sales"] if previous and previous["total_sales"] not in (None, 0) and item["sales"] else None,
        }
        annual.append(current)
        previous = current
    return {"source_dataset": "vgchartz-2024.csv", "window_years": recent_years,
            "window_start": start, "window_end": end, "annual": annual}


def advanced_dataset_profile(data: Any) -> dict[str, Any]:
    """Summarize supplemental-source coverage for fields used by this module."""
    rows = rows_as_mappings(data)
    fields = ("critic_score", "total_sales", "release_date", "publisher", "developer", "console", "genre")
    coverage = {}
    for field in fields:
        present = sum(category(row.get(field)) is not None for row in rows)
        coverage[field] = {"present": present, "missing": len(rows) - present,
                           "coverage_percent": 100 * present / len(rows) if rows else None}
    return {"source_dataset": "vgchartz-2024.csv", "row_count": len(rows),
            "duplicate_candidate_rows_retained": sum(category(row.get("_duplicate_status")) not in (None, "unique_by_checked_rules") for row in rows),
            "field_coverage": coverage,
            "source_separation_note": "These results use only vgchartz-2024.csv; they are not pooled with vgsales.csv."}
