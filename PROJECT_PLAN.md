# GameScope: Global Video Game Sales Intelligence

## Purpose and scope

This document is the technical architecture and staged implementation plan for GameScope. It covers both the university assignment and the proposed dashboard. This is planning only: no data cleaning, analytical pipeline, notebook, or dashboard has been implemented.

The assignment specification formally requires a Jupyter notebook with commented code, explanatory text, visualizations, and a short conclusion. `vgsales.csv` is the primary dataset for those required assignment analyses. `vgchartz-2024.csv` is supplemental and reserved for the project's Advanced Analysis unless an explicitly approved extension states otherwise. The dashboard is an additional project deliverable. Python is the source of truth for cleaning and calculations; Next.js presents prepared, versioned outputs and handles lightweight interaction.

## Current workspace and inspected inputs

The workspace currently contains `project_desc.pdf`, `vgsales.csv`, `vgchartz-2024.csv`, and this plan. There is no application scaffold, dependency manifest, or Git repository metadata. CSV inspection was read-only.

### `vgsales.csv`

- 16,598 rows and 11 columns: `Rank`, `Name`, `Platform`, `Year`, `Genre`, `Publisher`, `NA_Sales`, `EU_Sales`, `JP_Sales`, `Other_Sales`, `Global_Sales`.
- Numeric-looking columns parse as numbers; `Year` contains 271 literal `N/A` values (not empty fields). `Publisher` has 58 `N/A` and 203 `Unknown` labels.
- 12 genres, 31 platforms, 579 publisher strings; years parse from 1980 through 2020.
- No exact duplicate rows. A candidate key (`Name`, `Platform`, `Year`, `Genre`, `Publisher`) identifies 2 duplicate groups / 2 additional rows. These are candidates only; review before any deduplication.
- Regional sales sum exactly to `Global_Sales` for 12,087 rows; the largest difference across rows is 0.02. Do not overwrite global totals based on regional sums without source evidence.
- There is no release date; annual analyses rely on `Year` and must disclose missing years and source limitations.

### `vgchartz-2024.csv`

- 64,016 rows and 14 parsed columns: `img`, `title`, `console`, `genre`, `publisher`, `developer`, `critic_score`, `total_sales`, `na_sales`, `jp_sales`, `pal_sales`, `other_sales`, `release_date`, `last_update;;`.
- The last header is literally `last_update;;`; sample field values also end in `;;`. Treat normalization as a documented parser rule and preserve raw input unchanged.
- Missing fields: title, console, genre, publisher 1,533 each; developer 1,549; critic score 57,475; total sales 45,496; NA 51,670; JP 57,393; PAL 51,453; other 49,222; release date 8,452; final field 1,533.
- `publisher` contains 8,650 `Unknown`; `developer` contains 4,320 `Unknown` and 72 `TBD`. These sentinels are not blank strings and need explicit semantics.
- 20 observed genres, 80 console strings, and 3,265 publisher strings. Nonblank release dates parse as ISO dates; date precision/source conventions still need investigation.
- No exact duplicate rows. A case-normalized candidate key (`title`, `console`, `release_date`) flags 144 groups / 1,676 additional rows; 6,919 rows have at least one missing key component. Editions, ports, repeat releases, and missing identifiers make this ambiguous.
- Only 2,199 rows have all four region fields and total sales present; among those, 1,315 exactly match the regional sum and maximum difference is 0.02. Only 6,541 rows have critic scores.

Counts above are audit facts, not conclusions about the game market. The provided sources appear to have different populations, definitions, and coverage; use `vgsales.csv` for the required assignment analyses, use `vgchartz-2024.csv` for supplemental Advanced Analysis, and keep their results source-specific unless a documented reconciliation supports a comparison.

## Dataset-to-analysis assignment

The default dataset for each required university analysis is `vgsales.csv`. The additional dataset is a separate, clearly labeled source for advanced/extra-credit work. Do not use one dataset to fill missing values in the other or combine their rows for a shared ranking.

