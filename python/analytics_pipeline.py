"""Build and export dashboard-ready analytics from separately cleaned sources."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

from .genre_analysis import genre_frequency, genre_global_sales
from .advanced_analysis import (
    advanced_dataset_profile,
    critic_score_sales_association,
    developer_performance,
    platform_evolution as vgchartz_platform_evolution,
    publisher_developer_performance,
    publisher_performance,
    recent_industry_trends,
    release_date_trends,
)
from .insights import generate_insights
from .market_power import market_power_index, publisher_genre_market_shares
from .metrics import descriptive_statistics, top_games
from .platform_analysis import platform_evolution, platform_game_counts, platform_global_sales
from .publisher_analysis import publisher_genre_dominance, publisher_summary, top_publishers
from .regional_analysis import regional_genre_preferences, regional_sales_comparison
from .regional_divergence import (
    cultural_outliers,
    genre_region_affinity,
    regional_divergence_by_game,
    regional_favorites_by_year,
    regional_preference_changes,
    regional_preference_divergence_by_year,
    regional_preference_stability,
)
from .trends import annual_trends, games_released_per_year, global_sales_by_year
from .load_data import PROJECT_ROOT, load_primary_cleaned


ANALYSIS_FILES = {
    "dashboard_primary_records": ("dashboard_primary_records.json",),
    "dashboard_data_quality": ("dashboard_data_quality.json",),
    "descriptive_statistics": ("descriptive_statistics.json",),
    "top_games": ("top_games.json", "top_games.csv"),
    "games_released_per_year": ("games_released_per_year.json", "games_released_per_year.csv"),
    "global_sales_by_year": ("global_sales_by_year.json", "global_sales_by_year.csv"),
    "annual_trends": ("annual_trends.json", "annual_trends.csv"),
    "genre_frequency": ("genre_frequency.json", "genre_frequency.csv"),
    "genre_global_sales": ("genre_global_sales.json", "genre_global_sales.csv"),
    "platform_game_counts": ("platform_game_counts.json", "platform_game_counts.csv"),
    "platform_global_sales": ("platform_global_sales.json", "platform_global_sales.csv"),
    "platform_evolution": ("platform_evolution.json", "platform_evolution.csv"),
    "regional_sales_comparison": ("regional_sales_comparison.json", "regional_sales_comparison.csv"),
    "regional_genre_preferences": ("regional_genre_preferences.json", "regional_genre_preferences.csv"),
    "publisher_summary": ("publisher_summary.json", "publisher_summary.csv"),
    "top_publishers": ("top_publishers.json", "top_publishers.csv"),
    "publisher_genre_dominance": ("publisher_genre_dominance.json", "publisher_genre_dominance.csv"),
    "market_power_index": ("market_power_index.json", "market_power_index.csv"),
    "publisher_genre_market_shares": ("publisher_genre_market_shares.json", "publisher_genre_market_shares.csv"),
    "regional_divergence_by_game": ("regional_divergence_by_game.json", "regional_divergence_by_game.csv"),
    "regional_favorites_by_year": ("regional_favorites_by_year.json", "regional_favorites_by_year.csv"),
    "regional_preference_stability": ("regional_preference_stability.json", "regional_preference_stability.csv"),
    "regional_preference_divergence_by_year": ("regional_preference_divergence_by_year.json", "regional_preference_divergence_by_year.csv"),
    "genre_region_affinity": ("genre_region_affinity.json", "genre_region_affinity.csv"),
    "regional_preference_changes": ("regional_preference_changes.json", "regional_preference_changes.csv"),
    "cultural_outliers": ("cultural_outliers.json", "cultural_outliers.csv"),
    "insights": ("insights.json",),
    "vgchartz_profile": ("vgchartz_profile.json",),
    "critic_score_sales_association": ("critic_score_sales_association.json",),
    "critic_score_sales_points": ("critic_score_sales_points.json", "critic_score_sales_points.csv"),
    "developer_performance": ("vgchartz_developer_performance.json", "vgchartz_developer_performance.csv"),
    "publisher_performance": ("vgchartz_publisher_performance.json", "vgchartz_publisher_performance.csv"),
    "publisher_developer_performance": ("vgchartz_publisher_developer_performance.json", "vgchartz_publisher_developer_performance.csv"),
    "vgchartz_platform_by_year": ("vgchartz_platform_by_year.json", "vgchartz_platform_by_year.csv"),
    "vgchartz_platform_lifecycle": ("vgchartz_platform_lifecycle.json", "vgchartz_platform_lifecycle.csv"),
    "vgchartz_release_date_trends": ("vgchartz_release_date_trends.json",),
    "vgchartz_release_by_year": ("vgchartz_release_by_year.json", "vgchartz_release_by_year.csv"),
    "vgchartz_release_by_quarter": ("vgchartz_release_by_quarter.json", "vgchartz_release_by_quarter.csv"),
    "vgchartz_release_by_month": ("vgchartz_release_by_month.json", "vgchartz_release_by_month.csv"),
    "vgchartz_release_by_weekday": ("vgchartz_release_by_weekday.json", "vgchartz_release_by_weekday.csv"),
    "recent_industry_trends": ("vgchartz_recent_industry_trends.json",),
    "recent_industry_trends_annual": ("vgchartz_recent_industry_trends_annual.json", "vgchartz_recent_industry_trends_annual.csv"),
}


def _optional_number(value: Any, *, integer: bool = False) -> int | float | None:
    """Convert one cleaned CSV scalar for compact dashboard data; blanks stay null."""
    if value is None or str(value).strip() == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return int(number) if integer and number.is_integer() else number


def _dashboard_records(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Expose typed cleaned primary rows for lightweight dashboard filtering."""
    numeric = {
        "Rank": True, "Year": True, "NA_Sales": False, "EU_Sales": False,
        "JP_Sales": False, "Other_Sales": False, "Global_Sales": False,
    }
    text = ("Name", "Platform", "Genre", "Publisher")
    records: list[dict[str, Any]] = []
    for row in rows:
        record: dict[str, Any] = {
            "source_row": _optional_number(row.get("_source_row"), integer=True),
            "duplicate_status": row.get("_duplicate_status") or None,
        }
        record.update({field: _optional_number(row.get(field), integer=is_integer) for field, is_integer in numeric.items()})
        record.update({field: (row.get(field) or None) for field in text})
        records.append(record)
    return records


