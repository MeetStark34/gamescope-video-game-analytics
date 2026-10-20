export type NumericSummary = {
  count: number;
  missing_or_invalid: number;
  min: number | null;
  q1: number | null;
  median: number | null;
  q3: number | null;
  max: number | null;
  mean: number | null;
  std_population: number | null;
};

export type DescriptiveStatistics = Record<string, NumericSummary>;
export type TopGame = {
  name: string | null;
  platform: string | null;
  year: number | string | null;
  genre: string | null;
  publisher: string | null;
  global_sales: number;
  sales_rank: number;
  source_row?: number | null;
  duplicate_status?: string | null;
  sales_by_region?: { north_america: number | null; europe: number | null; japan: number | null; other: number | null };
};
export type AnnualTrend = {
  year: number;
  games_released: number;
  games_with_year_and_sales: number;
  global_sales_total: number | null;
  global_sales_mean: number | null;
};
export type GamesReleasedByYear = { year: number; games_released: number };
export type GlobalSalesByYear = { year: number; games_with_year_and_sales: number; global_sales_total: number | null; global_sales_mean: number | null };
export type GenreFrequency = { genre: string; game_count: number };
export type GenreSales = {
  genre: string;
  games_with_sales: number;
  global_sales_total: number;
  global_sales_mean: number;
  global_sales_share: number | null;
};
export type PlatformCount = { platform: string; game_count: number };
export type PlatformSales = {
  platform: string;
  games_with_sales: number;
  global_sales_total: number;
  global_sales_mean: number;
  global_sales_share: number | null;
};
export type PlatformEvolution = {
  platform: string;
  year: number;
  games_released: number;
  games_with_sales: number;
  global_sales_total: number | null;
};
export type RegionalSales = {
  region: string;
  sales_records: number;
  sales_total: number;
  sales_mean: number | null;
  share_of_reported_regional_sales: number | null;
};
export type GenreAffinity = {
  genre: string;
  region: string;
  regional_sales: number;
  genre_region_share: number | null;
  overall_region_sales_share: number | null;
  affinity_index: number | null;
  index_class: "over_indexed" | "under_indexed" | "at_baseline" | "unavailable";
};
export type RegionalGenrePreference = {
  genre: string;
  region: string;
  regional_sales: number;
  genre_region_share: number | null;
  overall_region_share: number | null;
  affinity_index: number | null;
  genre_sales_total_all_regions: number;
};
export type RegionalFavoriteByYear = {
  year: number;
  region: string;
  favorite_genre: string;
  favorite_genre_sales: number;
  genres_with_sales: number;
};
export type RegionalPreferenceChange = {
  region: string;
  year: number;
  genre: string;
  regional_genre_sales: number;
  regional_genre_share: number;
  previous_observed_year: number | null;
  previous_observed_genre_share: number | null;
  share_change: number | null;
  favorite_genre: string;
  favorite_changed: boolean | null;
};
export type RegionalStability = {
  region: string;
  observed_years: number;
  adjacent_observed_year_pairs: number;
  same_favorite_pairs: number;
  preference_stability_index: number | null;
  definition: string;
};
export type RegionalYearDivergence = {
  year: number;
  pairwise_region_distances: Array<{
    region_a: string;
    region_b: string;
    total_variation_distance: number;
  }>;
  mean_pairwise_divergence: number | null;
  regions_compared: number;
};
export type PublisherSummary = {
  publisher: string;
  game_count: number;
  games_with_sales: number;
  genre_count: number;
  genres: string[];
  global_sales_total: number;
  global_sales_share: number | null;
};
export type PublisherGenreShare = {
  publisher: string;
  genre: string;
  publisher_genre_sales: number;
  genre_total_sales: number;
  genre_market_share: number | null;
  games_with_sales: number;
  leader_threshold: number;
  is_genre_leader: boolean;
};
export type MarketPower = {
  publisher: string;
  game_record_count: number;
  games_with_global_sales: number;
  games_in_hit_rate_denominator: number;
  genre_count: number;
  total_genres_in_source: number;
  genre_leader_count: number;
  genre_leaders: string[];
  regional_complete_records: number;
  regional_incomplete_records: number;
  regional_sales_proportions: Record<string, number> | null;
  sales_share: number | null;
  genre_leadership_coverage: number | null;
  genre_diversity_score: number | null;
  regional_consistency_score: number | null;
  hit_rate: number | null;
  available_component_count: number;
  market_power_index: number | null;
  formula_version: string;
  publisher_archetype: string;
  market_power_rank: number | null;
};
export type DivergenceGame = {
  source_row: number | string | null;
  name: string | null;
  platform: string | null;
  year: number | null;
  genre: string | null;
  global_sales: number | null;
  regional_sales_total: number;
  regional_divergence_score: number;
  regional_proportions: Record<string, number>;
  baseline_regional_proportions: Record<string, number>;
  dominant_region: string;
  dominant_region_share: number;
  cultural_specificity_score: number;
  passes_cultural_outlier_screen: boolean;
};
export type Insight = {
  id: string;
  title: string;
  text: string;
  metric: string;
  value: number;
  source: string;
  coverage: number;
};
export type DashboardManifest = {
  schema_version: number;
  pipeline_version: string;
  generated_at: string;
  primary_source: string;
  primary_rows: number;
  advanced_source: string;
  advanced_rows: number;
  exported_files: number;
};
export type PrimaryDashboardRecord = {
  source_row: number | null;
  duplicate_status: string | null;
  Rank: number | null;
  Year: number | null;
  NA_Sales: number | null;
  EU_Sales: number | null;
  JP_Sales: number | null;
  Other_Sales: number | null;
  Global_Sales: number | null;
  Name: string | null;
  Platform: string | null;
  Genre: string | null;
  Publisher: string | null;
};
export type SourceDataQuality = {
  source_dataset: string;
  processed_dataset: string;
  original_rows: number;
  cleaned_rows: number;
  rows_removed: number;
  missing_value_total: number;
  missing_values_by_field: Record<string, number>;
  exact_duplicate_groups_flagged: number;
  potential_duplicate_groups_flagged: number;
  duplicate_rows_flagged: number;
  transformation_events: number;
  rows_with_transformations: number;
  transformations_by_field: Record<string, number>;
  categorical_policy: string;
  missing_policy: string;
  duplicate_policy: string;
};
export type DashboardDataQuality = SourceDataQuality & { advanced_source: SourceDataQuality | null };

