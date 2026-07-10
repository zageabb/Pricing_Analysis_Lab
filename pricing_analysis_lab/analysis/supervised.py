from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from pricing_analysis_lab.analysis.base import AnalysisContext
from pricing_analysis_lab.analysis.common import dataset_to_dataframe, resolve_feature_fields, validate_fields_exist


def prepare_supervised_frame(
    context: AnalysisContext,
    target_field: str,
    minimum_rows: int = 6,
) -> tuple[pd.DataFrame, list[str]]:
    df = dataset_to_dataframe(context)
    feature_fields = resolve_feature_fields(context, target_field=target_field)
    validate_fields_exist(context, feature_fields + [target_field])
    prepared = df[feature_fields + [target_field]].dropna(subset=[target_field]).copy()
    if prepared.shape[0] < minimum_rows:
        raise ValueError("Insufficient rows after removing missing target values.")
    return prepared, feature_fields


def build_supervised_pipeline(
    frame: pd.DataFrame,
    feature_fields: list[str],
    estimator: Any,
    scale_numeric: bool = False,
    sparse_output: bool = True,
) -> Pipeline:
    X = frame[feature_fields]
    numeric_features = X.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical_features = [field for field in feature_fields if field not in numeric_features]

    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", Pipeline(numeric_steps), numeric_features),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=sparse_output)),
                    ]
                ),
                categorical_features,
            ),
        ]
    )

    return Pipeline([("preprocessor", preprocessor), ("model", estimator)])


def prediction_input(feature_fields: list[str], input_parameters: dict[str, Any]) -> pd.DataFrame:
    row = {field: input_parameters.get(field) for field in feature_fields}
    return pd.DataFrame([row], columns=feature_fields)


def evaluation_predictions(
    context: AnalysisContext,
    row_frame: pd.DataFrame,
    actual_values,
    predicted_values,
    target_field: str,
    predicted_key: str,
    actual_key: str,
    max_rows: int = 10,
) -> list[dict[str, Any]]:
    dataset_frame = dataset_to_dataframe(context)
    output_fields = context.request.output_fields or context.request.parameter_fields or row_frame.columns.tolist()
    rows: list[dict[str, Any]] = []
    for index, actual_value, predicted_value in zip(row_frame.index.tolist(), actual_values, predicted_values, strict=True):
        source_row = dataset_frame.loc[index]
        payload = {field: _coerce_output_value(source_row[field]) for field in output_fields if field in source_row.index}
        payload["target_field"] = target_field
        payload[actual_key] = _coerce_output_value(actual_value)
        payload[predicted_key] = _coerce_output_value(predicted_value)
        rows.append(payload)
        if len(rows) >= max_rows:
            break
    return rows


def _coerce_output_value(value: Any) -> Any:
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:  # noqa: BLE001
            return value
    return value
