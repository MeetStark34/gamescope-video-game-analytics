# GameScope

Global video game sales intelligence built as a reproducible Python data pipeline and a source-aware Next.js dashboard. The required university analyses use `vgsales.csv`; `vgchartz-2024.csv` is analyzed separately for supplemental advanced work.

## Overview

GameScope inspects, cleans, validates, analyzes, and visualizes two video game sales datasets. Python is the source of truth for cleaning and analytical metrics. The dashboard presents prepared JSON outputs and provides lightweight filtering, search, sorting, and exploration in the browser.

Raw input CSVs are never edited by the pipeline. Cleaned tables, audit logs, and analytical exports are generated from those sources. The prepared dashboard snapshot in `dashboard/public/data/analytics/` is included so that the web app can build and run without Python or the source CSVs.

## Project objective

Deliver a reproducible, well-documented analysis of global video game sales, with transparent data-quality decisions, clearly scoped metrics, and an accessible interactive dashboard suitable for a static-data deployment on Vercel.

## University assignment requirements

The notebook and reports address dataset inspection, missing values, data types, duplicate detection, descriptive statistics, top games, annual releases and sales trends, genre and platform analysis, regional comparison, publisher analysis, visualization and storytelling, and conclusions about data-wrangling challenges. The custom Market Power Index and Regional Preference Divergence analyses are implemented in Python and documented with formulas. The assignment's primary results are computed from `vgsales.csv`.

## Features

- Repeatable cleaning with a row-level transformation log and validation report.
- Source-specific analytics and dashboard-ready JSON/CSV exports.
- Interactive dashboard filters, search, sortable tables, charts, and computed insight cards.
- Dedicated Market Power, Regional Divergence, Advanced Analysis, and Data Quality views.
- Accessible responsive interface with reduced-motion support.
- A checked-in prepared dashboard data snapshot for deployment without Python.

## Datasets

| File | Rows | Role | Notes |
|---|---:|---|---|
| `vgsales.csv` | 16,598 | Primary assignment dataset | 11 source columns; 271 `Year` entries are `N/A`. Used for all core assignment analyses and custom primary-source metrics. |
| `vgchartz-2024.csv` | 64,016 | Supplemental dataset | Different schema and coverage; critic scores and sales are jointly available for 4,043 valid records. Used only for the Advanced Analysis. |

Obtain the CSVs from the course materials or their original distributors and review their terms before redistribution. Put them in `data/raw/` using the exact filenames above. For compatibility with the current project checkout, the pipeline also discovers same-named CSVs in the project root. Both locations are ignored by Git. The project does not require the source CSVs to run the deployed dashboard.

The datasets are **not blindly merged**. `vgsales.csv` uses `Platform`, `EU_Sales`, and `Global_Sales`; the supplemental file uses `console`, `pal_sales`, and `total_sales`. Their classifications, regional definitions, and population coverage are not assumed to be interchangeable.

## Data pipeline

The pipeline is split into cleaning/validation and analytics export stages:

1. Read source CSVs as text, preserving source values and row order.
2. Write cleaned copies and an audit log under `data/processed/`.
3. Validate row counts, schema, parseability, duplicates, source-row references, and raw-file hashes.
4. Generate primary and supplemental analytics independently under `data/processed/analytics/`.
5. Copy dashboard-consumed JSON into `dashboard/public/data/analytics/` when the prepared Python outputs are available.

The last directory is the deployable static snapshot. `npm run build` can use it directly when Python and raw data are absent; it does not install or invoke Python on Vercel.

## Data cleaning

Cleaning is conservative and documented in [reports/data-cleaning.md](reports/data-cleaning.md). No source rows are silently removed; exact and potential duplicates are flagged and retained. Blank or invalid numeric/date values become missing in processed data, with transformation events recorded. Numeric zero stays zero. Categorical spelling, case, and placeholders such as `Unknown`, `N/A`, and `TBD` are not merged or corrected automatically. Dates are parsed only when the source representation is a valid ISO date; no date precision is inferred. Raw CSVs remain unchanged.

## Exploratory data analysis

The assignment notebook is [analysis/video_game_analysis.ipynb](analysis/video_game_analysis.ipynb). It explores the primary dataset with explanatory text and visualizations. Its source and coverage decisions are supported by [reports/data-audit.md](reports/data-audit.md) and the cleaning report.

## Market Power Index

For each primary-source publisher, the index combines five normalized components: overall publisher sales share, normalized genre leadership coverage, genre diversity, regional consistency, and hit rate. Genre leadership uses the specified strict `>30%` genre market-share threshold. The final score is the equal-weight arithmetic mean of available components, scaled to 0–100; the report explains why equal weights are a neutral baseline and documents missing-component handling. It is an analytical summary, not a legal or causal measure of market power.

## Regional Divergence