export type VgchartzProfile = {
  source_dataset: string;
  row_count: number;
  duplicate_candidate_rows_retained: number;
  field_coverage: Record<string, { present: number; missing: number; coverage_percent: number | null }>;
  source_separation_note: string;
};
export type CriticScoreBand = {
  score_band: string;
  score_lower: number;
  score_upper: number;
  upper_inclusive: boolean;
  record_count: number;
  mean_total_sales: number | null;
  median_total_sales: number | null;
};
export type CriticAssociation = {
  source_dataset: string;
  eligible_pair_count: number;
  source_row_count: number;
  eligible_pair_percent: number | null;
  critic_score_valid_range: [number, number];
  critic_score_sales_pearson_r: number | null;
  critic_score_sales_spearman_rho: number | null;
  critic_score_log1p_sales_pearson_r: number | null;
  missing_critic_score_count: number;
  missing_total_sales_count: number;
  unparseable_critic_score_count: number;
  unparseable_total_sales_count: number;
  invalid_critic_score_count: number;
  invalid_total_sales_count: number;
  negative_total_sales_count: number;
  critic_score_bands: CriticScoreBand[];
  interpretation: string;
};
export type CriticPoint = {
  title: string | null;
  console: string | null;
  critic_score: number;
  total_sales: number;
  release_date: string | null;
};
export type CompanyPerformance = {
  publisher?: string;
  developer?: string;
  release_records: number;
  records_with_sales: number;
  records_with_critic_score: number;
  total_sales: number;
  mean_sales?: number | null;
  median_sales?: number | null;
  sales_share?: number | null;
  mean_critic_score: number | null;
  median_critic_score?: number | null;
  developer_count?: number;
  console_count: number;
  genre_count: number;
  publisher_count?: number;
};
export type VgPlatformYear = {
  console: string;
  year: number;
  release_records: number;
  records_with_sales: number;
  total_sales: number | null;
};
export type VgPlatformLifecycle = {
  console: string;
  first_observed_release_year: number;
  last_observed_release_year: number;
  observed_active_year_count: number;
  peak_sales_year: number | null;
  peak_annual_sales: number | null;
};
export type VgReleaseDateTrends = {
  source_dataset: string;
  source_rows: number;
  valid_iso_release_dates: number;
  missing_or_invalid_release_dates: number;
  jan_1_possible_imprecise_dates: number;
  date_precision_note: string;
};
export type VgRecentTrend = {
  year: number;
  release_records: number;
  records_with_sales: number;
  total_sales: number | null;
  mean_sales: number | null;
  median_sales: number | null;
  console_count: number;
  publisher_count: number;
  developer_count: number;
  previous_observed_year: number | null;
  release_record_change_percent: number | null;
  sales_change_percent: number | null;
};
export type VgReleaseByYear = {
  year: number;
  release_records: number;
  records_with_sales: number;
  total_sales: number | null;
  mean_sales: number | null;
};

