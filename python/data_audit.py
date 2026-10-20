#!/usr/bin/env python3
"""Read-only, standard-library audit for the GameScope source CSV files.

Run from the project root:
    python python/data_audit.py

The script reads the raw CSVs but never changes them. It writes a Markdown
report to reports/data-audit.md unless --output is supplied.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASETS = ("vgsales.csv", "vgchartz-2024.csv")
MISSING_TOKENS = {"", "n/a", "na", "null", "none", "nan", "<na>"}
PLACEHOLDER_TOKENS = MISSING_TOKENS | {"unknown", "-", "--", "tbd", "not available", "unspecified"}
SALES_COLUMNS = {
    "vgsales.csv": ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales"],
    "vgchartz-2024.csv": ["total_sales", "na_sales", "jp_sales", "pal_sales", "other_sales"],
}


def find_dataset(name: str, root: Path) -> Path:
    candidates = [root / "data" / "raw" / name, root / name]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(f"Could not locate {name}; checked: " + ", ".join(map(str, candidates)))


def read_dataset(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"No CSV header found in {path}")
        rows = list(reader)
    return list(reader.fieldnames), rows


def is_missing(value: str | None) -> bool:
    return value is None or value.strip().casefold() in MISSING_TOKENS


def is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def parse_number(value: str | None) -> float | None:
    if is_missing(value):
        return None
    try:
        number = float(value.strip().replace(",", ""))
        return number if math.isfinite(number) else None
    except (ValueError, AttributeError):
        return None


def normalize_category(value: str) -> str:
    return " ".join(value.split()).casefold()


def markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def fmt_number(value: float) -> str:
    return f"{value:,.6g}"


def fmt_pct(part: int | float, whole: int | float) -> str:
    return "n/a" if not whole else f"{100 * part / whole:.2f}%"


def source_fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def numeric_profile(values: list[str]) -> dict[str, Any]:
    present = [value for value in values if not is_missing(value)]
    parsed = [number for value in present if (number := parse_number(value)) is not None]
    return {"present": len(present), "parsed": parsed, "parse_failures": len(present) - len(parsed)}


def field_type(values: list[str], column: str = "") -> str:
    present = [value for value in values if not is_missing(value)]
    if not present:
        return "empty / unknown"
    if column in {"release_date", "last_update;;"}:
        return "date-like text (CSV strings; see detailed date parsing)"
    profile = numeric_profile(values)
    if profile["parsed"] and len(profile["parsed"]) == len(present):
        numbers = profile["parsed"]
        if all(float(number).is_integer() for number in numbers):
            return "integer-like (CSV strings; numeric parse succeeds)"
        return "numeric (CSV strings; numeric parse succeeds)"
    if len(profile["parsed"]) / len(present) >= 0.8:
        return f"mixed; numeric-like ({len(profile['parsed'])}/{len(present)} present values parse)"
    return "categorical/text (CSV strings)"


def duplicate_summary(rows: list[dict[str, str]], columns: list[str]) -> dict[str, Any]:
    counts = Counter(tuple(row.get(column, "") for column in columns) for row in rows)
    groups = [(key, count) for key, count in counts.items() if count > 1]
    return {
        "groups": len(groups),
        "extra_rows": sum(count - 1 for _, count in groups),
        "examples": groups[:8],
    }


def candidate_key_summary(
    rows: list[dict[str, str]], columns: list[str], *, weak: bool = False
) -> dict[str, Any]:
    counts: Counter[tuple[str, ...]] = Counter()
    incomplete = 0
    for row in rows:
        values = tuple((row.get(column) or "").strip() for column in columns)
        has_incomplete_component = any(
            is_missing(value) or value.strip().casefold() in PLACEHOLDER_TOKENS
            for value in values
        )
        if has_incomplete_component:
            incomplete += 1
            # Blank-key strong candidates are too ambiguous to group. Keep
            # literal sentinels such as N/A/Unknown as raw key values so the
            # audit does not silently decide what those tokens mean.
            if not weak and any(is_blank(value) for value in values):
                continue
        key = tuple(normalize_category(value) if value else "<missing>" for value in values)
        counts[key] += 1
    groups = [(key, count) for key, count in counts.items() if count > 1]
    groups.sort(key=lambda item: (-item[1], item[0]))
    return {
        "key": columns,
        "groups": len(groups),
        "extra_rows": sum(count - 1 for _, count in groups),
        "incomplete_rows": incomplete,
        "examples": groups[:8],
    }


def categorical_review(column: str, values: list[str]) -> dict[str, Any]:
    counts = Counter(value for value in values if not is_blank(value))
    normalized: dict[str, set[str]] = defaultdict(set)
    for raw in counts:
        normalized[normalize_category(raw)].add(raw)
    variants = [sorted(items) for items in normalized.values() if len(items) > 1]
    whitespace = [(value, count) for value, count in counts.items() if value != value.strip() or re.search(r"\s{2,}", value)]
    placeholders = [(value, count) for value, count in counts.items() if value.strip().casefold() in PLACEHOLDER_TOKENS - {""}]

    # Fuzzy matching is a review aid, never an automatic spelling correction.
    # Cap at the 400 most frequent values per column to keep the audit bounded.
    ranked_values = [value for value, _ in counts.most_common(400)]
    fuzzy: list[tuple[str, str, float]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for index, left in enumerate(ranked_values):
        left_norm = normalize_category(left)
        for right in ranked_values[index + 1 :]:
            right_norm = normalize_category(right)
            if left_norm == right_norm or not left_norm or not right_norm:
                continue
            if left_norm[0] != right_norm[0] or abs(len(left_norm) - len(right_norm)) > 2:
                continue
            ratio = difflib.SequenceMatcher(None, left_norm, right_norm).ratio()
            if ratio >= 0.92:
                pair = tuple(sorted((left, right)))
                if pair not in seen_pairs:
                    fuzzy.append((pair[0], pair[1], ratio))
                    seen_pairs.add(pair)
    fuzzy.sort(key=lambda row: (-row[2], row[0].casefold(), row[1].casefold()))
    return {
        "unique_nonmissing": len(counts),
        "placeholders": placeholders,
        "whitespace": whitespace,
        "case_or_space_variants": variants,
        "fuzzy_candidates": fuzzy[:40],
        "fuzzy_values_checked": len(ranked_values),
        "fuzzy_truncated": len(counts) > len(ranked_values),
        "frequent_values": counts.most_common(15),
    }


def date_profile(rows: list[dict[str, str]], column: str) -> dict[str, Any]:
    values = [(row.get(column) or "").strip() for row in rows]
    nonempty = [value for value in values if value]
    valid_iso: list[date] = []
    valid_other: list[tuple[str, date]] = []
    invalid: Counter[str] = Counter()
    time_stripped: Counter[str] = Counter()
    patterns: Counter[str] = Counter()
    default_jan1 = Counter()
    default_dec31 = Counter()
    for original in nonempty:
        candidate = original.strip().rstrip(";").strip()
        if candidate != original:
            time_stripped[original] += 1
        if not candidate:
            patterns["delimiter-only / empty after trimming semicolons"] += 1
            continue
        if re.fullmatch(r"\d{4}", candidate):
            patterns["year-only"] += 1
            try:
                valid_other.append((original, date(int(candidate), 1, 1)))
            except ValueError:
                invalid[original] += 1
            continue
        if re.fullmatch(r"\d{4}-\d{2}", candidate):
            patterns["year-month"] += 1
            try:
                valid_other.append((original, date.fromisoformat(candidate + "-01")))
            except ValueError:
                invalid[original] += 1
            continue
        try:
            parsed = date.fromisoformat(candidate)
            valid_iso.append(parsed)
            patterns["ISO full date"] += 1
            if parsed.month == 1 and parsed.day == 1:
                default_jan1[parsed.year] += 1
            if parsed.month == 12 and parsed.day == 31:
                default_dec31[parsed.year] += 1
            continue
        except ValueError:
            pass
        parsed_other = None
        for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%Y.%m.%d"):
            try:
                parsed_other = datetime.strptime(candidate, fmt).date()
                break
            except ValueError:
                continue
        if parsed_other:
            valid_other.append((original, parsed_other))
            patterns["non-ISO parsed date"] += 1
        else:
            invalid[original] += 1
            patterns["unparsed / invalid"] += 1
    all_dates = valid_iso + [parsed for _, parsed in valid_other]
    return {
        "rows": len(rows),
        "empty": len(rows) - len(nonempty),
        "nonempty": len(nonempty),
        "iso_full_dates": len(valid_iso),
        "other_parsed_dates": len(valid_other),
        "invalid_count": sum(invalid.values()),
        "patterns": patterns,
        "invalid_examples": invalid.most_common(10),
        "values_with_trailing_semicolons": time_stripped.most_common(10),
        "default_jan1_years": default_jan1.most_common(15),
        "default_dec31_years": default_dec31.most_common(15),
        "min": min(all_dates) if all_dates else None,
        "max": max(all_dates) if all_dates else None,
    }


def audit_dataset(path: Path) -> dict[str, Any]:
    columns, rows = read_dataset(path)
    dataset = path.name
    missing = {}
    unique = {}
    types = {}
    numeric = {}
    categorical = {}
    for column in columns:
        values = [row.get(column, "") or "" for row in rows]
        blank_values = sum(is_blank(value) for value in values)
        candidate_tokens = Counter(
            value.strip() for value in values
            if not is_blank(value) and value.strip().casefold() in MISSING_TOKENS
        )
        candidate_missing = blank_values + sum(candidate_tokens.values())
        missing[column] = {
            "count": candidate_missing,
            "percentage": fmt_pct(candidate_missing, len(rows)),
            "blank_count": blank_values,
            "blank_percentage": fmt_pct(blank_values, len(rows)),
            "candidate_tokens": candidate_tokens,
        }
        raw_counts = Counter(value for value in values if not is_blank(value))
        unique[column] = {"count": len(raw_counts), "examples": raw_counts.most_common(30)}
        types[column] = field_type(values, column)
        number_profile = numeric_profile(values)
        if number_profile["present"] and len(number_profile["parsed"]) / number_profile["present"] >= 0.8:
            vals = number_profile["parsed"]
            q1, q3 = _quartiles(vals)
            iqr = q3 - q1
            low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outliers = [value for value in vals if value < low or value > high]
            numeric[column] = {
                "present": number_profile["present"],
                "parsed": len(vals),
                "parse_failures": number_profile["parse_failures"],
                "min": min(vals),
                "max": max(vals),
                "mean": statistics.fmean(vals),
                "median": statistics.median(vals),
                "q1": q1,
                "q3": q3,
                "iqr_fences": [low, high],
                "iqr_outlier_count": len(outliers),
                "iqr_outlier_examples": sorted(outliers)[:5] + (sorted(outliers)[-5:] if len(outliers) > 5 else []),
            }
        if column in _categorical_columns(dataset, columns):
            categorical[column] = categorical_review(column, values)

    exact = duplicate_summary(rows, columns)
    if dataset == "vgsales.csv":
        strong_key = candidate_key_summary(rows, ["Name", "Platform", "Year", "Genre", "Publisher"])
        weak_key = candidate_key_summary(rows, ["Name", "Platform"], weak=True)
    else:
        strong_key = candidate_key_summary(rows, ["title", "console", "release_date"])
        weak_key = candidate_key_summary(rows, ["title", "console"], weak=True)

    sales = _sales_checks(dataset, rows)
    dates = {}
    if dataset == "vgchartz-2024.csv":
        for column in ("release_date", "last_update;;"):
            if column in columns:
                dates[column] = date_profile(rows, column)
    year = _year_checks(dataset, rows, columns)
    return {
        "path": path,
        "rows": rows,
        "columns": columns,
        "row_count": len(rows),
        "column_count": len(columns),
        "types": types,
        "missing": missing,
        "unique": unique,
        "numeric": numeric,
        "categorical": categorical,
        "exact_duplicates": exact,
        "potential_duplicates": {"strong_key": strong_key, "weak_key": weak_key},
        "sales_checks": sales,
        "date_checks": dates,
        "year_checks": year,
        "sha256": source_fingerprint(path),
    }


def _quartiles(values: list[float]) -> tuple[float, float]:
    if len(values) == 1:
        return values[0], values[0]
    q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return q1, q3


def _categorical_columns(dataset: str, columns: list[str]) -> set[str]:
    known = {
        "vgsales.csv": {"Name", "Platform", "Genre", "Publisher"},
        "vgchartz-2024.csv": {"img", "title", "console", "genre", "publisher", "developer"},
    }
    return known.get(dataset, set(columns))


def _sales_checks(dataset: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    fields = SALES_COLUMNS[dataset]
    present = [field for field in fields if any(field in row for row in rows)]
    per_field = {}
    for field in present:
        values = [parse_number(row.get(field)) for row in rows]
        parsed = [value for value in values if value is not None]
        per_field[field] = {
            "parsed_count": len(parsed),
            "negative_count": sum(value < 0 for value in parsed),
            "zero_count": sum(value == 0 for value in parsed),
            "min": min(parsed) if parsed else None,
            "max": max(parsed) if parsed else None,
        }
    if dataset == "vgsales.csv":
        region_fields = ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]
        total_field = "Global_Sales"
    else:
        region_fields = ["na_sales", "jp_sales", "pal_sales", "other_sales"]
        total_field = "total_sales"
    complete = []
    for row in rows:
        vals = [parse_number(row.get(field)) for field in region_fields]
        total = parse_number(row.get(total_field))
        if total is not None and all(value is not None for value in vals):
            complete.append((total, sum(vals)))
    diffs = [total - regional for total, regional in complete]
    mismatch = [diff for diff in diffs if abs(diff) > 1e-9]
    return {
        "fields": per_field,
        "total_field": total_field,
        "regions": region_fields,
        "complete_region_total_rows": len(complete),
        "exact_region_sum_matches": len(diffs) - len(mismatch),
        "nonmatching_rows": len(mismatch),
        "maximum_absolute_difference": max(map(abs, diffs)) if diffs else None,
        "negative_sales_examples": [
            (index + 2, field, row.get(field))
            for index, row in enumerate(rows)
            for field in present
            if (value := parse_number(row.get(field))) is not None and value < 0
        ][:10],
        "rows_total_below_any_reported_region_sum": sum(total + 1e-9 < regional for total, regional in complete),
    }


def _year_checks(dataset: str, rows: list[dict[str, str]], columns: list[str]) -> dict[str, Any]:
    if dataset == "vgsales.csv":
        column = "Year"
        if column not in columns:
            return {}
        raw = [(row.get(column) or "").strip() for row in rows]
        invalid = Counter(value for value in raw if value and not re.fullmatch(r"\d{4}", value))
        years = [int(value) for value in raw if re.fullmatch(r"\d{4}", value)]
        return {
            "field": column,
            "empty_count": sum(not value for value in raw),
            "non_year_values": invalid.most_common(15),
            "parsed_year_count": len(years),
            "min_year": min(years) if years else None,
            "max_year": max(years) if years else None,
            "before_1970_count": sum(year < 1970 for year in years),
            "after_2026_count": sum(year > 2026 for year in years),
            "note": "1970 and 2026 bounds are audit flags only, not rules for dropping records.",
        }
    return {}


def render_dataset(report: dict[str, Any]) -> list[str]:
    name = report["path"].name
    rows = report["rows"]
    lines = [f"## {name}", "", f"- **Source file:** `{Path(report['path']).name}`", f"- **SHA-256:** `{report['sha256']}`", f"- **Rows:** {report['row_count']:,}", f"- **Columns:** {report['column_count']}", "", "### Columns, inferred data types, missingness, and unique values", "", "Unique-value examples are capped at 30 per column; the unique count includes all nonempty raw values, including null-like and placeholder tokens. CSV parsing initially reads fields as text; inferred types below describe parseability, not modifications. The combined candidate-missing count treats blanks and common null-like spellings as candidates for review only; it is not a final cleaning classification.", "", "| Column | Inferred type | Blank cells | Blank % | Candidate null-like tokens | Candidate missing % | Unique nonempty raw values | Value examples (up to 30) |", "|---|---|---:|---:|---|---:|---:|---|"]
    for column in report["columns"]:
        missing = report["missing"][column]
        values = report["unique"][column]["examples"]
        examples = ", ".join(f"{value!r} ({count})" for value, count in values) or "—"
        token_summary = ", ".join(f"{value!r}: {count:,}" for value, count in missing["candidate_tokens"].most_common()) or "none"
        lines.append(f"| `{markdown_cell(column)}` | {markdown_cell(report['types'][column])} | {missing['blank_count']:,} | {missing['blank_percentage']} | {markdown_cell(token_summary)} | {missing['percentage']} | {report['unique'][column]['count']:,} | {markdown_cell(examples)} |")
    lines += ["", "### Numeric ranges and potential outliers", "", "Potential outliers use the conventional 1.5 × IQR fence. This is a screening flag, not proof of error; strongly skewed sales and rank data can naturally produce many flags.", "", "| Column | Parsed / present | Parse failures | Min | Q1 | Median | Q3 | Max | IQR flags |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for column, stats in report["numeric"].items():
        lines.append(f"| `{column}` | {stats['parsed']:,} / {stats['present']:,} | {stats['parse_failures']:,} | {fmt_number(stats['min'])} | {fmt_number(stats['q1'])} | {fmt_number(stats['median'])} | {fmt_number(stats['q3'])} | {fmt_number(stats['max'])} | {stats['iqr_outlier_count']:,} |")
    lines += ["", "| Column | IQR fence | Outlier examples (smallest/largest) |", "|---|---:|---|"]
    for column, stats in report["numeric"].items():
        examples = ", ".join(fmt_number(value) for value in stats["iqr_outlier_examples"]) or "—"
        lines.append(f"| `{column}` | [{fmt_number(stats['iqr_fences'][0])}, {fmt_number(stats['iqr_fences'][1])}] | {examples} |")
    lines += ["", "### Categorical consistency review", "", "Placeholder labels are reported separately from empty/missing tokens. Fuzzy spelling candidates are generated from at most the 400 most frequent values per column and need human review; no labels were normalized by this audit.", ""]
    for column, result in report["categorical"].items():
        lines.append(f"#### `{column}`")
        lines.append(f"- Placeholder values: {', '.join(f'{value!r} ({count})' for value, count in result['placeholders']) or 'none detected'}.")
        lines.append(f"- Whitespace anomalies: {', '.join(f'{value!r} ({count})' for value, count in result['whitespace']) or 'none detected'}.")
        lines.append(f"- Case/whitespace-equivalent raw variants: {('; '.join(' / '.join(repr(v) for v in group) for group in result['case_or_space_variants'][:30])) or 'none detected'}.")
        if len(result["case_or_space_variants"]) > 30:
            lines.append(f"  - {len(result['case_or_space_variants']) - 30} additional variant groups omitted from this report section.")
        lines.append(f"- Possible spelling variants (similarity ≥ 0.92): {('; '.join(f'{a!r} / {b!r} ({score:.2f})' for a, b, score in result['fuzzy_candidates']) or 'none detected in the checked values')}.")
        if result["fuzzy_truncated"]:
            lines.append(f"- Fuzzy scan was limited to the {result['fuzzy_values_checked']} most frequent values of {result['unique_nonmissing']:,}; less frequent values were not compared.")
        lines.append("")
    lines += ["### Exact duplicate rows and potential duplicate games", "", f"- Exact full-row duplicate groups: **{report['exact_duplicates']['groups']:,}**; additional repeated rows: **{report['exact_duplicates']['extra_rows']:,}**."]
    for label, item in (("Strong candidate key", report["potential_duplicates"]["strong_key"]), ("Weak candidate key", report["potential_duplicates"]["weak_key"])):
        lines.append(f"- {label} `{', '.join(item['key'])}`: {item['groups']:,} repeated groups / {item['extra_rows']:,} additional rows; {item['incomplete_rows']:,} rows have at least one incomplete/placeholder key component.")
        if item["examples"]:
            lines.append("  - Examples: " + "; ".join(f"{key!r} × {count}" for key, count in item["examples"]))
    lines += ["", "These keys identify review candidates, not confirmed duplicates. Ports, editions, release variants, and missing identifiers can produce legitimate repeated keys. No rows were removed.", "", "### Year and date quality", ""]
    year = report["year_checks"]
    if year:
        lines += [f"- Field `{year['field']}`: {year['parsed_year_count']:,} four-digit year values, range {year['min_year']}–{year['max_year']}; {year['empty_count']:,} empty and non-year values: {year['non_year_values'] or 'none'}.", f"- Years before 1970: {year['before_1970_count']}; after 2026: {year['after_2026_count']}. {year['note']}", ""]
    if report["date_checks"]:
        for column, dates in report["date_checks"].items():
            lines += [f"#### `{column}`", f"- Nonempty values: {dates['nonempty']:,}; empty values: {dates['empty']:,}; ISO full dates: {dates['iso_full_dates']:,}; parsed non-ISO/year-only values: {dates['other_parsed_dates']:,}; invalid/unparsed: {dates['invalid_count']:,}.", f"- Detected forms: {dict(dates['patterns'])}.", f"- Parsed range: {dates['min'] or 'n/a'} to {dates['max'] or 'n/a'}.", f"- Frequent Jan 1 dates by year (possible year-only placeholders): {dates['default_jan1_years'] or 'none'}.", f"- Frequent Dec 31 dates by year (possible year-only placeholders): {dates['default_dec31_years'] or 'none'}.", f"- Raw values with trailing semicolons: {dates['values_with_trailing_semicolons'] or 'none'}.", f"- Invalid examples: {dates['invalid_examples'] or 'none'}.", ""]
        lines.append("ISO syntax validates the calendar date, not the accuracy or precision of the source date. Concentrations at January 1 or December 31 can indicate a year-only value encoded as a full date and require source documentation.")
        lines.append("")
    lines += ["### Sales validity and reconciliation checks", "", "| Field | Numeric rows | Negative | Zero | Min | Max |", "|---|---:|---:|---:|---:|---:|"]
    for column, stats in report["sales_checks"]["fields"].items():
        lines.append(f"| `{column}` | {stats['parsed_count']:,} | {stats['negative_count']:,} | {stats['zero_count']:,} | {fmt_number(stats['min'])} | {fmt_number(stats['max'])} |")
    sales = report["sales_checks"]
    lines += ["", f"- Rows with total and every regional field present: {sales['complete_region_total_rows']:,}.", f"- Regional sums exactly equal total: {sales['exact_region_sum_matches']:,}; nonmatching: {sales['nonmatching_rows']:,}; maximum absolute difference: {fmt_number(sales['maximum_absolute_difference']) if sales['maximum_absolute_difference'] is not None else 'n/a'}.", f"- Rows whose total is below the sum of all reported regions: {sales['rows_total_below_any_reported_region_sum']:,}.", f"- Negative sales examples: {sales['negative_sales_examples'] or 'none detected'}.", "- Sales greater than zero are not assumed to be valid solely because they are nonnegative. Units, rounding, and source methodology should be confirmed.", ""]
    return lines


def schema_comparison(reports: list[dict[str, Any]]) -> list[str]:
    left, right = reports
    a, b = set(left["columns"]), set(right["columns"])
    right_casefold = {column.casefold(): column for column in right["columns"]}
    casefold_matches = [
        (column, right_casefold[column.casefold()])
        for column in left["columns"]
        if column.casefold() in right_casefold and column != right_casefold[column.casefold()]
    ]
    lines = ["## Schema comparison and potential matching", "", "| Aspect | `vgsales.csv` | `vgchartz-2024.csv` |", "|---|---|---|"]
    lines.append(f"| Columns | {', '.join(f'`{column}`' for column in left['columns'])} | {', '.join(f'`{column}`' for column in right['columns'])} |")
    lines.append(f"| Exact same-name columns | {', '.join(f'`{column}`' for column in sorted(a & b)) or 'none'} | {', '.join(f'`{column}`' for column in sorted(a & b)) or 'none'} |")
    lines.append(f"| Case-insensitive header matches | {', '.join(f'`{one}` / `{two}`' for one, two in casefold_matches) or 'none'} | {', '.join(f'`{one}` / `{two}`' for one, two in casefold_matches) or 'none'} |")
    lines.append(f"| Only in this dataset | {', '.join(f'`{column}`' for column in sorted(a - b)) or 'none'} | {', '.join(f'`{column}`' for column in sorted(b - a)) or 'none'} |")
    lines += ["", "### Potential matching keys (not a merge recommendation)", "", "- **Game title:** `Name` ↔ `title` is a possible fuzzy candidate after documented whitespace/case/punctuation normalization. Titles may differ by edition, subtitle, localization, or franchise naming; collisions need manual review.", "- **Platform/console:** `Platform` ↔ `console` is a possible categorical mapping, not a guaranteed direct key. Alias tables and one-to-many cases need review.", "- **Publisher:** `Publisher` ↔ `publisher` is a possible reviewed entity mapping; imprints, subsidiaries, spelling, and unknown labels make direct equality unreliable.", "- **Genre:** `Genre` ↔ `genre` may be comparable after exact category review, but does not identify a game.", "- **Year/date:** `Year` could be compared with the year portion of `release_date` only after date provenance and precision are understood. It is not an exact key.", "- A defensible candidate record identity would need title + mapped platform/console and possibly release year/date, with duplicate/edition resolution. Neither file shows a verified shared game ID in the inspected schemas.", "", "### Columns that must remain source-specific unless a mapping is justified", "", "- Sales totals and regional fields: `Global_Sales` ↔ `total_sales`; `NA_Sales` ↔ `na_sales`; `JP_Sales` ↔ `jp_sales`; `Other_Sales` ↔ `other_sales`; and especially `EU_Sales` ↔ `pal_sales` are not assumed equivalent.", "- `Platform` and `console` are separate source classifications until mapped.", "- `Year`, `release_date`, and `last_update;;` represent different concepts; do not join them as equivalent date fields.", "- `Rank` is a source-specific ordinal and must not be merged with game identity or interpreted as a comparable rank across files.", "- `img`, `developer`, `critic_score`, and `last_update;;` have no direct counterpart in `vgsales.csv` and remain supplemental source fields.", "- `Name`/`title`, `Publisher`/`publisher`, and `Genre`/`genre` are candidate correspondences only, not columns to concatenate or coalesce without review.", "", "**Recommendation:** do not merge the datasets for the assignment’s required analyses. Keep source-level outputs separate. Any future matching exercise should be an explicit, auditable supplemental analysis with confidence flags and unmatched/ambiguous counts.", ""]
    return lines


def missing_strategy_section() -> list[str]:
    return ["## Missing values: strategies to evaluate, no policy selected", "", "This audit distinguishes empty cells, candidate null-like spellings (`N/A`, `NA`, `null`, `None`, `NaN`, `<NA>`), and placeholder categories such as `Unknown`, `-`, and `TBD`. Whether an individual token denotes missingness or a literal category remains a data-policy decision. The report does not choose a strategy or alter values. Before cleaning, document a field-specific decision and its rationale.", "", "Possible options include:", "", "1. **Retain as missing and report coverage.** Suitable when imputation would invent sales, score, year, or publisher information; use metric-specific complete-case denominators.", "2. **Impute only with a defensible domain method.** Document method, training/cohort boundaries, and an imputation flag. Avoid imputing sales or critic scores without strong justification.", "3. **Exclude rows for a particular metric only.** Keep the row in other analyses and publish each metric’s eligible row count; do not globally drop rows because one field is absent.", "4. **Keep unknown categories distinct.** Treat `Unknown`, `TBD`, and blank as separate raw states until provenance establishes that they mean the same thing. A display label such as “Unspecified” can be produced without overwriting source data.", "5. **Resolve or drop duplicate candidates only after review.** Compare all fields and source identity; document removed rows and retain an audit trail.", "", "No missing-value, duplicate, spelling, or outlier policy has been selected by this audit.", ""]


def build_report(reports: list[dict[str, Any]]) -> str:
    lines = ["# GameScope Data Audit", "", f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}", "", "## Scope and method", "", "This report is generated by `python/data_audit.py` using Python’s standard library. The source CSV files were read only. No cleaning, imputation, spelling correction, row removal, or merge was performed.", "", "- Blank cells and explicit null-like spellings are reported separately. A combined candidate-missing percentage is shown for review only; it is not a final classification.", "- Placeholder categories (`Unknown`, `TBD`, `-`, etc.) are reported as observed values, not silently converted to missing.", "- CSV-inferred types are parseability-based; the raw CSV reader returns strings and this audit does not cast or write data.", "- Numeric outliers are screening flags from 1.5 × IQR fences, not error labels.", "- Potential duplicate game keys and fuzzy category variants are review candidates, not confirmed errors.", "- Dates are assessed both for parseability and patterns that may indicate imprecise placeholder dates.", ""]
    for report in reports:
        lines.extend(render_dataset(report))
    lines.extend(schema_comparison(reports))
    lines.extend(missing_strategy_section())
    lines += ["## Reproducibility", "", "Run from the repository root with `python python/data_audit.py`. The script prefers `data/raw/<filename>` when present and otherwise uses the CSV in the project root. SHA-256 hashes above identify the exact files inspected.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Project root (defaults to this script's parent project).")
    parser.add_argument("--output", type=Path, default=None, help="Report path (defaults to reports/data-audit.md under the project root).")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve() if args.output else root / "reports" / "data-audit.md"
    reports = [audit_dataset(find_dataset(name, root)) for name in DATASETS]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_report(reports), encoding="utf-8")
    print(f"Audit complete: {output}")
    for report in reports:
        print(f"{report['path']}: {report['row_count']:,} rows × {report['column_count']} columns")


if __name__ == "__main__":
    main()
