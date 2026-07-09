from __future__ import annotations

from typing import Any

import pandas as pd

from pricing_analysis_lab.analysis.base import AnalysisContext


def dataset_to_dataframe(context: AnalysisContext) -> pd.DataFrame:
    return pd.DataFrame(context.dataset.rows, columns=context.dataset.columns)


def resolve_feature_fields(context: AnalysisContext, target_field: str | None = None) -> list[str]:
    request = context.request
    excluded = set(request.excluded_fields)
    features = [
        field
        for field in request.parameter_fields
        if field in context.dataset.columns and field not in excluded and field != target_field
    ]
    if not features:
        features = [
            column
            for column in context.dataset.columns
            if column not in excluded and column != target_field
        ]
    return features


def validate_fields_exist(context: AnalysisContext, fields: list[str]) -> None:
    missing = [field for field in fields if field not in context.dataset.columns]
    if missing:
        raise ValueError(f"Fields not found in dataset: {', '.join(missing)}")


def filter_dataframe(df: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
    filtered = df.copy()
    for key, expected in filters.items():
        if key not in filtered.columns:
            continue
        filtered = filtered[filtered[key].astype(str) == str(expected)]
    return filtered
