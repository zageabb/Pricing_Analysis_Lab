from __future__ import annotations

from typing import Any

from ..schemas import AnalysisPlan, AnalysisRequest


def create_analysis_plan(request_model: AnalysisRequest, dataset_profile: dict[str, Any]) -> AnalysisPlan:
    target_field = request_model.target_fields[0] if request_model.target_fields else None
    columns = {column["name"]: column for column in dataset_profile.get("columns", [])}
    row_count = dataset_profile.get("row_count", 0)
    preferred_model = request_model.model_preferences.preferred_model.lower().strip()
    preferred_function = _preferred_function_for_request(request_model.task, preferred_model)

    if request_model.task == "data summary/statistical analysis":
        return AnalysisPlan(
            selected_function="descriptive_statistics",
            reason="The request explicitly asked for descriptive statistics.",
        )

    if request_model.task == "similarity/search":
        if preferred_function == "filtered_search":
            return AnalysisPlan(
                selected_function="filtered_search",
                reason="The preferred model requested a direct filtered search.",
            )
        return AnalysisPlan(
            selected_function="nearest_neighbor_similarity" if request_model.input_parameters else "filtered_search",
            reason="The request explicitly asked for search-style matching.",
        )

    if target_field and target_field in columns and row_count >= 8:
        inferred_type = columns[target_field]["inferred_type"]
        feature_fields = request_model.parameter_fields or [
            column["name"] for column in dataset_profile["columns"] if column["name"] != target_field
        ]
        if request_model.task == "classification" or inferred_type in {"category", "text"}:
            selected_function = preferred_function or (
                "gradient_boosting_classification" if row_count >= 40 else "random_forest_classification"
            )
            return AnalysisPlan(
                selected_function=selected_function,
                reason="The target field looks categorical and there are enough rows for supervised classification.",
                target_field=target_field,
                feature_fields=feature_fields,
                model_settings={
                    "n_estimators": 300,
                    "max_depth": None,
                    "min_samples_leaf": 2,
                    "test_size": 0.2,
                    "random_state": 42,
                },
            )
        if request_model.task in {"regression", "prediction", "auto"} and inferred_type == "numeric":
            selected_function = preferred_function or _auto_regression_function(row_count)
            return AnalysisPlan(
                selected_function=selected_function,
                reason="The target field is numeric and there are enough rows for supervised regression.",
                target_field=target_field,
                feature_fields=feature_fields,
                model_settings={
                    "n_estimators": 300,
                    "max_depth": None,
                    "min_samples_leaf": 2,
                    "test_size": 0.2,
                    "random_state": 42,
                },
            )

    if request_model.input_parameters:
        return AnalysisPlan(
            selected_function="nearest_neighbor_similarity" if preferred_function != "filtered_search" else "filtered_search",
            reason="There is not enough signal for a supervised model, so returning matching rows is safer.",
        )

    return AnalysisPlan(
        selected_function="descriptive_statistics",
        reason="No reliable supervised target was available, so falling back to descriptive statistics.",
    )


def interpret_analysis_result(result: dict[str, Any], plan: AnalysisPlan, dataset_profile: dict[str, Any]) -> dict[str, Any]:
    warnings = list(result.get("warnings", []))
    summary = f"Selected {plan.selected_function} because {plan.reason.lower()}"
    reasons = [plan.reason]
    improvement_suggestions = []

    if dataset_profile.get("row_count", 0) < 25:
        warnings.append("Low sample size means the result should be treated as directional.")
    if plan.selected_function.startswith("random_forest"):
        improvement_suggestions.append("Add more rows and richer feature coverage to improve model reliability.")
        if result.get("feature_importance"):
            top_feature = max(result["feature_importance"], key=lambda item: item["importance"])
            reasons.append(f"Top contributing feature: {top_feature['feature']}.")
    elif plan.selected_function == "filtered_search":
        improvement_suggestions.append("Add a prediction target field to enable supervised modeling.")
    else:
        improvement_suggestions.append("Add a clean target field if you want the system to attempt prediction.")

    return {
        "summary": summary,
        "reasons": reasons,
        "caveats": warnings,
        "improvement_suggestions": improvement_suggestions,
    }


def _preferred_function_for_request(task: str, preferred_model: str) -> str | None:
    mapping = {
        "linear_regression": "linear_regression",
        "gradient_boosting": "gradient_boosting_classification" if task == "classification" else "gradient_boosting_regression",
        "gradient_boosting_regression": "gradient_boosting_regression",
        "gradient_boosting_classification": "gradient_boosting_classification",
        "random_forest": "random_forest_classification" if task == "classification" else "random_forest_regression",
        "random_forest_regression": "random_forest_regression",
        "random_forest_classification": "random_forest_classification",
        "nearest_neighbor_similarity": "nearest_neighbor_similarity",
        "filtered_search": "filtered_search",
        "auto": None,
    }
    return mapping.get(preferred_model)


def _auto_regression_function(row_count: int) -> str:
    if row_count >= 40:
        return "gradient_boosting_regression"
    if row_count <= 15:
        return "linear_regression"
    return "random_forest_regression"