| Analysis or dashboard area | Dataset | Scope and handling |
|---|---|---|
| Structure inspection, missing values, types, duplicate detection, descriptive statistics | Both, reported separately | The assignment’s primary audit and cleaning narrative focuses on `vgsales.csv`; a separate advanced-data quality view documents `vgchartz-2024.csv`. |
| Top 10 globally best-selling games | `vgsales.csv` | Required assignment ranking by `Global_Sales`. State the rank measure and source. |
| Releases per year and global sales over time | `vgsales.csv` | Required assignment trends use `Year` and `Global_Sales`; disclose missing year values and source coverage. |
| Genre counts and global sales | `vgsales.csv` | Required assignment measure. |
| Platform counts, sales, and popularity over time | `vgsales.csv` | Required assignment measure using `Platform`, `Year`, and sales fields. |
| Regional preference comparison and genre-region dominance | `vgsales.csv` | Required regions: North America, Europe, Japan (plus Other where useful); use `NA_Sales`, `EU_Sales`, `JP_Sales`, `Other_Sales`. |
| Top 10 publishers and publisher-by-genre hit investigation | `vgsales.csv` | Required assignment analysis, using the primary source’s global sales and genre fields. |
| Market Power Index | `vgsales.csv` | Required custom metric. Keep publisher genre shares, leadership flags, genre diversity, regional consistency, hit rate, composite score, and archetypes in the primary dataset population. |
| Regional Preference Divergence: game, genre, time, stability, cultural outliers | `vgsales.csv` | Required custom analysis; document eligibility where region sales or year are missing/zero. |
| Critic-score versus sales relationship | `vgchartz-2024.csv` | Supplemental advanced analysis only; restrict to records with the required score and sales fields, and always report the eligible sample size. |
| Developer and richer console analyses | `vgchartz-2024.csv` | Optional advanced analysis; report the dataset’s coverage, category definitions, and missingness. Console is not automatically the same classification as primary `Platform`. |
| Date-level or advanced release-period analysis | `vgchartz-2024.csv` | Optional advanced analysis only after date precision and placeholder conventions are reviewed. It does not replace the primary dataset’s required annual trend analysis. |
| Additional publisher/genre views | `vgchartz-2024.csv`, as a distinct view | May add depth for extra marks, but must not be pooled into primary rankings or used to backfill primary results. |
| Overview, Market Trends, Genre, Platform, Regional, Publisher, Market Power, Regional Divergence pages | `vgsales.csv` by default | These dashboard pages implement and explain the required assignment analyses. If supplemental-source views are offered, label them by source and keep their filters/results distinct. |
| Advanced Analysis page | `vgchartz-2024.csv` | Dedicated supplemental section, with coverage notes and separate visual labels. |
| Data Quality page | Both, side by side or source-selected | Keep row counts, missingness, duplicate candidates, parse issues, and validation summaries separated by source. |

Cross-source comparison is not a default analysis. A future comparison requires an explicit question, documented field/coverage reconciliation, compatible units and definitions, and clear disclosure. `EU_Sales` and `pal_sales`, and `Platform` and `console`, are not interchangeable aliases without evidence.
## Architecture principles

1. Separate raw data, processed data, Python analysis, notebooks, and the web dashboard into distinct top-level areas with explicit ownership. Raw data is immutable. Every cleaned/intermediate file and report can be regenerated from source files and recorded configuration.
2. Python owns parsing, cleaning, validation, cohort selection, grouping, all metrics, and generated insight text/data. The frontend never performs Pandas-like work or embeds analytical answers as constants.
3. Do not blindly merge the datasets. Their schemas and coverage differ, so keep source-specific schemas, cleaning, analyses, and outputs separate by default. Any future join or cross-source comparison requires a documented reconciliation and justification. `EU_Sales` and `pal_sales` are not interchangeable by default.
4. Every metric travels with definition/version, unit, source, cohort, and coverage/denominator metadata.
5. Use prepared aggregates for dashboard interaction. If a filter combination needs a new aggregation, Python prepares it during the build or a future server-side analytics API computes it; the browser must not reconstruct raw-data analysis.
6. Prefer a static-first Next.js/Vercel deployment: generate compact JSON as part of an explicit analytics build and ship it as static assets. Consider a server/API only if later requirements demand arbitrary filters or refreshed data.
7. Keep files modular and maintain separation among pipeline, analysis, export contracts, visual components, and page-specific UI.

## Proposed repository layout

