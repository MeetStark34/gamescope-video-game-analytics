"""Input discovery and raw CSV loading for the GameScope pipeline."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_NAMES = ("vgsales.csv", "vgchartz-2024.csv")


@dataclass
class RawDataset:
    name: str
    path: Path
    columns: list[str]
    rows: list[dict[str, str]]


def locate_dataset(name: str, root: Path = PROJECT_ROOT) -> Path:
    """Prefer the conventional data/raw path, with current-root fallback."""
    candidates = (root / "data" / "raw" / name, root / name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    checked = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Could not locate {name}; checked: {checked}")


def load_dataset(path: Path) -> RawDataset:
    """Read every source field as text, preserving blanks and sentinel tokens."""
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        columns = list(reader.fieldnames)
        rows = []
        for row in reader:
            # DictReader uses None for overflow cells; preserve their value for validation.
            rows.append({key: value if value is not None else "" for key, value in row.items()})
    return RawDataset(path.name, path.resolve(), columns, rows)


def load_all(root: Path = PROJECT_ROOT) -> list[RawDataset]:
    return [load_dataset(locate_dataset(name, root)) for name in DATASET_NAMES]


def load_processed_rows(path: Path) -> list[dict[str, str]]:
    """Read one cleaned CSV as row mappings for analytics/export functions."""
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def load_primary_cleaned(root: Path = PROJECT_ROOT) -> list[dict[str, str]]:
    """Load the assignment's primary cleaned dataset; never substitute raw data."""
    path = root / "data" / "processed" / "vgsales_clean.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Cleaned primary data not found at {path}; run `python -m python.pipeline` first.")
    return load_processed_rows(path)
