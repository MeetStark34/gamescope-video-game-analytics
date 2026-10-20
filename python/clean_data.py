"""Conservative, source-specific cleaning and explicit dtype conversion."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ImportError:  # Allows the pipeline to run before optional setup is performed.
    pd = None  # type: ignore[assignment]

PANDAS_AVAILABLE = pd is not None

NUMERIC_COLUMNS = {
    "vgsales.csv": {"Rank": "Int64", "Year": "Int64", "NA_Sales": "Float64", "EU_Sales": "Float64", "JP_Sales": "Float64", "Other_Sales": "Float64", "Global_Sales": "Float64"},
    "vgchartz-2024.csv": {"critic_score": "Float64", "total_sales": "Float64", "na_sales": "Float64", "jp_sales": "Float64", "pal_sales": "Float64", "other_sales": "Float64"},
}
DATE_COLUMNS = {
    "vgsales.csv": {},
    "vgchartz-2024.csv": {"release_date": "%Y-%m-%d", "last_update": "%Y-%m-%d"},
}
TEXT_COLUMNS = {
    "vgsales.csv": {"Name", "Platform", "Genre", "Publisher"},
    "vgchartz-2024.csv": {"img", "title", "console", "genre", "publisher", "developer"},
}
NULL_NUMERIC_TOKENS = {"n/a", "na", "null", "none", "nan", "<na>", "-", "--", "tbd", "unknown"}


def _log(
    audit_log: list[dict[str, Any]], dataset: str, source_row: int | None,
    source_column: str | None, output_column: str | None, before: Any,
    after: Any, rule: str, record_type: str = "cell_transformation",
) -> None:
    audit_log.append({
        "record_type": record_type,
        "dataset": dataset,
        "source_row": source_row,
        "source_column": source_column,
        "output_column": output_column,
        "original_value": before,
        "cleaned_value": after,
        "rule": rule,
    })


def _schema_name_map(dataset: str, columns: list[str], audit_log: list[dict[str, Any]]) -> dict[str, str]:
    """Apply only known, explicit header aliases; preserve all other spelling."""
    aliases = {"vgchartz-2024.csv": {"last_update;;": "last_update"}}.get(dataset, {})
    mapping: dict[str, str] = {}
    for original in columns:
        cleaned = aliases.get(original, original.strip())
        if cleaned != original:
            _log(audit_log, dataset, None, original, cleaned, original, cleaned,
                 "explicit_header_alias" if original in aliases else "trim_header_whitespace",
                 "schema_transformation")
        mapping[original] = cleaned
    if len(set(mapping.values())) != len(mapping):
        raise ValueError(f"Header normalization creates duplicate columns in {dataset}: {mapping}")
    return mapping


def _collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _as_number(value: str, integer: bool) -> int | float | None:
    if value.strip().casefold() in NULL_NUMERIC_TOKENS:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not number.is_integer() and integer:
        return None
    return int(number) if integer else number


def _as_date(value: str) -> str | None:
    if not value:
        return None
    try:
        # Strict full-date input; no guessed formats or inferred day/month.
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def _duplicate_metadata(dataset: str, columns: list[str], rows: list[dict[str, Any]], audit_log: list[dict[str, Any]]) -> dict[str, Any]:
    exact_keys = []
    for row in rows:
        exact_keys.append(tuple(row.get(column) for column in columns))
    exact_counts = Counter(exact_keys)
    exact_rows: set[int] = set()
    exact_groups = 0
    for key, count in exact_counts.items():
        if count > 1:
            exact_groups += 1
            matched = [index for index, candidate in enumerate(exact_keys) if candidate == key]
            exact_rows.update(matched)
            _log(audit_log, dataset, None, None, None, list(key), matched,
                 "exact_duplicate_rows_flagged_and_retained", "duplicate_candidate_group")

    key_columns = ("Name", "Platform", "Year", "Genre", "Publisher") if dataset == "vgsales.csv" else ("title", "console", "release_date")
    key_counts: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        raw = [row.get(column) for column in key_columns]
        # Blank key pieces are too ambiguous for a useful grouped candidate.
        if any(value is None or str(value).strip() == "" for value in raw):
            continue
        key = tuple(_collapse_whitespace(str(value)).casefold() for value in raw)
        key_counts[key].append(index)
    candidate_rows: set[int] = set()
    candidate_groups = 0
    for key, indexes in key_counts.items():
        if len(indexes) > 1:
            candidate_groups += 1
            candidate_rows.update(indexes)
            _log(audit_log, dataset, None, None, None, list(key), indexes,
                 "candidate_game_key_duplicates_flagged_and_retained_review_required", "duplicate_candidate_group")
    for index, row in enumerate(rows):
        is_exact = index in exact_rows
        is_candidate = index in candidate_rows
        row["_duplicate_status"] = (
            "exact_and_game_key_candidate" if is_exact and is_candidate else
            "exact_duplicate_candidate" if is_exact else
            "game_key_candidate" if is_candidate else "unique_by_checked_rules"
        )
    return {
        "exact_duplicate_groups": exact_groups,
        "exact_duplicate_rows_flagged": len(exact_rows),
        "potential_game_key": list(key_columns),
        "potential_game_key_groups": candidate_groups,
        "potential_game_key_rows_flagged": len(candidate_rows),
        "rows_removed": 0,
    }


def clean_dataset(raw_dataset: Any) -> tuple[list[str], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Clean one dataset without dropping records or overwriting its raw file."""
    dataset = raw_dataset.name
    audit_log: list[dict[str, Any]] = []
    header_map = _schema_name_map(dataset, raw_dataset.columns, audit_log)
    numeric_columns = NUMERIC_COLUMNS[dataset]
    date_columns = DATE_COLUMNS[dataset]
    output_columns = [header_map[column] for column in raw_dataset.columns]
    cleaned_rows: list[dict[str, Any]] = []
    field_changes: Counter[str] = Counter()
    field_parse_failures: Counter[str] = Counter()
    field_null_tokens: Counter[str] = Counter()

    for source_row, raw_row in enumerate(raw_dataset.rows, start=1):
        cleaned: dict[str, Any] = {"_source_row": source_row}
        for source_column in raw_dataset.columns:
            output_column = header_map[source_column]
            raw_value = raw_row.get(source_column, "")
            if raw_value is None:
                raw_value = ""
            before = str(raw_value)
            value = before
            if output_column == "last_update":
                stripped_semicolons = value.rstrip(";").strip()
                if stripped_semicolons != value:
                    _log(audit_log, dataset, source_row, source_column, output_column,
                         value, stripped_semicolons,
                         "remove_export_trailing_semicolons_from_last_update_only")
                    field_changes[output_column] += 1
                value = stripped_semicolons
            normalized = _collapse_whitespace(value)
            if normalized != value:
                _log(audit_log, dataset, source_row, source_column, output_column,
                     value, normalized, "trim_and_collapse_whitespace")
                field_changes[output_column] += 1
            value = normalized

            if output_column in numeric_columns:
                integer = numeric_columns[output_column] == "Int64"
                parsed = _as_number(value, integer) if value else None
                if value and parsed is None:
                    field_parse_failures[output_column] += 1
                    if value.casefold() in NULL_NUMERIC_TOKENS:
                        field_null_tokens[output_column] += 1
                        rule = "numeric_null_like_token_set_to_missing_no_imputation"
                    else:
                        rule = "unparseable_or_nonintegral_numeric_set_to_missing_no_imputation"
                    _log(audit_log, dataset, source_row, source_column, output_column,
                         before, None, rule)
                    field_changes[output_column] += 1
                elif not value and before.strip():
                    _log(audit_log, dataset, source_row, source_column, output_column,
                         before, None, "blank_after_whitespace_cleanup_set_to_missing")
                    field_changes[output_column] += 1
                cleaned[output_column] = parsed
            elif output_column in date_columns:
                parsed = _as_date(value)
                if value and parsed is None:
                    field_parse_failures[output_column] += 1
                    _log(audit_log, dataset, source_row, source_column, output_column,
                         before, None, "invalid_or_non_ISO_date_set_to_missing_no_date_inference")
                    field_changes[output_column] += 1
                elif not value and before.strip():
                    _log(audit_log, dataset, source_row, source_column, output_column,
                         before, None, "delimiter_only_or_blank_date_set_to_missing")
                    field_changes[output_column] += 1
                cleaned[output_column] = parsed
            else:
                if not value:
                    cleaned[output_column] = None
                    if before.strip():
                        _log(audit_log, dataset, source_row, source_column, output_column,
                             before, None, "blank_after_whitespace_cleanup_set_to_missing")
                        field_changes[output_column] += 1
                else:
                    # Case, punctuation, Unknown, TBD, N/A and other labels are retained.
                    cleaned[output_column] = value
        cleaned_rows.append(cleaned)

    duplicate_report = _duplicate_metadata(dataset, output_columns, cleaned_rows, audit_log)
    output_columns += ["_source_row", "_duplicate_status"]
    summary = {
        "dataset": dataset,
        # Keep run summaries safe to share; do not serialize machine-specific paths.
        "input_path": raw_dataset.name,
        "input_rows": len(raw_dataset.rows),
        "output_rows": len(cleaned_rows),
        "input_columns": len(raw_dataset.columns),
        "output_columns": len(output_columns),
        "header_mapping": header_map,
        "categorical_policy": "trim and collapse whitespace only; preserve case, spelling, punctuation, N/A, Unknown, TBD, and other labels",
        "missing_policy": "blank values become null in processed outputs; numeric null-like tokens become null with row-level audit; categorical tokens remain literal; no imputation",
        "numeric_dtypes": numeric_columns,
        "date_dtypes": {column: "datetime64[ns]" for column in date_columns},
        "text_dtypes": sorted(TEXT_COLUMNS[dataset]),
        "field_change_counts": dict(field_changes),
        "numeric_or_date_parse_failures": dict(field_parse_failures),
        "numeric_null_like_token_counts": dict(field_null_tokens),
        "duplicate_handling": duplicate_report,
        "rows_removed": 0,
        "pandas_available": PANDAS_AVAILABLE,
        "output_backend": "pandas" if PANDAS_AVAILABLE else "stdlib_fallback",
    }
    return output_columns, cleaned_rows, audit_log, summary