```text
gamescope/
├── README.md
├── PROJECT_PLAN.md
├── .gitignore
├── .gitattributes
├── LICENSE                         # choose after ownership/redistribution review
├── data/
│   ├── raw/                        # local source CSVs; ignored by Git by default
│   ├── interim/                    # regenerated normalized tables, if useful
│   └── processed/                  # generated aggregates and reports
├── docs/
│   ├── data-dictionary.md
│   ├── methodology.md
│   ├── reproducibility.md
│   └── deployment.md
├── notebooks/
│   ├── 01_data_quality.ipynb
│   ├── 02_core_eda.ipynb
│   ├── 03_market_power.ipynb
│   ├── 04_regional_divergence.ipynb
│   └── 05_vgchartz_advanced.ipynb
├── python/
│   ├── pyproject.toml
│   ├── src/gamescope/
│   │   ├── config.py
│   │   ├── provenance.py
│   │   ├── io.py
│   │   ├── schemas/
│   │   │   ├── vgsales.py
│   │   │   └── vgchartz.py
│   │   ├── quality/
│   │   │   ├── inspection.py
│   │   │   ├── validation.py
│   │   │   └── duplicate_review.py
│   │   ├── cleaning/
│   │   │   ├── common.py
│   │   │   ├── vgsales.py
│   │   │   └── vgchartz.py
│   │   ├── metrics/
│   │   │   ├── descriptive.py
│   │   │   ├── market_power.py
│   │   │   └── regional_divergence.py
│   │   ├── analysis/
│   │   │   ├── overview.py
│   │   │   ├── trends.py
│   │   │   ├── genres.py
│   │   │   ├── platforms.py
│   │   │   ├── regions.py
│   │   │   ├── publishers.py
│   │   │   ├── advanced_vgchartz.py
│   │   │   └── insights.py
│   │   ├── exports/
│   │   │   ├── models.py
│   │   │   ├── json_writer.py
│   │   │   └── report_writer.py
│   │   ├── pipeline.py
│   │   └── cli.py
│   ├── tests/
│       ├── fixtures/
│       ├── test_cleaning.py
│       ├── test_validation.py
│       ├── test_metrics.py
│       └── test_export_contract.py
├── web/
│   ├── package.json
│   ├── next.config.ts
│   ├── public/data/                  # generated frontend payloads only
│   └── src/
│       ├── app/
│       │   ├── page.tsx
│       │   ├── market-trends/page.tsx
│       │   ├── genre-analysis/page.tsx
│       │   ├── platform-analysis/page.tsx
│       │   ├── regional-intelligence/page.tsx
│       │   ├── publisher-intelligence/page.tsx
│       │   ├── market-power/page.tsx
│       │   ├── regional-divergence/page.tsx
│       │   ├── advanced-analysis/page.tsx
│       │   └── data-quality/page.tsx
│       ├── components/
│       │   ├── charts/
│       │   ├── filters/
│       │   ├── insights/
│       │   ├── layout/
│       │   ├── search/
│       │   └── tables/
│       ├── features/
│       │   ├── overview/
│       │   ├── market-trends/
│       │   ├── genre-analysis/
│       │   ├── platform-analysis/
│       │   ├── regional-intelligence/
│       │   ├── publisher-intelligence/
│       │   ├── market-power/
│       │   ├── regional-divergence/
│       │   ├── advanced-analysis/
│       │   └── data-quality/
│       ├── lib/
│       │   ├── analytics-client.ts
│       │   ├── filter-state.ts
│       │   ├── format.ts
│       │   └── search.ts
│       ├── types/
│       │   └── analytics.ts
│       └── styles/
├── reports/                          # generated inspection/EDA summaries
└── .github/workflows/                # optional CI after repository setup
```

Keep the supplied files in their current locations during planning. At repository setup, move/copy them to `data/raw/` only as a deliberate, documented step. Do not commit source data until licenses, redistribution terms, file size, and assignment rules have been confirmed. Raw data should be ignored by default; document exact local filenames and acquisition steps.

### Folder responsibilities