Primary-source regional divergence uses total-variation distance between each eligible game's four-region sales mix and the complete-case overall regional baseline. Genre-region affinity compares a genre's sales share in a region with its global genre share. Time-series divergence, preference stability, and cultural-specificity screens are also exported. These measures describe sales patterns; they do not prove cultural causes or preferences.

## Advanced analysis

The supplemental dataset is used separately to study critic-score/sales association, developer and publisher summaries, console evolution, recent trends, and release-date patterns. Current date parsing finds 55,564 valid ISO release dates, including 4,871 January 1 records that may represent imprecise dates. Critic-score/sales statistics use only eligible paired records and are described as associations, not causation. See [reports/advanced-analysis.md](reports/advanced-analysis.md) for formulas, cohort sizes, and limitations.

## Dashboard

The Next.js application lives in [`dashboard/`](dashboard/). It includes Overview, Market Trends, Genre, Platform, Regional, Publisher, Market Power, Regional Divergence, Advanced Analysis, and Data Quality pages. The frontend consumes prepared JSON and performs only presentation-level filtering and interaction; it does not reimplement the Python analytics.

## Architecture

```text
Source CSVs (local, ignored)
          |
          v
Python loading, cleaning, validation
          |
          +--> cleaned CSVs + audit/report (generated locally)
          |
          v
Python analytics/export pipeline
          |
          +--> data/processed/analytics (generated locally)
          |
          v
dashboard/public/data/analytics (prepared static snapshot)
          |
          v
Next.js presentation and Vercel deployment
```

## Folder structure

```text
.
├── analysis/                   # University EDA notebook
├── data/
│   ├── raw/                    # Local source datasets; ignored by Git
│   └── processed/              # Generated cleaned data and analytics; ignored
├── dashboard/
│   ├── app/                    # Next.js routes, layout, and design system
│   ├── components/             # Reusable charts, filters, tables, and sections
│   ├── lib/                    # Analytics access, types, and view interactions
│   ├── public/data/analytics/  # Prepared deployable JSON snapshot
│   └── scripts/                # Local snapshot synchronization
├── python/                     # Audit, cleaning, validation, metrics, exporters
└── reports/                    # Data audit, cleaning decisions, and methodology
```

## Technologies

- Python 3.10+; pandas and matplotlib for the notebook/cleaning environment; Jupyter.
- Next.js 16, React 19, TypeScript, Tailwind CSS 4, Recharts, and Lucide React.
- Node.js 20.9 or newer for Next.js 16.

## Installation

Install Python and Node.js, clone the repository, and obtain the two source CSVs from the approved course/source location. Keep the CSVs local; the project `.gitignore` excludes them. On Windows PowerShell, commands below use the Python launcher (`py`) and work without activating the virtual environment.

## Python setup

From the project root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Place the source files at `data/raw/vgsales.csv` and `data/raw/vgchartz-2024.csv`. The current project-root copies are also detected during local development.

## Running the data pipeline

Run from the project root:

```powershell
py -3 -m python.data_audit
py -3 -m python.pipeline
py -3 -m python.analytics_pipeline
```

The audit writes `reports/data-audit.md`. Cleaning writes validated processed tables, schema/summary metadata, and a JSONL audit log under `data/processed/`; the analytics stage generates exports under `data/processed/analytics/`. To refresh the dashboard's local static copy, run:

```powershell
Set-Location dashboard
npm run sync:data
Set-Location ..
```

The dashboard pre-dev and pre-build hooks also sync available prepared analytics automatically.

## Running the Jupyter notebook

After installing requirements and generating cleaned data:

```powershell
py -3 -m jupyter lab analysis/video_game_analysis.ipynb
```

Select the `.venv` Python kernel if using Jupyter from another installation. The notebook analyzes the primary cleaned dataset and does not merge in supplemental records.

## Running the dashboard

From the project root:

```powershell
Set-Location dashboard
npm ci
npm run dev
```

Open the local URL printed by Next.js. For a local production preview:

```powershell
npm run build
npm start
```

## Environment variables

No environment variables, API keys, or external services are required. [`.env.example`](.env.example) documents this. Do not put credentials, local paths, or private information into committed environment files.

## Development

The dashboard scripts are `npm run lint`, `npm run typecheck`, `npm run check`, and `npm run build`. `npm run sync:data` refreshes the app's static snapshot from `data/processed/analytics/` when available. Run Python from the repository root so the default input and output paths resolve correctly. Do not commit raw datasets, credentials, local environment files, or generated cleaning metadata containing machine-specific details.

## Production build

```powershell
Set-Location dashboard
npm ci
npm run lint
npm run typecheck
npm run build
```

The build uses the prepared JSON snapshot under `dashboard/public/data/analytics/`. A local build refreshes it from Python outputs if the latter exist. With only a fresh clone and the checked-in snapshot, the build remains Node-only and does not require raw data or server-side Python.

## Vercel deployment

Create a Vercel project connected to the repository and configure:

