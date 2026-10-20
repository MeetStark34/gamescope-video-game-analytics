"""Run the complete reproducible GameScope cleaning pipeline.

From the project root run:
    python -m python.pipeline
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from .clean_data import DATE_COLUMNS, NUMERIC_COLUMNS, PANDAS_AVAILABLE, TEXT_COLUMNS, clean_dataset, write_clean_csv, write_jsonl
from .load_data import PROJECT_ROOT, load_all
from .validation import sha256_file, validate_output


def _json_write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def _portable_path(path: Path, root: Path) -> str:
    """Return a repository-relative path, falling back to a basename outside root."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _render_cleaning_report(
    summaries: list[dict[str, Any]], validations: list[dict[str, Any]],
    audit_log_path: Path, output_dir: Path, run_started: str,
) -> str:
    lines = [
        "# GameScope Data Cleaning Report", "",
        f"Pipeline run: {run_started}", "",
        "## Scope", "",
        "The pipeline reads each source independently and writes cleaned copies under `data/processed/`. Raw input files are never overwritten. No datasets are merged. Every processed row retains a 1-based `_source_row` reference to its original data row.", "",
        "## Problems found and cleaning decisions", "",
        "| Issue | Decision applied | Reason / limitation |", "|---|---|---|",
        "| Source schemas differ; vgchartz has a final header `last_update;;` and trailing `;;` in that field's values | Rename that one known header to `last_update`; strip trailing semicolons from that field only; log every changed cell/header | Explicit export artifact rule; the original raw file remains intact. Other fields are not renamed by guessed aliases. |",
        "| Leading/trailing and repeated whitespace may occur in text and headers | Strip edges and collapse repeated internal whitespace in values; trim other headers only if needed; log changes | Preserve original case, punctuation, spelling, and substantive words. This does not resolve entity aliases. |",
        "| Categorical casing, spelling, and placeholders can be meaningful or inconsistent | Do not case-fold, spell-correct, or merge categories. Preserve `N/A`, `Unknown`, `TBD`, `-`, and other nonblank labels in categorical fields | Use audit candidates for later, documented crosswalk decisions; unknown and missing remain distinct. |",
        "| Blank fields and null-like tokens in numeric fields | Blank values and unparseable numeric tokens become nullable values; numeric `N/A`/similar tokens are logged as candidate missing; no imputation | Categorical `N/A` remains literal. A column-specific domain decision may later refine token meaning. |",
        "| Numeric-looking CSV strings | Convert only schema-declared numeric columns to nullable `Int64`/`Float64` when pandas is installed; reject non-integral values in integer fields to missing and log them | No values are filled or rounded. CSV output is text; `cleaning_schema.json` records intended dtypes. |",
        "| Date fields and imprecise/invalid values | Parse only ISO `YYYY-MM-DD`; strip the known vgchartz suffix first; invalid/delimiter-only values become missing and are logged | No inferred month/day, and no year-only date is fabricated. ISO syntax does not prove date precision. |",
        "| Exact and potential game-key duplicates | Keep and flag records; write duplicate candidate groups to the JSONL audit log | Title/platform/year or release date may identify ports, editions, or separate releases. No row is silently removed. |",
        "| Zero sales | Preserve numeric zero as zero | Zero is a reported value, not a missing-value marker. |",
        "", "## Files produced", "",
        f"- Processed CSV files: `{_portable_path(output_dir, output_dir.parent.parent)}`.",
        f"- Row-level transformation and duplicate log: `{_portable_path(audit_log_path, output_dir.parent.parent)}`.",
        f"- Run summary: `{_portable_path(output_dir / 'cleaning_summary.json', output_dir.parent.parent)}`.",
        f"- Dtype/schema contract: `{_portable_path(output_dir / 'cleaning_schema.json', output_dir.parent.parent)}`.",
        f"- Validation result: `{_portable_path(output_dir / 'validation_report.json', output_dir.parent.parent)}`.", "",
        "## Dataset results", "",
    ]
    for summary, validation in zip(summaries, validations):
        lines += [
            f"### {summary['dataset']}", "",
            f"- Input: `{Path(summary['input_path']).name}` ({summary['input_rows']:,} rows, {summary['input_columns']} columns).",
            f"- Output: `{Path(summary['output_file']).name}` ({summary['output_rows']:,} rows, {summary['output_columns']} columns).",
            f"- Logged cell transformation events: {summary['transformation_events']:,}; distinct source rows with at least one logged value change: {summary['rows_with_logged_transformations']:,}.",
            f"- Field-level events: `{json.dumps(summary['field_change_counts'], ensure_ascii=False)}`.",
            f"- Numeric/date parse failures set to missing: `{json.dumps(summary['numeric_or_date_parse_failures'], ensure_ascii=False)}`.",
            f"- Candidate null-like numeric tokens set to missing: `{json.dumps(summary['numeric_null_like_token_counts'], ensure_ascii=False)}`.",
            f"- Exact duplicate groups flagged: {summary['duplicate_handling']['exact_duplicate_groups']:,} ({summary['duplicate_handling']['exact_duplicate_rows_flagged']:,} rows flagged).",
            f"- Potential game-key groups flagged: {summary['duplicate_handling']['potential_game_key_groups']:,} ({summary['duplicate_handling']['potential_game_key_rows_flagged']:,} rows flagged); all retained.",
            f"- Rows removed: **{summary['rows_removed']}**.",
            f"- Validation: **{'passed' if validation['passed'] else 'failed'}**; errors: {validation['errors'] or 'none'}; warnings: {validation['warnings'] or 'none'}.",
            "",
        ]
    lines += [
        "## Validation", "",
        "The pipeline verifies output existence and schema, row-count preservation, source-row sequence, duplicate flags, parseability of typed output values, ISO date validity, and source SHA-256 equality before and after the run. Sales negatives and duplicate candidates are surfaced for review rather than automatically removed. Regional/global sum differences are retained because rounding and source methodology are unresolved.", "",
        "## Runtime limitation", "",
        "The current environment does not have pandas installed, and the package index was unavailable during this run. Therefore this execution used the standard-library CSV fallback; it emitted the same nullable-value conventions and a schema contract with the intended pandas dtypes. Install `python/requirements.txt` to run the pandas backend, which applies pandas nullable `Int64`, `Float64`, `string`, and `datetime64[ns]` dtypes before CSV serialization. The backend used is recorded in `cleaning_summary.json`.", "",
        "## Limitations", "",
        "- CSV serialization does not itself persist pandas dtypes. Consumers should load with the accompanying schema or run the pipeline with pandas.",
        "- Null-like token interpretation in numeric fields is conservative but still a documented choice; raw text is retained in the JSONL change log for every affected cell.",
        "- Categorical variants and potential duplicate games are not automatically reconciled; no spelling/identity crosswalk is inferred.",
        "- The datasets are not merged, and `EU_Sales` is not treated as interchangeable with `pal_sales`.",
        "- This pipeline does not perform analytical calculations or produce dashboard assets.", "",
    ]
    return "\n".join(lines)