export interface AnalyticsDataMap {
  dashboard_primary_records: PrimaryDashboardRecord[];
  dashboard_data_quality: DashboardDataQuality;
  dashboard_manifest: DashboardManifest;
  descriptive_statistics: DescriptiveStatistics;
  top_games: TopGame[];
  annual_trends: AnnualTrend[];
  games_released_per_year: GamesReleasedByYear[];
  global_sales_by_year: GlobalSalesByYear[];
  genre_frequency: GenreFrequency[];
  genre_global_sales: GenreSales[];
  genre_region_affinity: GenreAffinity[];
  platform_game_counts: PlatformCount[];
  platform_global_sales: PlatformSales[];
  platform_evolution: PlatformEvolution[];
  regional_sales_comparison: RegionalSales[];
  regional_genre_preferences: RegionalGenrePreference[];
  regional_favorites_by_year: RegionalFavoriteByYear[];
  regional_preference_changes: RegionalPreferenceChange[];
  regional_preference_stability: RegionalStability[];
  regional_preference_divergence_by_year: RegionalYearDivergence[];
  regional_divergence_by_game: DivergenceGame[];
  cultural_outliers: DivergenceGame[];
  publisher_summary: PublisherSummary[];
  top_publishers: PublisherSummary[];
  publisher_genre_market_shares: PublisherGenreShare[];
  publisher_genre_dominance: PublisherGenreShare[];
  market_power_index: MarketPower[];
  insights: Insight[];
  vgchartz_profile: VgchartzProfile;
  critic_score_sales_association: CriticAssociation;
  critic_score_sales_points: CriticPoint[];
  vgchartz_developer_performance: CompanyPerformance[];
  vgchartz_publisher_performance: CompanyPerformance[];
  vgchartz_publisher_developer_performance: Array<CompanyPerformance & { publisher: string; developer: string }>;
  vgchartz_platform_by_year: VgPlatformYear[];
  vgchartz_platform_lifecycle: VgPlatformLifecycle[];
  vgchartz_release_date_trends: VgReleaseDateTrends;
  vgchartz_release_by_year: VgReleaseByYear[];
  vgchartz_release_by_month: Array<{ month: number; release_records: number; records_with_sales: number; total_sales: number | null; mean_sales: number | null }>;
  vgchartz_release_by_quarter: Array<{ quarter: number; label: string; release_records: number; records_with_sales: number; total_sales: number | null; mean_sales: number | null }>;
  vgchartz_release_by_weekday: Array<{ weekday: number; label: string; release_records: number; records_with_sales: number; total_sales: number | null; mean_sales: number | null }>;
  vgchartz_recent_industry_trends: { source_dataset: string; window_years: number; window_start: number; window_end: number };
  vgchartz_recent_industry_trends_annual: VgRecentTrend[];
}

export type AnalyticsKey = keyof AnalyticsDataMap;
