"""Small pure helpers shared by the independent analytics functions."""

from __future__ import annotations

import math
import statistics
from typing import Any, Iterable, Mapping


def as_number(value: Any) -> float | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        number = float(str(value).strip().replace(",", ""))
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def as_year(value: Any) -> int | None:
    number = as_number(value)
    if number is None or not number.is_integer():
        return None
    return int(number)


def category(value: Any) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text if text else None


def region_fields(row: Mapping[str, Any]) -> dict[str, float | None]:
    """Return source-specific sales under their original region labels."""
    if any(key in row for key in ("NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales")):
        keys = {"North America": "NA_Sales", "Europe": "EU_Sales", "Japan": "JP_Sales", "Other": "Other_Sales"}
    else:
        keys = {"North America": "na_sales", "PAL": "pal_sales", "Japan": "jp_sales", "Other": "other_sales"}
    return {label: as_number(row.get(key)) for label, key in keys.items()}


def median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def sorted_records(records: Iterable[Mapping[str, Any]], key: str, descending: bool = True) -> list[dict[str, Any]]:
    return sorted((dict(record) for record in records), key=lambda row: (row.get(key) is None, row.get(key, 0)), reverse=descending)


def safe_share(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def rows_as_mappings(data: Any) -> list[Mapping[str, Any]]:
    """Accept row mappings or a DataFrame-like object without requiring pandas."""
    if data is None:
        return []
    if hasattr(data, "to_dict") and hasattr(data, "columns"):
        try:
            return list(data.to_dict(orient="records"))
        except TypeError:
            pass
    if isinstance(data, Mapping):
        return [data]
    try:
        return [row for row in data if isinstance(row, Mapping)]
    except TypeError:
        return []
