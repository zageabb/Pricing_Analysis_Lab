from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_absolute_percentage_error,
    precision_score,
    r2_score,
    recall_score,
    root_mean_squared_error,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from pricing_analysis_lab.analysis.base import AnalysisContext, AnalysisFunction
from pricing_analysis_lab.analysis.common import dataset_to_dataframe, resolve_feature_fields, validate_fields_exist
from pricing_analysis_lab.analysis.supervised import evaluation_predictions
from pricing_analysis_lab.schemas import AnalysisPlan


class _RandomForestBase(AnalysisFunction):
    minimum_rows = 8

    def validate(self, context: AnalysisContext, plan: AnalysisPlan) -> None:
        target_field = plan.target_field or (context.request.target_fields[0] if context.request.target_fields else None)
        if not target_field:
            raise ValueError("A target field is required.")
        validate_fields_exist(context, [target_field])
        if context.dataset.row_count < self.minimum_rows:
            raise ValueError("Insufficient rows for Random Forest analysis.")

    def _prepare_frame(self, context: AnalysisContext, target_field: str) -> tuple[pd.DataFrame, list[str]]:
        df = dataset_to_dataframe(context)
        feature_fields = resolve_feature_fields(context, target_field=target_field)
        validate_fields_exist(context, feature_fields + [target_field])
        prepared = df[feature_fields + [target_field]].dropna(subset=[target_field]).copy()
        if prepared.shape[0] < self.minimum_rows:
            raise ValueError("Insufficient rows after removing missing target values.")
        return prepared, feature_fields

    def _build_pipeline(self, frame: pd.DataFrame, feature_fields: list[str], estimator: Any) -> Pipeline:
        X = frame[feature_fields]
        numeric_features = X.select_dtypes(include=["number", "bool"]).columns.tolist()
        categorical_features = [field for field in feature_fields if field not in numeric_features]

        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "numeric",
                    Pipeline([("imputer", SimpleImputer(strategy="median"))]),
                    numeric_features,
                ),
                (
                    "categorical",
                    Pipeline(
                        [
                            ("imputer", SimpleImputer(strategy="most_frequent")),
                            ("encoder", OneHotEncoder(handle_unknown="ignore")),
                        ]
                    ),
                    categorical_features,
                ),
            ]
        )

        return Pipeline([("preprocessor", preprocessor), ("model", estimator)])

    def _feature_importance(self, pipeline: Pipeline) -> list[dict[str, Any]]:
        preprocessor = pipeline.named_steps["preprocessor"]
        model = pipeline.named_steps["model"]
        transformed_names = preprocessor.get_feature_names_out().tolist()
        return [
            {"feature": feature, "importance": float(value)}
            for feature, value in zip(transformed_names, model.feature_importances_, strict=True)
        ]

    def _prediction_input(self, feature_fields: list[str], input_parameters: dict[str, Any]) -> pd.DataFrame:
        row = {field: input_parameters.get(field) for field in feature_fields}
        return pd.DataFrame([row], columns=feature_fields)