- `data/raw/`: untouched source snapshots. Never write cleaned values over these files.
- `data/interim/`: optional normalized row-level outputs for repeatable pipeline stages; safe to regenerate.
- `data/processed/`: generated, frontend-ready aggregates, quality reports, and manifests.
- `docs/`: data dictionary, methods/formulas, source provenance, reproducibility, and deployment instructions.
- `notebooks/`: the formal university deliverable and narrative EDA. Reuse package functions so notebook and dashboard results do not diverge; notebooks explain findings and decisions rather than becoming a second hidden production pipeline.
- `python/src/gamescope/`: source-specific ingestion, cleaning, validation, analytic functions, insight generation, export, and CLI orchestration.
- `python/tests/`: deterministic checks for transformations, formulas, edge cases, and data-contract output.
- `web/src/app/`: route composition, navigation shell, metadata, and route-level states.
- `web/src/features/`: page-specific binding of prepared datasets to reusable visual and interaction components.
- `web/src/components/`: shared charts, tables, search, filter controls, insight/quality cards, and layout.
- `web/src/lib/` and `web/src/types/`: payload loading, filter state, search/format helpers, and typed JSON contracts; no heavy calculations.
- `web/public/data/`: generated data only, never hand-authored metrics.
- `reports/`: human-readable generated quality/analysis summaries for review and documentation.

## Python architecture and responsibilities

- `config.py`: project-relative paths, source file names, output destinations, and explicit parameters. No developer-machine absolute paths.
- `provenance.py`: input SHA-256 fingerprints, run timestamp, code/schema version, and configuration metadata.
- `io.py`: encoding/delimiter checks, CSV loading, source fingerprints, and preservation of original fields/raw values.
- `schemas/`: independent expected columns and types for each source. Normalize the `last_update;;` header/value artifact only through a named, reported rule.
- `quality/inspection.py`: row/column counts, missing and sentinel counts, type parse rates, category cardinalities, numeric distributions, exact duplicates, candidate keys, and quality report generation.
- `quality/duplicate_review.py`: identify repeated-key clusters and compare all fields; preserve review evidence. Only approved rules can remove rows.
- `cleaning/`: source-specific type conversion, whitespace normalization, sentinel semantics, date parsing, and column naming. Keep a raw-to-cleaned change log and never silently impute/drop.
- `quality/validation.py`: required columns, parse failures, bounds, nonnegative sales, date ranges, region-total arithmetic, row-count changes, and output invariants.
- `metrics/descriptive.py`: descriptive statistics, top-10 games, annual release counts, global sales summaries, and common numeric summaries.
- `analysis/trends.py`: annual release and sales time series with missing/partial-year markers and specified aggregation choice.
- `analysis/genres.py`, `platforms.py`, `regions.py`, `publishers.py`: focused source-aware groupings for required EDA.
- `metrics/market_power.py`: component metrics, formula version, ranks, archetype features, and all denominator/coverage behavior.
- `metrics/regional_divergence.py`: game divergence, genre-region affinity, yearly regional favorites, preference stability, cultural outliers, and component scores.
- `analysis/advanced_vgchartz.py`: vgchartz-only analyses such as score-sales association, developer/publisher/console cuts, date-based trends, and coverage diagnostics where data supports them.
- `analysis/insights.py`: generates evidence-backed insight records in Python from computed values, with trigger/metric provenance; do not hardcode analytical prose in the frontend.
- `exports/`: schema-validated JSON, CSV and report outputs with explicit nulls, units, versions, and metadata.
- `pipeline.py`/`cli.py`: deterministic stages such as `inspect`, `clean`, `analyze`, `export`, and `all`; log warnings and input/output row counts.

### Formal notebook mapping

The notebook sequence covers the specification and explains data-wrangling choices:

1. `01_data_quality`: source loading, structure inspection, missing/sentinel analysis, types, duplicate candidates, validation checks, and cleaning rationale.
2. `02_core_eda`: descriptive statistics, top 10 games, annual releases, global sales trend, genre, platform, regional comparison, and publisher analysis.
3. `03_market_power`: market share by publisher/genre, genre leaders, diversity, regional consistency, hit rate, composite index, rankings, and archetypes.
4. `04_regional_divergence`: game-level divergence, genre-region affinity/indexing, temporal favorite/stability, and cultural outliers.
5. `05_vgchartz_advanced`: distinct advanced analyses using `vgchartz-2024.csv`, with coverage and comparability limits clearly stated.

Use matplotlib or seaborn as required. Every plot needs a meaningful title, labeled axes, legend where appropriate, and a written interpretation tied to computed results. Notebook conclusions summarize key findings, data-wrangling challenges, and how visualization aided understanding.

## Analytical definitions to settle before implementation