def _dashboard_quality(rows: list[dict[str, str]], advanced_rows: list[dict[str, str]], summary_path: Path) -> dict[str, Any]:
    """Summarize actual cleaning provenance and missingness for the quality page."""
    if not summary_path.is_file():
        raise FileNotFoundError(f"Cleaning summary is missing: {summary_path}; run the cleaning pipeline first.")
    cleaning = json.loads(summary_path.read_text(encoding="utf-8"))
    datasets = cleaning.get("datasets", [])
    primary = next((item for item in datasets if item.get("dataset") == "vgsales.csv"), None)
    advanced = next((item for item in datasets if item.get("dataset") == "vgchartz-2024.csv"), None)
    if primary is None:
        raise ValueError("Cleaning summary does not include vgsales.csv provenance.")
    def source_quality(source: dict[str, Any], source_rows: list[dict[str, str]]) -> dict[str, Any]:
        columns = [key for key in (source_rows[0].keys() if source_rows else []) if not key.startswith("_")]
        missing_by_field = {column: sum(1 for row in source_rows if not (row.get(column) or "").strip()) for column in columns}
        duplicate = source.get("duplicate_handling", {})
        return {
            "source_dataset": source.get("dataset"),
            "processed_dataset": Path(source.get("output_file", "processed output")).name,
            "original_rows": source.get("input_rows"),
            "cleaned_rows": source.get("output_rows"),
            "rows_removed": source.get("rows_removed"),
            "missing_value_total": sum(missing_by_field.values()),
            "missing_values_by_field": missing_by_field,
            "exact_duplicate_groups_flagged": duplicate.get("exact_duplicate_groups", 0),
            "potential_duplicate_groups_flagged": duplicate.get("potential_game_key_groups", 0),
            "duplicate_rows_flagged": duplicate.get("exact_duplicate_rows_flagged", 0) + duplicate.get("potential_game_key_rows_flagged", 0),
            "transformation_events": source.get("transformation_events", 0),
            "rows_with_transformations": source.get("rows_with_logged_transformations", 0),
            "transformations_by_field": source.get("field_change_counts", {}),
            "categorical_policy": source.get("categorical_policy", ""),
            "missing_policy": source.get("missing_policy", ""),
            "duplicate_policy": "Candidate duplicate records are flagged and retained; rows removed: 0.",
        }
    primary_quality = source_quality(primary, rows)
    advanced_quality = source_quality(advanced, advanced_rows) if advanced else None
    return {
        **primary_quality,
        "advanced_source": advanced_quality,
    }