class RandomForestRegressionFunction(_RandomForestBase):
    name = "random_forest_regression"
    description = "Predict numeric target fields using RandomForestRegressor."
    supported_tasks = ("auto", "prediction", "regression")
    required_inputs = ("target_field",)
    output_schema = {"model_results": "object", "predictions": "array", "feature_importance": "array"}

    def run(self, context: AnalysisContext, plan: AnalysisPlan) -> dict[str, Any]:
        target_field = plan.target_field or context.request.target_fields[0]
        frame, feature_fields = self._prepare_frame(context, target_field)
        X = frame[feature_fields]
        y = frame[target_field]

        estimator = RandomForestRegressor(
            n_estimators=int(plan.model_settings.get("n_estimators", 300)),
            max_depth=plan.model_settings.get("max_depth"),
            min_samples_leaf=int(plan.model_settings.get("min_samples_leaf", 2)),
            random_state=int(plan.model_settings.get("random_state", 42)),
        )
        pipeline = self._build_pipeline(frame, feature_fields, estimator)

        test_size = float(plan.model_settings.get("test_size", 0.2))
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)

        metrics = {
            "r2": float(r2_score(y_test, predictions)),
            "mae": float(mean_absolute_error(y_test, predictions)),
            "rmse": float(root_mean_squared_error(y_test, predictions)),
        }
        if (y_test != 0).all():
            metrics["mape"] = float(mean_absolute_percentage_error(y_test, predictions))

        prediction_output = evaluation_predictions(
            context,
            X_test,
            y_test.tolist(),
            predictions.tolist(),
            target_field,
            predicted_key="predicted_value",
            actual_key="actual_value",
        )
        if context.request.input_parameters:
            incoming = self._prediction_input(feature_fields, context.request.input_parameters)
            predicted_value = float(pipeline.predict(incoming)[0])
            prediction_output.append({"target_field": target_field, "predicted_value": predicted_value})

        return {
            "analysis_type": self.name,
            "statistics": metrics,
            "predictions": prediction_output,
            "feature_importance": self._feature_importance(pipeline),
            "warnings": [],
            "model_results": {
                "train_rows": int(X_train.shape[0]),
                "test_rows": int(X_test.shape[0]),
                "target_field": target_field,
                "feature_fields": feature_fields,
            },
        }


class RandomForestClassificationFunction(_RandomForestBase):
    name = "random_forest_classification"
    description = "Predict categorical target fields using RandomForestClassifier."
    supported_tasks = ("auto", "prediction", "classification")
    required_inputs = ("target_field",)
    output_schema = {"model_results": "object", "predictions": "array", "feature_importance": "array"}

    def run(self, context: AnalysisContext, plan: AnalysisPlan) -> dict[str, Any]:
        target_field = plan.target_field or context.request.target_fields[0]
        frame, feature_fields = self._prepare_frame(context, target_field)
        X = frame[feature_fields]
        y = frame[target_field].astype(str)

        estimator = RandomForestClassifier(
            n_estimators=int(plan.model_settings.get("n_estimators", 300)),
            max_depth=plan.model_settings.get("max_depth"),
            min_samples_leaf=int(plan.model_settings.get("min_samples_leaf", 2)),
            random_state=int(plan.model_settings.get("random_state", 42)),
        )
        pipeline = self._build_pipeline(frame, feature_fields, estimator)

        test_size = float(plan.model_settings.get("test_size", 0.2))
        n_classes = int(y.nunique())
        test_rows = max(1, int(round(len(y) * test_size)))
        use_stratify = y if y.nunique() > 1 and test_rows >= n_classes else None
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=42,
            stratify=use_stratify,
        )
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)

        metrics = {
            "accuracy": float(accuracy_score(y_test, predictions)),
            "precision": float(precision_score(y_test, predictions, average="weighted", zero_division=0)),
            "recall": float(recall_score(y_test, predictions, average="weighted", zero_division=0)),
            "f1": float(f1_score(y_test, predictions, average="weighted", zero_division=0)),
        }

        prediction_output = evaluation_predictions(
            context,
            X_test,
            y_test.tolist(),
            predictions.tolist(),
            target_field,
            predicted_key="predicted_class",
            actual_key="actual_class",
        )
        if context.request.input_parameters:
            incoming = self._prediction_input(feature_fields, context.request.input_parameters)
            predicted_class = str(pipeline.predict(incoming)[0])
            output = {"target_field": target_field, "predicted_class": predicted_class}
            model = pipeline.named_steps["model"]
            if hasattr(model, "predict_proba"):
                probabilities = pipeline.predict_proba(incoming)[0]
                classes = model.classes_
                output["class_probabilities"] = {
                    str(label): float(probability)
                    for label, probability in zip(classes, probabilities, strict=True)
                }
            prediction_output.append(output)

        return {
            "analysis_type": self.name,
            "statistics": metrics,
            "predictions": prediction_output,
            "feature_importance": self._feature_importance(pipeline),
            "warnings": [],
            "model_results": {
                "train_rows": int(X_train.shape[0]),
                "test_rows": int(X_test.shape[0]),
                "target_field": target_field,
                "feature_fields": feature_fields,
            },
        }