def run_pipeline(root: Path = PROJECT_ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    output_dir = (output_dir or root / "data" / "processed").resolve()
    report_dir = root / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    run_started = datetime.now().astimezone().isoformat(timespec="seconds")

    raw_datasets = load_all(root)
    summaries: list[dict[str, Any]] = []
    full_audit_log: list[dict[str, Any]] = []
    schema_entries = []
    validation_inputs = []

    for raw in raw_datasets:
        output_columns, cleaned_rows, events, summary = clean_dataset(raw)
        summary["source_sha256"] = sha256_file(raw.path)
        output_name = "vgsales_clean.csv" if raw.name == "vgsales.csv" else "vgchartz_2024_clean.csv"
        output_path = output_dir / output_name
        declared_dtypes = write_clean_csv(output_path, output_columns, cleaned_rows, raw.name)
        source_rows_changed = {
            event["source_row"] for event in events
            if event.get("record_type") == "cell_transformation" and event.get("source_row") is not None
        }
        summary.update({
            "output_file": _portable_path(output_path, root),
            "rows_removed": 0,
            "transformation_events": sum(event.get("record_type") == "cell_transformation" for event in events),
            "rows_with_logged_transformations": len(source_rows_changed),
            "declared_output_dtypes": declared_dtypes,
        })
        validation_inputs.append((raw, output_path, output_columns, summary))
        summaries.append(summary)
        full_audit_log.extend(events)
        schema_entries.append({
            "dataset": raw.name,
            "columns": [{"name": column, "dtype": declared_dtypes.get(column, "string")} for column in output_columns],
            "source_columns": raw.columns,
            "header_mapping": summary["header_mapping"],
            "backend_used": summary["output_backend"],
        })

    audit_log_path = output_dir / "cleaning_audit.jsonl"
    write_jsonl(audit_log_path, full_audit_log)
    _json_write(output_dir / "cleaning_summary.json", {
        "run_started": run_started,
        "pandas_available": PANDAS_AVAILABLE,
        "backend_used": "pandas" if PANDAS_AVAILABLE else "stdlib_fallback",
        "datasets": summaries,
        "audit_log": _portable_path(audit_log_path, root),
        "audit_log_records": len(full_audit_log),
        "merge_performed": False,
    })
    _json_write(output_dir / "cleaning_schema.json", {
        "schema_version": 1,
        "note": "CSV files are serialized text. Dtypes are applied by the pandas backend and declared here for deterministic reloading.",
        "datasets": schema_entries,
    })

    validations = []
    for raw, output_path, expected_columns, summary in validation_inputs:
        validation = validate_output(
            raw.name, raw.path, output_path, len(raw.rows), expected_columns,
            summary["source_sha256"], summary["duplicate_handling"],
        )
        validations.append(validation)
    validation_report = {
        "run_started": run_started,
        "passed": all(item["passed"] for item in validations),
        "datasets": validations,
    }
    _json_write(output_dir / "validation_report.json", validation_report)
    (report_dir / "data-cleaning.md").write_text(
        _render_cleaning_report(summaries, validations, audit_log_path, output_dir, run_started),
        encoding="utf-8",
    )
    if not validation_report["passed"]:
        details = [error for item in validations for error in item["errors"]]
        raise RuntimeError("Pipeline validation failed: " + " | ".join(details))
    return {"summaries": summaries, "validations": validations, "output_dir": output_dir, "report": report_dir / "data-cleaning.md"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean GameScope source CSVs reproducibly without modifying raw files.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Project root (defaults to this module's parent project).")
    parser.add_argument("--output-dir", type=Path, default=None, help="Processed output directory (defaults to data/processed).")
    args = parser.parse_args()
    result = run_pipeline(args.root, args.output_dir)
    print(f"Cleaning complete and validated: {result['output_dir']}")
    for summary, validation in zip(result["summaries"], result["validations"]):
        print(f"{summary['dataset']}: {summary['input_rows']:,} input rows -> {summary['output_rows']:,} output rows; removed 0; validation {'passed' if validation['passed'] else 'failed'}")
        if not summary["pandas_available"]:
            print("  pandas not installed; standard-library fallback used. See reports/data-cleaning.md.")
    print(f"Report: {result['report']}")


if __name__ == "__main__":
    main()
