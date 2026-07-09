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