| Setting | Value |
|---|---|
| Framework preset | Next.js |
| Root directory | `dashboard` |
| Install command | `npm ci` (or Vercel's detected npm install command) |
| Build command | `npm run build` |
| Output directory | Leave the Next.js default |
| Environment variables | None required |

Ensure the repository includes `dashboard/public/data/analytics/*.json`; these static assets are sufficient for deployment. The build does not require local Windows paths, the source CSV files, or Python. Do not enable static export or add a Python runtime for this dashboard. Next.js 16 requires Node.js 20.9 or newer; select a supported Vercel Node version meeting that minimum. For an optional local CLI deployment, run `npx vercel` from `dashboard/` after linking the intended Vercel project. See [Vercel's monorepo root-directory guidance](https://vercel.com/docs/monorepos/monorepo-faq) and [Next.js installation requirements](https://nextjs.org/docs/pages/getting-started/installation).

## Data methodology

Each source is read and analyzed independently. Missing numeric values are not imputed, unknown labels remain distinct from blanks, zero remains numeric zero, and potential game duplicates are flagged rather than removed. Aggregate outputs document their source, eligibility, and coverage. The browser snapshot is a generated presentation input and is not a substitute for the raw sources or pipeline.

## Analytical formulas

- **Genre market share:** publisher global sales in a genre divided by all valid global sales in that genre.
- **Genre leadership:** strict share greater than 0.30; leadership coverage is the number of genres led divided by all observed genres.
- **Genre diversity:** publisher's represented genre count divided by all observed genres.
- **Regional consistency:** `clip(1 - population_sd(four regional publisher shares) / (sqrt(3)/4), 0, 1)` using records complete in all four regions.
- **Hit rate:** publisher records whose valid global sales strictly exceed their genre median, divided by its eligible records.
- **Market Power Index:** `100 × arithmetic_mean(available components)` over overall sales share, genre leadership coverage, genre diversity, regional consistency, and hit rate. Equal weights are used because the assignment provides no evidence for privileging a component; unavailable components are omitted and their coverage is reported.
- **Regional divergence:** total variation distance `0.5 × sum_r |game_share_r - baseline_share_r|` across North America, Europe, Japan, and Other.
- **Genre-region affinity:** regional genre sales share divided by global genre sales share; 1 is baseline, values above/below 1 indicate over-/under-indexing.
- **Critic-score/sales analysis:** Pearson, Spearman, and log1p-sales Pearson associations for records with valid score and nonnegative sales; association does not establish causation.

Definitions, formulas, and edge-case rules are documented in [reports/advanced-analysis.md](reports/advanced-analysis.md).

## Limitations

- Source definitions, collection methods, and record coverage differ; cross-source pooling is not justified by the available metadata.
- The primary dataset has 271 missing release years and no exact release dates.
- The supplemental dataset has substantial missing score and sales coverage; critic-score analyses use a small eligible subset.
- January 1 release dates may encode year-only precision; the date string alone cannot confirm the original precision.
- Literal publisher/developer labels are not entity-resolved; aliases and subsidiaries may be split.
- Sales totals and regional components can differ slightly due to source rounding/methodology.
- Dataset redistribution rights must be checked with the course or source provider before publishing data files.

## Key findings

Findings below describe the current generated outputs and should be refreshed after rerunning the pipeline:

- The primary source has 16,598 records; the cleaning pipeline retains all rows and flags duplicate candidates for review.
- The current Market Power ranking starts with Nintendo (59.44), Electronic Arts (49.64), and Sony Computer Entertainment (48.99) under the documented equal-weight formula.
- Regional divergence is computable for 16,597 primary records; the documented concentrated-sales screen flags 6,524 records. This is a sales-concentration screen, not evidence of cultural cause.
- The supplemental source has 64,016 records, but critic-score/sales association uses 4,043 eligible pairs (6.32%). The current Pearson correlation is 0.284 for raw sales and 0.348 for log1p sales; neither implies causation.
- Of 55,564 valid supplemental release dates, 4,871 are January 1 and may be imprecise.

These are calculated results, not constants used by the frontend. See the generated methodology report for cohort details.

## Future improvements

- Add a versioned data dictionary and automated pipeline/schema checks in CI.
- Add alternate-weight sensitivity analysis for the Market Power Index.
- Improve entity resolution only with documented, reviewable mappings.
- Add accessible chart descriptions and keyboard-driven chart selection where supported.
- Add a documented data refresh workflow and source licensing record.

## Academic context

This repository supports a university data-wrangling and analytics assignment. It records methodology and data-quality decisions to make findings reviewable and reproducible. The student should confirm the instructor's requirements, cite the dataset providers and references, and add any required course attribution before submission or public release. No student names, IDs, or private course credentials are included here.

## License

No project license file is currently provided. Until the project owner selects and adds a license, the repository's original code and documentation remain subject to default copyright; this README does not grant reuse rights. Dataset rights are separate and governed by their respective providers. Confirm those terms before sharing data or a public deployment containing the prepared dashboard snapshot.