The assignment names some measures but leaves their equations partly open. Record final choices in `docs/methodology.md` and alongside each exported metric. Do not present a metric as objective until its denominator, eligible population, missing-value behavior, time scope, and weighting have been agreed.

### Market Power Index

Required publisher-level components:

- **Publisher genre share:** publisher sales within genre divided by total genre sales.
- **Genre leader flag:** share strictly greater than 30% for that genre.
- **Genre Diversity Score:** number of distinct genres represented. Decide if simple count is sufficient or whether a normalized diversity measure will supplement it; preserve required count either way.
- **Regional Consistency Score:** standard deviation of a publisher’s regional sales proportions; lower standard deviation means more consistent. Define regions for each source separately and how unknown/missing regional sales affect the proportions.
- **Hit Rate:** proportion of a publisher’s games whose sales exceed the median sales for that game’s genre. Define source, unit of game identity, treatment of duplicate releases, and genre-median cohort.
- **Composite index and archetypes:** custom formula, normalization, weights, missing-component strategy, tie handling, sensitivity/robustness review, and archetype rules must be documented. The assignment does not specify these; choose transparently before coding and include component scores with the final rank.

### Regional Preference Divergence

- **Game-level divergence:** normalize regional sales to within-game shares; compare each with the overall region-share baseline; calculate a documented divergence measure (candidate examples in the assignment: coefficient of variation or entropy-based). Define zero-sales/zero-region behavior and whether incomplete regional rows are eligible.
- **Genre-region affinity:** for every genre, compute sales share by region; compare with overall regional shares; define over/under-index threshold (or report continuous index values without arbitrary labels).
- **Temporal preferences:** group by year and region, choose the favorite genre rule (sales versus title count, ties), and quantify preference stability/convergence over time. The preference stability equation is custom and needs approval/documentation.
- **Cultural outliers:** implement the given screen (>50% in one region, <10% in each other region) on a defined complete-case population; specify the cultural-specificity score and how ties/missing regions are treated.

## Next.js dashboard architecture

### Routes and page responsibilities

- **Overview:** Python-prepared headline metrics, insight cards, dataset/source selector, and navigation into detail pages.
- **Market Trends:** annual releases and sales, source-aware time span, filters, and notes about incomplete years.
- **Genre Analysis:** genre counts/sales, regional mixes, ranking and composition visualizations.
- **Platform Analysis:** platform volume/sales, active years, and prepared evolution series.
- **Regional Intelligence:** regional comparison and genre-region heatmap with region names that retain source-specific meaning.
- **Publisher Intelligence:** top publishers, genre footprint, prepared publisher search and drill-down.
- **Market Power Index:** ranked index, component breakdown, genre-leader display, and methodology explanation.
- **Regional Divergence:** divergence ranking, affinity matrix, temporal stability, and cultural-outlier exploration.
- **Advanced Analysis:** vgchartz-specific views, including critic-score/sales association only for rows with the necessary data; show eligible sample sizes.
- **Data Quality:** missingness, sentinel values, parse/validation issues, duplicate candidates/resolutions, source definitions, and coverage notes.

### Shared modules/components

- Layout: `DashboardShell`, `SidebarNav`, `PageHeader`, responsive navigation, breadcrumbs.
- Filters: `GlobalFilterBar`, `DatasetSelector`, `YearRangeFilter`, `MultiSelectFilter`, clear/reset control, and active-filter summary.
- Visual/data display: `KpiCard`, `InsightCard`, `ChartCard`, `DataTable`, `CoverageNote`, `MethodologyDisclosure`, `EmptyState`, `LoadingState`, `ErrorState`.
- Search: `SearchBox`, result list and detail drawer/page using generated title/publisher/platform index; support clear no-results behavior.
- Charts: reusable line/time series, ranked bars, grouped/stacked bars, heatmap, composition, and scatter components. Chart components receive typed data and labels; they do not calculate aggregate metrics.
- Feature folders contain each route’s data selection, local interaction state, explanations, and chart/table composition.
- `analytics-client.ts` validates/fetches generated manifest/payloads; `filter-state.ts` manages URL-addressable filter state; `search.ts` queries prepared search records; `format.ts` formats units, nulls, and dates; `types/analytics.ts` defines contracts.

### Interactive filters and search constraint

