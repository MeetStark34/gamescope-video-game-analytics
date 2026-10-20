# GameScope Dashboard

The standalone Next.js application for GameScope. It presents Python-prepared analytical data; it does not run Python or reproduce analytical calculations in the browser.

## Local development

Use Node.js 20.9 or newer. From the repository root, generate the source outputs if you have the two local CSV datasets:

```powershell
py -3 -m python.pipeline
py -3 -m python.analytics_pipeline
```

Then run the dashboard:

```powershell
Set-Location dashboard
npm ci
npm run dev
```

The predev/prebuild hooks synchronize generated JSON from `../data/processed/analytics/` when that directory is available. Otherwise, they validate and use the checked-in static snapshot in `public/data/analytics/`. Refresh it manually with `npm run sync:data` after regenerating analytics.

## Quality checks and production

```powershell
npm run lint
npm run typecheck
npm run build
npm start
```

`npm run lint` is a dependency-free source-hygiene check for trailing whitespace, debug logging/statements, and hardcoded Windows paths. `npm run typecheck` runs TypeScript's strict compiler check.

The build does not need Python, raw CSVs, or machine-specific paths. Do not add secrets or environment values; none are currently required.

## Vercel

Create a Next.js project with the repository directory `dashboard` as its Root Directory. Use `npm ci` to install and `npm run build` to build; leave the Next.js output directory at its default. Keep `public/data/analytics/*.json` in Git because these prepared static assets are the dashboard's deployment data source. Vercel does not need to read files outside the dashboard directory and does not invoke Python.

The repo's Python pipeline is the source of truth. The tracked public snapshot is regenerated using `npm run sync:data` whenever prepared analytics exist locally, then reviewed and committed with the intended data release. Review dataset redistribution terms before publishing a new snapshot.

## Data scope

Primary-source routes use the prepared `vgsales.csv` outputs. The Advanced page uses the separate `vgchartz-2024.csv` outputs. Data Quality reports both separately. See [the root README](../README.md) and [`reports/advanced-analysis.md`](../reports/advanced-analysis.md) for methodology and definitions.