def build_analytics(data: Any, vgchartz_data: Any = None) -> dict[str, Any]:
    """Run all assignment analyses on the supplied cleaned primary data.

    Args:
        data: Row mappings or a DataFrame following the cleaned `vgsales.csv` schema.
        vgchartz_data: Optional, separate row mappings/DataFrame following the
            cleaned `vgchartz-2024.csv` schema. It is never merged with `data`.

    Returns:
        A dictionary of named result tables and descriptive metadata. No file
        I/O, global data, or printing is used by this function.
    """
    result = {
        "dashboard_primary_records": _dashboard_records(data if isinstance(data, list) else data.to_dict(orient="records")),
        "descriptive_statistics": descriptive_statistics(data),
        "top_games": top_games(data, 10),
        "games_released_per_year": games_released_per_year(data),
        "global_sales_by_year": global_sales_by_year(data),
        "annual_trends": annual_trends(data),
        "genre_frequency": genre_frequency(data),
        "genre_global_sales": genre_global_sales(data),
        "platform_game_counts": platform_game_counts(data),
        "platform_global_sales": platform_global_sales(data),
        "platform_evolution": platform_evolution(data),
        "regional_sales_comparison": regional_sales_comparison(data),
        "regional_genre_preferences": regional_genre_preferences(data),
        "publisher_summary": publisher_summary(data),
        "top_publishers": top_publishers(data, 10),
        "publisher_genre_dominance": publisher_genre_dominance(data),
        "market_power_index": market_power_index(data),
        "publisher_genre_market_shares": publisher_genre_market_shares(data),
        "regional_divergence_by_game": regional_divergence_by_game(data),
        "regional_favorites_by_year": regional_favorites_by_year(data),
        "regional_preference_stability": regional_preference_stability(data),
        "regional_preference_divergence_by_year": regional_preference_divergence_by_year(data),
        "genre_region_affinity": genre_region_affinity(data),
        "regional_preference_changes": regional_preference_changes(data),
        "cultural_outliers": cultural_outliers(data),
        "insights": generate_insights(data),
    }
    vg_rows = vgchartz_data if vgchartz_data is not None else []
    association = critic_score_sales_association(vg_rows)
    points = association.pop("paired_points", [])
    date_trends = release_date_trends(vg_rows)
    platform_trends = vgchartz_platform_evolution(vg_rows)
    recent_trends = recent_industry_trends(vg_rows)
    result.update({
        "vgchartz_profile": advanced_dataset_profile(vg_rows),
        "critic_score_sales_association": association,
        "critic_score_sales_points": points,
        "developer_performance": developer_performance(vg_rows),
        "publisher_performance": publisher_performance(vg_rows),
        "publisher_developer_performance": publisher_developer_performance(vg_rows),
        "vgchartz_platform_by_year": platform_trends["console_year"],
        "vgchartz_platform_lifecycle": platform_trends["console_lifecycle"],
        "vgchartz_release_date_trends": date_trends,
        "vgchartz_release_by_year": date_trends["by_year"],
        "vgchartz_release_by_quarter": date_trends["by_quarter"],
        "vgchartz_release_by_month": date_trends["by_month"],
        "vgchartz_release_by_weekday": date_trends["by_weekday"],
        "recent_industry_trends": {key: value for key, value in recent_trends.items() if key != "annual"},
        "recent_industry_trends_annual": recent_trends["annual"],
    })
    return result


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"Cannot serialize {type(value).__name__} to JSON")


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=_json_default) + "\n", encoding="utf-8")


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=_json_default)
    return value


def _write_records_csv(path: Path, records: list[dict[str, Any]]) -> list[str]:
    columns = list(records[0].keys()) if records else []
    with path.open("w", encoding="utf-8", newline="") as stream:
        if not columns:
            return columns
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({key: _csv_value(value) for key, value in record.items()})
    return columns


