"""Post-cleaning validations; warnings are distinguished from hard failures."""

from __future__ import annotations

import csv
import hashlib
from datetime import date
from pathlib import Path
from typing import Any

from .clean_data import DATE_COLUMNS, NUMERIC_COLUMNS


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _number(value: str) -> float | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def validate_output(
    dataset: str,
    raw_path: Path,
    output_path: Path,
    expected_rows: int,
    expected_columns: list[str],
    source_hash_before: str,
    duplicate_summary: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {}
    if not output_path.is_file():
        return {"dataset": dataset, "passed": False, "errors": [f"Output does not exist: {output_path}"], "warnings": [], "checks": {}}

    with output_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        output_columns = reader.fieldnames or []
        rows = list(reader)
    checks["output_rows"] = len(rows)
    checks["output_columns"] = len(output_columns)
    checks["expected_rows"] = expected_rows
    if len(rows) != expected_rows:
        errors.append(f"Row count changed: input {expected_rows}, processed output {len(rows)}.")
    if output_columns != expected_columns:
        errors.append("Processed output columns/order do not match the declared schema.")
    if duplicate_summary.get("rows_removed") != 0:
        errors.append("Duplicate handling unexpectedly reports removed rows.")
    checks["rows_removed"] = duplicate_summary.get("rows_removed", 0)
    checks["raw_hash_before"] = source_hash_before
    current_hash = sha256_file(raw_path)
    checks["raw_hash_after"] = current_hash
    if current_hash != source_hash_before:
        errors.append("Raw source fingerprint changed while pipeline ran.")

    if "_source_row" in output_columns:
        expected_ids = [str(index) for index in range(1, len(rows) + 1)]
        actual_ids = [row.get("_source_row", "") for row in rows]
        if actual_ids != expected_ids:
            errors.append("_source_row must be a stable, sequential 1-based source row index.")
        else:
            checks["source_row_sequence"] = "valid"
    if "_duplicate_status" in output_columns:
        valid_status = {"unique_by_checked_rules", "game_key_candidate", "exact_duplicate_candidate", "exact_and_game_key_candidate"}
        bad_status = sorted({row.get("_duplicate_status", "") for row in rows} - valid_status)
        if bad_status:
            errors.append(f"Unknown duplicate status values: {bad_status}")
        checks["duplicate_status_values"] = sorted({row.get("_duplicate_status", "") for row in rows})

    numeric_checks = {}
    for column, dtype in NUMERIC_COLUMNS[dataset].items():
        if column not in output_columns:
            errors.append(f"Required numeric field missing from output: {column}")
            continue
        invalid = [(index + 1, row[column]) for index, row in enumerate(rows) if row.get(column, "") and _number(row[column]) is None]
        if invalid:
            errors.append(f"{column}: {len(invalid)} nonempty output values are not numeric; examples {invalid[:5]}.")
        values = [number for row in rows if (number := _number(row.get(column, ""))) is not None]
        numeric_checks[column] = {
            "declared_dtype": dtype,
            "parsed_values": len(values),
            "missing_values": len(rows) - len(values),
            "min": min(values) if values else None,
            "max": max(values) if values else None,
        }
        if column.lower().endswith("sales") or column == "Global_Sales":
            negative = sum(value < 0 for value in values)
            numeric_checks[column]["negative_values"] = negative
            if negative:
                warnings.append(f"{column} has {negative} negative values; retained for review, not removed.")
    checks["numeric_fields"] = numeric_checks

    date_checks = {}
    for column in DATE_COLUMNS[dataset]:
        if column not in output_columns:
            errors.append(f"Required date field missing from output: {column}")
            continue
        bad = []
        parsed = []
        for index, row in enumerate(rows):
            value = row.get(column, "")
            if not value:
                continue
            try:
                parsed.append(date.fromisoformat(value))
            except ValueError:
                bad.append((index + 1, value))
        if bad:
            errors.append(f"{column}: invalid dates remain in output; examples {bad[:5]}.")
        date_checks[column] = {
            "valid_iso_dates": len(parsed),
            "missing_dates": len(rows) - len(parsed) - len(bad),
            "invalid_dates": len(bad),
            "min": min(parsed).isoformat() if parsed else None,
            "max": max(parsed).isoformat() if parsed else None,
        }
    checks["date_fields"] = date_checks

    sales_fields = [field for field in NUMERIC_COLUMNS[dataset] if field.lower().endswith("sales")]
    negative_sales = {column: numeric_checks[column]["negative_values"] for column in sales_fields if numeric_checks[column]["negative_values"]}
    if negative_sales:
        warnings.append(f"Negative sales observed and retained: {negative_sales}.")
    if duplicate_summary.get("exact_duplicate_groups", 0) or duplicate_summary.get("potential_game_key_groups", 0):
        warnings.append("Duplicate candidates were flagged and retained; human review is needed before any removal.")
    return {"dataset": dataset, "passed": not errors, "errors": errors, "warnings": warnings, "checks": checks}
