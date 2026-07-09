from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

from .spreadsheet_loader import SpreadsheetData


@dataclass(slots=True)
class ColumnProfile:
    name: str
    inferred_type: str
    null_count: int
    unique_count: int
    example_values: list[Any]


def profile_dataset(dataset: SpreadsheetData) -> dict[str, Any]:
    column_profiles = [profile_column(dataset.rows, column) for column in dataset.columns]
    type_counts = Counter(profile.inferred_type for profile in column_profiles)
    return {
        "file_name": dataset.file_name,
        "sheet_name": dataset.sheet_name,
        "header_row": dataset.header_row,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count,
        "sheet_names": dataset.sheet_names,
        "columns": [asdict(profile) for profile in column_profiles],
        "type_counts": dict(type_counts),
        "preview": dataset.preview(),
    }


def profile_column(rows: list[dict[str, Any]], column_name: str) -> ColumnProfile:
    values = [row.get(column_name) for row in rows]
    non_null_values = [value for value in values if value not in (None, "")]
    inferred_type = infer_type(non_null_values)
    examples = unique_examples(non_null_values)
    unique_count = len({repr(value) for value in non_null_values})
    null_count = len(values) - len(non_null_values)
    return ColumnProfile(
        name=column_name,
        inferred_type=inferred_type,
        null_count=null_count,
        unique_count=unique_count,
        example_values=examples,
    )


def infer_type(values: list[Any]) -> str:
    if not values:
        return "empty"
    if all(isinstance(value, bool) for value in values):
        return "boolean"
    if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
        return "numeric"
    if all(isinstance(value, str) and _looks_like_iso_date(value) for value in values):
        return "date"
    if all(isinstance(value, str) for value in values):
        unique_count = len(set(values))
        if unique_count <= min(20, max(3, len(values) // 2)):
            return "category"
        return "text"
    return "mixed"


def unique_examples(values: list[Any], limit: int = 3) -> list[Any]:
    examples: list[Any] = []
    seen: set[str] = set()
    for value in values:
        marker = repr(value)
        if marker in seen:
            continue
        seen.add(marker)
        examples.append(value)
        if len(examples) == limit:
            break
    return examples


def _looks_like_iso_date(value: str) -> bool:
    parts = value.split("T", 1)[0].split("-")
    return len(parts) == 3 and all(part.isdigit() for part in parts)