def _column_schema(results: dict[str, Any]) -> dict[str, Any]:
    schema = {}
    for name, value in results.items():
        if isinstance(value, list):
            sample = value[0] if value else {}
            schema[name] = {"kind": "record_table", "fields": list(sample.keys()), "row_count": len(value)}
        elif isinstance(value, dict):
            schema[name] = {"kind": "keyed_object", "keys": list(value.keys())}
        else:
            schema[name] = {"kind": type(value).__name__}
    return schema


def _schema_document() -> str:
    return """# Analytics export schema

These outputs are generated by `python -m python.analytics_pipeline` from `data/processed/vgsales_clean.csv` and `data/processed/vgchartz_2024_clean.csv`. Each table is source-specific: required analyses use only `vgsales.csv`, and `vgchartz_*` analyses use only `vgchartz-2024.csv`; the files are never pooled. All sales values use their source-reported units and definitions. JSON null means unavailable/not computable; zero means a reported zero.

## Stable exports

| Filename stem | Grain / contents |
|---|---|
| `dashboard_primary_records` | Typed, cleaned primary source rows for responsive dashboard filtering. These are not raw records or analytical aggregates; complex derived metrics continue to use the Python tables below. |
| `dashboard_data_quality` | Original/cleaned row counts, field missingness from the cleaned primary CSV, duplicate candidates, and logged cleaning transformations. |
| `descriptive_statistics` | Numeric field keyed object: count, missing/invalid count, min, quartiles, median, max, mean, population standard deviation. |
| `top_games` | Game/platform/year/genre/publisher ranked by `Global_Sales`, maximum ten records. |
| `games_released_per_year` | One row per valid year; count of records. Rows with invalid/missing year are omitted from this grouping. |
| `global_sales_by_year` | One row per valid year; number of rows with both year and sales, total and mean. |
| `annual_trends` | Combined release counts and global sales summary by year. |
| `genre_frequency` | One row per genre label; game-record count. |
| `genre_global_sales` | One row per genre; valid sales count, total, mean, share of total. |
| `platform_game_counts` | One row per platform label; record count. |
| `platform_global_sales` | One row per platform; valid sales count, total, mean, share. |
| `platform_evolution` | One row per platform/year; release count and global sales sum. |
| `regional_sales_comparison` | One row per region (`North America`, `Europe`, `Japan`, `Other`); sum, mean, row coverage, share of reported regional sales. |
| `regional_genre_preferences` | One row per genre/region; regional sales, within-genre share, overall regional baseline, affinity ratio. Ratio >1 means over-index relative to the full source mix. |
| `publisher_summary`, `top_publishers` | One row per publisher or top ten; record/sales counts, sales totals/share, genre footprint. Literal placeholder categories remain distinct. |
| `publisher_genre_dominance` | One row per publisher/genre; genre sales share and strict >30% leadership flag. |
| `market_power_index` | One row per publisher; composite, components, rank, leader genres, and archetype. Formula `mpi_equal_weight_arithmetic_v2` averages the available normalized components equally. |
| `publisher_genre_market_shares` | One row per publisher/genre; publisher sales divided by all genre sales and strict >30% leadership flag. |
| `regional_divergence_by_game` | One eligible game/platform row; regional shares and total-variation distance from overall regional sales mix (0-1). Incomplete regional data and zero regional totals are excluded from this metric only. |
| `regional_favorites_by_year` | One row per observed year/region; highest-sales genre, with alphabetical tie-break. |
| `regional_preference_stability` | One row per region; share of adjacent observed-year favorite pairs that repeat. Gaps in calendar years are not filled. |
| `regional_preference_divergence_by_year` | One row per year; pairwise total-variation distances among regional genre mixes and their mean. |
| `genre_region_affinity` | One row per genre/region; affinity ratio and over/under-index label at the exact neutral baseline of 1. |
| `regional_preference_changes` | One row per region/year/genre; share and change versus the prior observed year, with no interpolation. |
| `cultural_outliers` | Eligible games with >50% of regional sales in a single region and <10% in each other region. Score = 100 times (dominant share minus largest other share). |
| `insights` | Evidence-linked cards generated from computed values; each has metric, source, coverage, and computed value. |
| `vgchartz_*` | Source-separated advanced outputs: score-sales association, developer/publisher summaries, console evolution, date trends, and trailing observed-year trends. |

Each table has matching `.json` and `.csv` files except descriptive statistics and insights, which are JSON-only. CSVs encode nested objects/arrays as JSON strings. `manifest.json` records pipeline version, generated timestamp, input row count, schema fields and row counts. `analytics_schema.json` and this README describe table fields and definitions. Values are calculated by Python, not hardcoded in a frontend.

## Interpretation notes

- Regional labels follow `vgsales.csv`; Europe is `EU_Sales`. They are not mapped to the supplemental source's PAL region.
- Duplicate game rows are kept. Analyses treat source rows as records unless a metric explicitly aggregates them by label.
- The Market Power Index is a project-specific descriptive composite, not an established industry standard. Formula and component choices are documented in `reports/advanced-analysis.md` and versioned in each result row.
- Regional divergence uses total variation distance. It is bounded between 0 and 1; higher values indicate greater difference from the overall regional mix.
- `vgchartz-2024.csv` outputs are computed separately and never pooled into primary assignment tables. Its regional field `PAL` is not renamed to `Europe`.
"""


