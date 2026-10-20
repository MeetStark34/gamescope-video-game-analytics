"""Generate dashboard/notebook insight cards from calculated analytics."""

from __future__ import annotations

from typing import Any

from .genre_analysis import genre_frequency, genre_global_sales
from .metrics import top_games
from .platform_analysis import platform_global_sales
from .publisher_analysis import top_publishers
from .regional_analysis import regional_sales_comparison
from .trends import annual_trends


def generate_insights(data: Any) -> list[dict[str, Any]]:
    """Create evidence-linked insight records; all displayed values are computed."""
    cards: list[dict[str, Any]] = []
    games = top_games(data, 1)
    if games:
        game = games[0]
        cards.append({"id": "top_game", "title": "Top recorded global seller",
                      "text": f"{game['name']} ({game['platform']}) leads the supplied records with {game['global_sales']:g} reported global sales.",
                      "metric": "Global_Sales", "value": game["global_sales"], "source": "vgsales.csv", "coverage": 1})
    genres = genre_global_sales(data)
    if genres:
        genre = genres[0]
        cards.append({"id": "top_genre_sales", "title": "Highest-sales genre",
                      "text": f"{genre['genre']} has the largest summed global sales in the analyzed records ({genre['global_sales_total']:g}).",
                      "metric": "genre_global_sales_total", "value": genre["global_sales_total"], "source": "vgsales.csv", "coverage": genre["games_with_sales"]})
    frequencies = genre_frequency(data)
    if frequencies:
        genre = frequencies[0]
        cards.append({"id": "most_frequent_genre", "title": "Most frequently listed genre",
                      "text": f"{genre['genre']} is the most frequent genre label, appearing in {genre['game_count']} records.",
                      "metric": "genre_record_count", "value": genre["game_count"], "source": "vgsales.csv", "coverage": genre["game_count"]})
    platforms = platform_global_sales(data)
    if platforms:
        platform = platforms[0]
        cards.append({"id": "top_platform_sales", "title": "Platform with highest summed sales",
                      "text": f"{platform['platform']} has the largest platform sales sum ({platform['global_sales_total']:g}) in the supplied records.",
                      "metric": "platform_global_sales_total", "value": platform["global_sales_total"], "source": "vgsales.csv", "coverage": platform["games_with_sales"]})
    publishers = top_publishers(data, 1)
    if publishers:
        publisher = publishers[0]
        cards.append({"id": "top_publisher_sales", "title": "Publisher with highest summed sales",
                      "text": f"{publisher['publisher']} has the largest publisher sales sum ({publisher['global_sales_total']:g}) in the supplied records.",
                      "metric": "publisher_global_sales_total", "value": publisher["global_sales_total"], "source": "vgsales.csv", "coverage": publisher["games_with_sales"]})
    regions = regional_sales_comparison(data)
    if regions:
        region = max(regions, key=lambda item: item["sales_total"])
        cards.append({"id": "largest_region_sales", "title": "Largest reported regional total",
                      "text": f"{region['region']} has the largest sum among the region fields in this source ({region['sales_total']:g}). Regional definitions are source-specific.",
                      "metric": "regional_sales_total", "value": region["sales_total"], "source": "vgsales.csv", "coverage": region["sales_records"]})
    trends = annual_trends(data)
    valid_sales = [row for row in trends if row["global_sales_total"] is not None]
    if valid_sales:
        peak = max(valid_sales, key=lambda row: row["global_sales_total"])
        cards.append({"id": "peak_annual_sales", "title": "Highest recorded annual sales sum",
                      "text": f"The largest annual sales sum in years with valid year and sales values is {peak['year']} ({peak['global_sales_total']:g}).",
                      "metric": "annual_global_sales_total", "value": peak["global_sales_total"], "year": peak["year"], "source": "vgsales.csv", "coverage": peak["games_with_year_and_sales"]})
    return cards