def write_clean_csv(path: Path, columns: list[str], rows: list[dict[str, Any]], dataset: str) -> dict[str, str]:
    """Write typed output using pandas when installed, otherwise standard CSV."""
    dtype_map: dict[str, str] = {"_source_row": "Int64", "_duplicate_status": "string"}
    dtype_map.update(NUMERIC_COLUMNS[dataset])
    dtype_map.update({column: "string" for column in TEXT_COLUMNS[dataset]})
    dtype_map.update({column: "datetime64[ns]" for column in DATE_COLUMNS[dataset]})
    if PANDAS_AVAILABLE:
        frame = pd.DataFrame(rows, columns=columns)
        for column, dtype in dtype_map.items():
            if column not in frame.columns:
                continue
            if dtype == "datetime64[ns]":
                frame[column] = pd.to_datetime(frame[column], format="%Y-%m-%d", errors="coerce")
            elif dtype in {"Int64", "Float64"}:
                frame[column] = pd.to_numeric(frame[column], errors="coerce").astype(dtype)
            elif dtype == "string":
                frame[column] = frame[column].astype("string")
        frame.to_csv(path, index=False, encoding="utf-8", na_rep="")
        return {column: str(frame[column].dtype) for column in frame.columns}

    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            output = {}
            for column in columns:
                value = row.get(column)
                if value is None:
                    output[column] = ""
                elif column in DATE_COLUMNS[dataset] and value:
                    output[column] = str(value)
                else:
                    output[column] = value
            writer.writerow(output)
    return dtype_map


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
