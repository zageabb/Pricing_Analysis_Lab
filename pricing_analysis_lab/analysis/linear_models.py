from __future__ import annotations

from typing import Any

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split

from pricing_analysis_lab.analysis.base import AnalysisContext, AnalysisFunction
from pricing_analysis_lab.analysis.common import validate_fields_exist
from pricing_analysis_lab.analysis.supervised import (
    build_supervised_pipeline,
    evaluation_predictions,
    prediction_input,
    prepare_supervised_frame,
)
from pricing_analysis_lab.schemas import AnalysisPlan


class LinearRegressionFunction(AnalysisFunction):
    name = "linear_regression"
    description = "Predict numeric target fields using a simple linear regression baseline."
    supported_tasks = ("auto", "prediction", "regression")
    required_inputs = ("target_field",)
    output_schema = {"model_results": "object", "predictions": "array", "feature_importance": "array"}

    def validate(self, context: AnalysisContext, plan: AnalysisPlan) -> None:
        target_field = plan.target_field or (context.request.target_fields[0] if context.request.target_fields else None)
        if not target_field:
            raise ValueError("A target field is required.")
        validate_fields_exist(context, [target_field])
        if context.dataset.row_count < 6:
            raise ValueError("Insufficient rows for linear regression.")

    def run(self, context: AnalysisContext, plan: AnalysisPlan) -> dict[str, Any]:
        target_field = plan.target_field or context.request.target_fields[0]
        frame, feature_fields = prepare_supervised_frame(context, target_field, minimum_rows=6)
        X = frame[feature_fields]
        y = frame[target_field]

        pipeline = build_supervised_pipeline(
            frame,
            feature_fields,
            LinearRegression(),
            scale_numeric=True,
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

        feature_names = pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()
        coefficients = pipeline.named_steps["model"].coef_
        feature_importance = [
            {"feature": feature, "importance": float(abs(value)), "coefficient": float(value)}
            for feature, value in zip(feature_names, coefficients, strict=True)
        ]

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
            incoming = prediction_input(feature_fields, context.request.input_parameters)
            predicted_value = float(pipeline.predict(incoming)[0])
            prediction_output.append(
                {
                    "prediction_scope": "scenario",
                    "target_field": target_field,
                    "predicted_value": predicted_value,
                }
            )

        return {
            "analysis_type": self.name,
            "statistics": metrics,
            "predictions": prediction_output,
            "feature_importance": feature_importance,
            "warnings": ["Linear regression assumes simpler relationships than tree-based models."],
            "model_results": {
                "train_rows": int(X_train.shape[0]),
                "test_rows": int(X_test.shape[0]),
                "target_field": target_field,
                "feature_fields": feature_fields,
            },
        }