The backend will prepare aggregates at the dimensions needed by the agreed dashboard filters (for example source × year × genre × platform, plus publisher/region-specific aggregates where needed). The frontend may select/slice those prepared outputs and update visual state. It must not derive new sales totals, ranks, indices, or insights by aggregating downloaded raw rows. Any filter combination not represented by prepared output is either disabled/limited or served by a future Python API. Search uses a compact Python-generated index, not the source CSV.

## Frontend data contract

Generate compact, partitioned JSON during the Python export stage. Suggested files and key contents:

- `manifest.json`: schema version, pipeline/code version, generated timestamp, source IDs and fingerprints, source row counts, output inventory, and units/region labels.
- `quality.json`: field-level empty/sentinel/parse-failure counts, exact duplicates, candidate duplicate groups, validation warnings, and coverage information.
- `overview.json`: headline values and Python-generated insight cards, each with source, period/cohort, formula/meaning, denominator/coverage, and display unit.
- `annual_trends.json`: source-specific year buckets with release counts, global/total sales summaries, regional sums, and missing/partial-year annotations.
- `top_games.json`: ranked records and ranking definition; support top-ten notebook output and dashboard search/drill-down separately.
- `genre_aggregates.json`: per-source genre counts, sales metrics, shares, and regional composition.
- `platform_aggregates.json`: per-source platform counts, sales, active-year series, and coverage.
- `regional_aggregates.json`: source-specific region labels and values, denominators, and cohort definitions.
- `publisher_aggregates.json`: publisher totals, game counts, genre footprints, ranks/shares, and unknown-publisher treatment.
- `market_power.json`: overall score, ranks, all components, weights, formula version, eligibility, and archetype labels.
- `regional_divergence.json`: game/genre/year/region metrics, baseline distributions, formula version, thresholds, and eligibility counts.
- `vgchartz_advanced.json`: advanced metric records with source, sample sizes, and coverage limitations.
- `search_index.json`: normalized searchable strings and stable IDs, limited to required fields.

Every payload has explicit null semantics, metric units, source, applied cohort, coverage/denominator, and `schemaVersion`. Avoid duplicating large game-level details across multiple files; use stable IDs and bounded pagination/partitioning. Measure output sizes before selecting partition strategy.

## Deployment and repository design

- **GitHub:** initialize the repository only during setup; `.gitignore` excludes environments, caches, secrets, raw data by default, and regenerable intermediates. Track source code, documentation, notebooks, and small generated samples/contracts. Decide source-data licensing and PDF redistribution before publishing. Do not commit secrets or local machine paths. Optional CI validates Python package and export contract, then builds the Next.js app.
- **Vercel:** deploy only `web/`; configure the repository root/build command and generated data location explicitly. The analytics build runs in a supported Python environment before deployment or in CI, writes the prepared JSON consumed by Next.js, and checks generated data is available. Use static JSON delivery first; if artifacts exceed practical payload/build limits or truly arbitrary filtering is required, design a Python-backed API and hosting separately rather than sending raw CSVs to Vercel clients.
- **Reproducibility:** document Python and Node versions/dependencies, one command for analytics export, one for local web development, and a clean-data acquisition procedure. Record input fingerprints and output schema version on each build.

## Risks and decisions

1. **Source comparability:** do not blindly merge or append the CSVs. Keep them independent unless field definitions, populations, sales units, and coverage are validated and a documented reconciliation justifies a specific comparison.
2. **Regional naming:** `EU_Sales` is not automatically equal to `pal_sales`; carry labels and definitions by source.
3. **Unknown/missing distinction:** preserve blanks, `N/A`, `Unknown`, and `TBD` as separate raw states until policy is approved; do not map missing sales to zero without evidence.
4. **Duplicates and identity:** repeated title/platform/year is not proof of duplication; inspect all fields and potentially distinct releases/editions before removal.
5. **Sales reconciliation:** totals and regional sums can differ by up to 0.02 in observed comparable rows; likely rounding/source conventions need explanation, not automatic correction.
6. **Date precision:** ISO syntax does not guarantee true day-level precision; some dates may be placeholders. Verify source semantics before day/month analyses.
7. **Alias resolution:** publisher, title, genre, platform/console naming can differ; maintain explicit reviewed crosswalks if comparison is needed and record match confidence.
8. **Custom metric subjectivity:** index weights, stability/divergence formulas, outlier score, and archetype rules are choices; document rationale and test sensitivity.
9. **Coverage bias:** VGChartz numeric metrics are sparsely available; every score-sales or regional comparison needs its own eligible sample count and selection disclosure.
10. **Public data licensing:** verify dataset and assignment-material terms before GitHub/Vercel publication. Raw data is excluded by default.
11. **Static data size/privacy:** only public, aggregate/prepared fields belong in client assets; keep payloads compact and do not expose unnecessary row-level data.
12. **Future filter growth:** exact multi-dimensional arbitrary filterability may make static aggregates large. Keep the initial supported filters explicit and reassess before adding API complexity.

