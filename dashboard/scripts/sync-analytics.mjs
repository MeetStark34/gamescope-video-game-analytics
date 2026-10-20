import { mkdir, readFile, copyFile, writeFile, access } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const sourceDir = path.resolve(here, "../../data/processed/analytics");
const publicDir = path.resolve(here, "../public/data/analytics");

const files = [
  "dashboard_primary_records.json", "dashboard_data_quality.json",
  "descriptive_statistics.json", "top_games.json", "annual_trends.json",
  "games_released_per_year.json", "global_sales_by_year.json",
  "genre_frequency.json", "genre_global_sales.json", "genre_region_affinity.json",
  "platform_game_counts.json", "platform_global_sales.json", "platform_evolution.json",
  "regional_sales_comparison.json", "regional_genre_preferences.json",
  "regional_preference_changes.json", "regional_preference_stability.json",
  "regional_preference_divergence_by_year.json", "regional_divergence_by_game.json",
  "cultural_outliers.json", "publisher_summary.json", "top_publishers.json",
  "publisher_genre_market_shares.json", "publisher_genre_dominance.json",
  "market_power_index.json", "insights.json", "vgchartz_profile.json",
  "critic_score_sales_association.json", "critic_score_sales_points.json", "critic_score_sales_points.csv",
  "vgchartz_developer_performance.json", "vgchartz_publisher_performance.json",
  "vgchartz_publisher_developer_performance.json", "vgchartz_platform_by_year.json",
  "vgchartz_platform_lifecycle.json", "vgchartz_release_date_trends.json",
  "vgchartz_release_by_year.json", "vgchartz_release_by_month.json",
  "vgchartz_release_by_quarter.json", "vgchartz_release_by_weekday.json",
  "vgchartz_recent_industry_trends.json", "vgchartz_recent_industry_trends_annual.json",
];

await mkdir(publicDir, { recursive: true });
try {
  await access(path.join(sourceDir, "manifest.json"));
  for (const file of files) {
    if (file.endsWith(".csv")) continue;
    await copyFile(path.join(sourceDir, file), path.join(publicDir, file));
  }

  const manifest = JSON.parse(await readFile(path.join(sourceDir, "manifest.json"), "utf8"));
  const publicManifest = {
    schema_version: manifest.schema_version,
    pipeline_version: manifest.pipeline_version,
    generated_at: manifest.generated_at,
    primary_source: manifest.source_dataset,
    primary_rows: manifest.source_rows,
    advanced_source: manifest.advanced_source_dataset,
    advanced_rows: manifest.advanced_source_rows,
    exported_files: files.filter((file) => file.endsWith(".json")).length,
  };
  await writeFile(path.join(publicDir, "dashboard_manifest.json"), `${JSON.stringify(publicManifest, null, 2)}\n`);
  console.log(`Synced prepared analytics files from ${sourceDir}`);
} catch (error) {
  if (!error || typeof error !== "object" || !("code" in error) || error.code !== "ENOENT") throw error;
  await access(path.join(publicDir, "dashboard_manifest.json"));
  for (const file of files.filter((item) => item.endsWith(".json"))) {
    await access(path.join(publicDir, file));
  }
  console.log("Using the checked-in dashboard analytics snapshot; Python and raw datasets are not required for this build.");
}