def export_analytics(root: Path = PROJECT_ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    """Compute primary and vgchartz-only analyses and export stable JSON/CSV files."""
    root = root.resolve()
    input_path = root / "data" / "processed" / "vgsales_clean.csv"
    advanced_input_path = root / "data" / "processed" / "vgchartz_2024_clean.csv"
    if not input_path.is_file():
        raise FileNotFoundError(f"Missing {input_path}; run the cleaning pipeline first.")
    if not advanced_input_path.is_file():
        raise FileNotFoundError(f"Missing {advanced_input_path}; run the cleaning pipeline first.")
    from .load_data import load_processed_rows
    rows = load_processed_rows(input_path)
    vgchartz_rows = load_processed_rows(advanced_input_path)
    results = build_analytics(rows, vgchartz_rows)
    results["dashboard_data_quality"] = _dashboard_quality(rows, vgchartz_rows, root / "data" / "processed" / "cleaning_summary.json")
    target = (output_dir or root / "data" / "processed" / "analytics").resolve()
    target.mkdir(parents=True, exist_ok=True)
    schemas = _column_schema(results)
    output_inventory: dict[str, Any] = {}
    for key, filenames in ANALYSIS_FILES.items():
        value = results[key]
        for filename in filenames:
            path = target / filename
            if filename.endswith(".json"):
                _write_json(path, value)
                fields = list(value[0].keys()) if isinstance(value, list) and value else list(value.keys()) if isinstance(value, dict) else []
                count = len(value) if isinstance(value, list) else None
            else:
                records = value if isinstance(value, list) else []
                fields = _write_records_csv(path, records)
                count = len(records)
            output_inventory[filename] = {"rows": count, "fields": fields, "bytes": path.stat().st_size}
    generated = datetime.now().astimezone().isoformat(timespec="seconds")
    manifest = {
        "schema_version": 1,
        "pipeline_version": "gamescope_analytics_v2",
        "generated_at": generated,
        "source_dataset": "vgsales.csv",
        "source_processed_path": "data/processed/vgsales_clean.csv",
        "source_rows": len(rows),
        "advanced_source_dataset": "vgchartz-2024.csv",
        "advanced_source_processed_path": "data/processed/vgchartz_2024_clean.csv",
        "advanced_source_rows": len(vgchartz_rows),
        "row_policy": "No input records removed by analytics; group-specific missing-value eligibility is documented per output.",
        "outputs": output_inventory,
    }
    _write_json(target / "manifest.json", manifest)
    _write_json(target / "analytics_schema.json", {"schema_version": 1, "tables": schemas})
    (target / "README.md").write_text(_schema_document(), encoding="utf-8")
    return {"results": results, "manifest": manifest, "output_dir": target}


def main() -> None:
    parser = argparse.ArgumentParser(description="Export GameScope core analytics from the cleaned primary dataset.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Project root.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Analytics output directory.")
    args = parser.parse_args()
    result = export_analytics(args.root, args.output_dir)
    print(f"Analytics exports written to {result['output_dir']}")
    print(f"Source records: {result['manifest']['source_rows']:,}; output files: {len(result['manifest']['outputs'])}")


if __name__ == "__main__":
    main()
