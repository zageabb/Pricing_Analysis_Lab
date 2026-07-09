from __future__ import annotations

from typing import Any

from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
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

from pricing_analysis_lab.analysis.base import AnalysisContext, AnalysisFunction
from pricing_analysis_lab.analysis.common import validate_fields_exist
from pricing_analysis_lab.analysis.supervised import build_supervised_pipeline, prediction_input, prepare_supervised_frame
from pricing_analysis_lab.schemas import AnalysisPlan


class _GradientBoostingBase(AnalysisFunction):
    minimum_rows = 10

    def validate(self, context: AnalysisContext, plan: AnalysisPlan) -> None:
        target_field = plan.target_field or (context.request.target_fields[0] if context.request.target_fields else None)
        if not target_field:
            raise ValueError("A target field is required.")
        validate_fields_exist(context, [target_field])
        if context.dataset.row_count < self.minimum_rows:
            raise ValueError("Insufficient rows for gradient boosting.")

    def _feature_importance(self, pipeline):
        feature_names = pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()
        importances = pipeline.named_steps["model"].feature_importances_
        return [
            {"feature": feature, "importance": float(value)}
            for feature, value in zip(feature_names, importances, strict=True)
        ]


class GradientBoostingRegressionFunction(_GradientBoostingBase):
    name = "gradient_boosting_regression"
    description = "Predict numeric target fields using gradient boosting regression."
    supported_tasks = ("auto", "prediction", "regression")
    required_inputs = ("target_field",)
    output_schema = {"model_results": "object", "predictions": "array", "feature_importance": "array"}

    def run(self, context: AnalysisContext, plan: AnalysisPlan) -> dict[str, Any]:
        target_field = plan.target_field or context.request.target_fields[0]
        frame, feature_fields = prepare_supervised_frame(context, target_field, minimum_rows=self.minimum_rows)
        X = frame[feature_fields]
        y = frame[target_field]
        pipeline = build_supervised_pipeline(
            frame,
            feature_fields,
            GradientBoostingRegressor(random_state=int(plan.model_settings.get("random_state", 42))),
            sparse_output=False,
        )
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

        prediction_output = []
        if context.request.input_parameters:
            incoming = prediction_input(feature_fields, context.request.input_parameters)
            prediction_output.append(
                {"target_field": target_field, "predicted_value": float(pipeline.predict(incoming)[0])}
            )

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


class GradientBoostingClassificationFunction(_GradientBoostingBase):
    name = "gradient_boosting_classification"
    description = "Predict categorical target fields using gradient boosting classification."
    supported_tasks = ("auto", "prediction", "classification")
    required_inputs = ("target_field",)
    output_schema = {"model_results": "object", "predictions": "array", "feature_importance": "array"}

    def run(self, context: AnalysisContext, plan: AnalysisPlan) -> dict[str, Any]:
        target_field = plan.target_field or context.request.target_fields[0]
        frame, feature_fields = prepare_supervised_frame(context, target_field, minimum_rows=self.minimum_rows)
        X = frame[feature_fields]
        y = frame[target_field].astype(str)
        pipeline = build_supervised_pipeline(
            frame,
            feature_fields,
            GradientBoostingClassifier(random_state=int(plan.model_settings.get("random_state", 42))),
            sparse_output=False,
        )
        test_size = float(plan.model_settings.get("test_size", 0.2))
        class_count = int(y.nunique())
        test_rows = max(1, int(round(len(y) * test_size)))
        use_stratify = y if class_count > 1 and test_rows >= class_count else None
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

        prediction_output = []
        if context.request.input_parameters:
            incoming = prediction_input(feature_fields, context.request.input_parameters)
            predicted_class = str(pipeline.predict(incoming)[0])
            output = {"target_field": target_field, "predicted_class": predicted_class}
            model = pipeline.named_steps["model"]
            if hasattr(model, "predict_proba"):
                probabilities = pipeline.predict_proba(incoming)[0]
                output["class_probabilities"] = {
                    str(label): float(probability)
                    for label, probability in zip(model.classes_, probabilities, strict=True)
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