## Staged implementation plan and acceptance gates

### Stage 0 — Project decisions and setup

Confirm data provenance/licenses, source acquisition, public/private repository choice, package/runtime versions, output policy, and which dashboard filters are in the first release. Establish repository layout and ignore rules without modifying source CSV contents.

**Gate:** clean clone can locate documented input paths; no raw data/secrets are tracked accidentally; versions and reproducible commands are recorded.

### Stage 1 — Data audit and data dictionary

Implement schema checks, type/missingness/sentinel reports, category counts, sales reconciliation, exact/candidate duplicate analysis, date review, and raw file fingerprints. Document each field and unresolved source question.

**Gate:** reports reproduce inspected counts and distinguish blank from sentinel values; candidate duplicates are reviewed rather than removed by assumption.

### Stage 2 — Cleaning policy and reproducible Python pipeline

Approve source-specific missing/sentinel, type, date/header, category normalization, duplicate and invalid-row policies. Implement immutable raw-to-interim stages and validation/error reporting.

**Gate:** deterministic rerun produces the same cleaned records and a machine-readable change/quality report; every row drop or value transformation is attributable to a rule.

### Stage 3 — Required core analysis and notebook

Implement descriptive statistics, top 10, yearly releases/sales, genres, platforms, regional comparison, publishers, and visualizations using matplotlib/seaborn. Build the explanatory Jupyter notebook from package functions.

**Gate:** notebook covers every Part I/II requirement, contains labeled/insightful plots, and ends with the required conclusions; formulas can be traced to Python modules.

### Stage 4 — Custom metrics and VGChartz advanced analysis

Agree and document market-power and regional-divergence formulas, weights, denominator/cohort rules, and ties. Implement component outputs and run sensitivity/edge-case review. Add advanced second-source analysis only for adequately covered values.

**Gate:** each index is reproducible and accompanied by formula version, eligibility, components, and limitations; incomplete records do not silently become zeros.

### Stage 5 — Export contract and dashboard data preparation

Define typed/versioned payloads; generate partitioned JSON, quality report, manifest, search index, and supported filter aggregates. Validate size and schema.

**Gate:** a clean pipeline run creates every expected payload and the frontend can load it without modifying analytical results.

### Stage 6 — Next.js dashboard foundation

Build the responsive shell, routes, typed loaders, common components, error/loading/empty states, and URL-backed filter controls. Wire it to generated sample payloads/contracts, not hardcoded analytical values.

**Gate:** each planned route renders; interactions stay within prepared data; accessibility and mobile layout receive review.

### Stage 7 — Dashboard storytelling and feature completion

Add all feature pages, charts, evidence-based insight cards, coverage notes, methodology disclosures, and search/exploration. Coordinate region/filter labels to their dataset source.

**Gate:** every visualization can be traced to a Python payload and each insight has a metric definition and denominator; no browser-side heavy aggregation is present.

### Stage 8 — End-to-end review and deployment preparation

Check notebook and dashboard consistency, data quality warnings, payload size, Vercel build configuration, GitHub docs, licensing, and public-data boundaries. Run the documented local pipeline/build and deployment preview.

**Gate:** a fresh environment can reproduce analytics and build the site; deployment artifacts contain prepared outputs only and no unapproved data/secrets.

### Stage 9 — Release and ongoing maintenance

After repository/deployment authorization, publish the approved code/artifacts, document source refresh procedure and metric versioning, and keep future source updates auditable.

**Gate:** published release links to methodology, versioned output provenance, and data acquisition/licensing notes.

## Current boundary

Only architecture and planning are authorized at this stage. Do not begin dashboard implementation, create a Next.js scaffold, clean or rewrite CSVs, choose unapproved custom-metric weights, or publish anything until the corresponding next instruction and methodology decisions are provided.





