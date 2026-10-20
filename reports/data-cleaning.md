# GameScope Data Cleaning Report

Pipeline run: 2026-10-20T13:37:01+02:00

## Scope

The pipeline reads each source independently and writes cleaned copies under `data/processed/`. Raw input files are never overwritten. No datasets are merged. Every processed row retains a 1-based `_source_row` reference to its original data row.

## Problems found and cleaning decisions

| Issue | Decision applied | Reason / limitation |
|---|---|---|
| Source schemas differ; vgchartz has a final header `last_update;;` and trailing `;;` in that field's values | Rename that one known header to `last_update`; strip trailing semicolons from that field only; log every changed cell/header | Explicit export artifact rule; the original raw file remains intact. Other fields are not renamed by guessed aliases. |
| Leading/trailing and repeated whitespace may occur in text and headers | Strip edges and collapse repeated internal whitespace in values; trim other headers only if needed; log changes | Preserve original case, punctuation, spelling, and substantive words. This does not resolve entity aliases. |
| Categorical casing, spelling, and placeholders can be meaningful or inconsistent | Do not case-fold, spell-correct, or merge categories. Preserve `N/A`, `Unknown`, `TBD`, `-`, and other nonblank labels in categorical fields | Use audit candidates for later, documented crosswalk decisions; unknown and missing remain distinct. |
| Blank fields and null-like tokens in numeric fields | Blank values and unparseable numeric tokens become nullable values; numeric `N/A`/similar tokens are logged as candidate missing; no imputation | Categorical `N/A` remains literal. A column-specific domain decision may later refine token meaning. |
| Numeric-looking CSV strings | Convert only schema-declared numeric columns to nullable `Int64`/`Float64` when pandas is installed; reject non-integral values in integer fields to missing and log them | No values are filled or rounded. CSV output is text; `cleaning_schema.json` records intended dtypes. |
| Date fields and imprecise/invalid values | Parse only ISO `YYYY-MM-DD`; strip the known vgchartz suffix first; invalid/delimiter-only values become missing and are logged | No inferred month/day, and no year-only date is fabricated. ISO syntax does not prove date precision. |
| Exact and potential game-key duplicates | Keep and flag records; write duplicate candidate groups to the JSONL audit log | Title/platform/year or release date may identify ports, editions, or separate releases. No row is silently removed. |
| Zero sales | Preserve numeric zero as zero | Zero is a reported value, not a missing-value marker. |

## Files produced

- Processed CSV files: `D:\VSC\University Projects\DataWrangling\data\processed`.
- Row-level transformation and duplicate log: `D:\VSC\University Projects\DataWrangling\data\processed\cleaning_audit.jsonl`.
- Run summary: `D:\VSC\University Projects\DataWrangling\data\processed\cleaning_summary.json`.
- Dtype/schema contract: `D:\VSC\University Projects\DataWrangling\data\processed\cleaning_schema.json`.
- Validation result: `D:\VSC\University Projects\DataWrangling\data\processed\validation_report.json`.

## Dataset results

### vgsales.csv

- Input: `D:\VSC\University Projects\DataWrangling\vgsales.csv` (16,598 rows, 11 columns).
- Output: `D:\VSC\University Projects\DataWrangling\data\processed\vgsales_clean.csv` (16,598 rows, 13 columns).
- Logged cell transformation events: 276; distinct source rows with at least one logged value change: 276.
- Field-level events: `{"Year": 271, "Name": 5}`.
- Numeric/date parse failures set to missing: `{"Year": 271}`.
- Candidate null-like numeric tokens set to missing: `{"Year": 271}`.
- Exact duplicate groups flagged: 0 (0 rows flagged).
- Potential game-key groups flagged: 1 (2 rows flagged); all retained.
- Rows removed: **0**.
- Validation: **passed**; errors: none; warnings: ['Duplicate candidates were flagged and retained; human review is needed before any removal.'].

### vgchartz-2024.csv

- Input: `D:\VSC\University Projects\DataWrangling\vgchartz-2024.csv` (64,016 rows, 14 columns).
- Output: `D:\VSC\University Projects\DataWrangling\data\processed\vgchartz_2024_clean.csv` (64,016 rows, 16 columns).
- Logged cell transformation events: 107,546; distinct source rows with at least one logged value change: 62,490.
- Field-level events: `{"last_update": 107398, "developer": 80, "title": 38, "img": 8, "publisher": 22}`.
- Numeric/date parse failures set to missing: `{}`.
- Candidate null-like numeric tokens set to missing: `{}`.
- Exact duplicate groups flagged: 0 (0 rows flagged).
- Potential game-key groups flagged: 142 (285 rows flagged); all retained.
- Rows removed: **0**.
- Validation: **passed**; errors: none; warnings: ['Duplicate candidates were flagged and retained; human review is needed before any removal.'].

## Validation

The pipeline verifies output existence and schema, row-count preservation, source-row sequence, duplicate flags, parseability of typed output values, ISO date validity, and source SHA-256 equality before and after the run. Sales negatives and duplicate candidates are surfaced for review rather than automatically removed. Regional/global sum differences are retained because rounding and source methodology are unresolved.

## Runtime limitation

The current environment does not have pandas installed, and the package index was unavailable during this run. Therefore this execution used the standard-library CSV fallback; it emitted the same nullable-value conventions and a schema contract with the intended pandas dtypes. Install `python/requirements.txt` to run the pandas backend, which applies pandas nullable `Int64`, `Float64`, `string`, and `datetime64[ns]` dtypes before CSV serialization. The backend used is recorded in `cleaning_summary.json`.

## Limitations

- CSV serialization does not itself persist pandas dtypes. Consumers should load with the accompanying schema or run the pipeline with pandas.
- Null-like token interpretation in numeric fields is conservative but still a documented choice; raw text is retained in the JSONL change log for every affected cell.
- Categorical variants and potential duplicate games are not automatically reconciled; no spelling/identity crosswalk is inferred.
- The datasets are not merged, and `EU_Sales` is not treated as interchangeable with `pal_sales`.
- This pipeline does not perform analytical calculations or produce dashboard assets.
