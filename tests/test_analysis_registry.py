from pathlib import Path

import pytest

from pricing_analysis_lab.schemas import AnalysisPlan
from pricing_analysis_lab.services.analysis_runner import run_analysis_function
from pricing_analysis_lab.services.request_validator import validate_analysis_request
from pricing_analysis_lab.services.spreadsheet_loader import load_spreadsheet


def _write_regression_csv(path: Path) -> Path:
    path.write_text(
        "supplier,category,region,quantity,price\n"
        "Acme,Transformer,UK,10,100\n"
        "Acme,Transformer,UK,20,180\n"
        "Bravo,Transformer,DE,10,110\n"
        "Bravo,Cable,DE,30,210\n"
        "Cora,Cable,UK,15,140\n"
        "Cora,Switch,UK,40,260\n"
        "Delta,Switch,DE,25,190\n"
        "Delta,Transformer,FR,35,250\n"
        "Echo,Cable,FR,50,320\n"
        "Echo,Switch,UK,45,300\n",
        encoding="utf-8",
    )
    return path


def _write_classification_csv(path: Path) -> Path:
    path.write_text(
        "supplier,category,region,quantity,band\n"
        "Acme,Transformer,UK,10,low\n"
        "Acme,Transformer,UK,20,medium\n"
        "Bravo,Transformer,DE,10,low\n"
        "Bravo,Cable,DE,30,medium\n"
        "Cora,Cable,UK,15,low\n"
        "Cora,Switch,UK,40,high\n"
        "Delta,Switch,DE,25,medium\n"
        "Delta,Transformer,FR,35,high\n"
        "Echo,Cable,FR,50,high\n"
        "Echo,Switch,UK,45,high\n",
        encoding="utf-8",
    )
    return path


def test_descriptive_statistics_fallback(tmp_path: Path):
    dataset = load_spreadsheet(_write_regression_csv(tmp_path / "regression.csv"))
    request_model = validate_analysis_request(
        {
            "data_source": {"type": "uploaded_file", "file_id": "regression.csv"},
            "task": "data summary/statistical analysis",
        }
    )
    plan = AnalysisPlan(selected_function="descriptive_statistics", reason="summary")
    result = run_analysis_function(request_model, dataset, plan)
    assert result["analysis_type"] == "descriptive_statistics"
    assert "numeric_summary" in result["statistics"]


def test_random_forest_regression(tmp_path: Path):
    dataset = load_spreadsheet(_write_regression_csv(tmp_path / "regression.csv"))
    request_model = validate_analysis_request(
        {
            "data_source": {"type": "uploaded_file", "file_id": "regression.csv"},
            "task": "regression",
            "parameter_fields": ["supplier", "category", "region", "quantity"],
            "input_parameters": {"supplier": "Acme", "category": "Transformer", "region": "UK", "quantity": 12},
            "target_fields": ["price"],
            "output_fields": ["supplier", "price"],
        }
    )
    plan = AnalysisPlan(
        selected_function="random_forest_regression",
        reason="numeric target",
        target_field="price",
        feature_fields=["supplier", "category", "region", "quantity"],
        model_settings={"n_estimators": 50, "min_samples_leaf": 1, "test_size": 0.2, "random_state": 42},
    )
    result = run_analysis_function(request_model, dataset, plan)
    assert result["analysis_type"] == "random_forest_regression"
    assert "r2" in result["statistics"]
    assert result["predictions"]


def test_random_forest_classification(tmp_path: Path):
    dataset = load_spreadsheet(_write_classification_csv(tmp_path / "classification.csv"))
    request_model = validate_analysis_request(
        {
            "data_source": {"type": "uploaded_file", "file_id": "classification.csv"},
            "task": "classification",
            "parameter_fields": ["supplier", "category", "region", "quantity"],
            "input_parameters": {"supplier": "Echo", "category": "Switch", "region": "UK", "quantity": 44},
            "target_fields": ["band"],
            "output_fields": ["supplier", "band"],
        }
    )
    plan = AnalysisPlan(
        selected_function="random_forest_classification",
        reason="categorical target",
        target_field="band",
        feature_fields=["supplier", "category", "region", "quantity"],
        model_settings={"n_estimators": 50, "min_samples_leaf": 1, "test_size": 0.2, "random_state": 42},
    )
    result = run_analysis_function(request_model, dataset, plan)
    assert result["analysis_type"] == "random_forest_classification"
    assert "accuracy" in result["statistics"]
    assert result["predictions"][0]["predicted_class"]


def test_linear_regression(tmp_path: Path):
    dataset = load_spreadsheet(_write_regression_csv(tmp_path / "linear.csv"))
    request_model = validate_analysis_request(
        {
            "data_source": {"type": "uploaded_file", "file_id": "linear.csv"},
            "task": "regression",
            "parameter_fields": ["quantity"],
            "input_parameters": {"quantity": 18},
            "target_fields": ["price"],
            "model_preferences": {"preferred_model": "linear_regression", "allow_llm_to_tune": True},
        }
    )
    plan = AnalysisPlan(selected_function="linear_regression", reason="simple baseline", target_field="price")
    result = run_analysis_function(request_model, dataset, plan)
    assert result["analysis_type"] == "linear_regression"
    assert "r2" in result["statistics"]
    assert result["predictions"]


def test_gradient_boosting_regression(tmp_path: Path):
    dataset = load_spreadsheet(_write_regression_csv(tmp_path / "boost.csv"))
    request_model = validate_analysis_request(
        {
            "data_source": {"type": "uploaded_file", "file_id": "boost.csv"},
            "task": "regression",
            "parameter_fields": ["supplier", "category", "region", "quantity"],
            "input_parameters": {"supplier": "Delta", "category": "Transformer", "region": "FR", "quantity": 36},
            "target_fields": ["price"],
            "model_preferences": {"preferred_model": "gradient_boosting", "allow_llm_to_tune": True},
        }
    )
    plan = AnalysisPlan(selected_function="gradient_boosting_regression", reason="boosting", target_field="price")
    result = run_analysis_function(request_model, dataset, plan)
    assert result["analysis_type"] == "gradient_boosting_regression"
    assert result["feature_importance"]


@pytest.mark.parametrize(
    ("selected_function", "target_field", "expected_prediction_key", "csv_builder", "task"),
    [
        ("linear_regression", "price", "predicted_value", _write_regression_csv, "regression"),
        ("random_forest_regression", "price", "predicted_value", _write_regression_csv, "regression"),
        ("gradient_boosting_regression", "price", "predicted_value", _write_regression_csv, "regression"),
        ("random_forest_classification", "band", "predicted_class", _write_classification_csv, "classification"),
        ("gradient_boosting_classification", "band", "predicted_class", _write_classification_csv, "classification"),
    ],
)
def test_supervised_models_return_holdout_predictions_without_input_parameters(
    tmp_path: Path,
    selected_function: str,
    target_field: str,
    expected_prediction_key: str,
    csv_builder,
    task: str,
):
    dataset = load_spreadsheet(csv_builder(tmp_path / f"{selected_function}.csv"))
    request_model = validate_analysis_request(
        {
            "data_source": {"type": "uploaded_file", "file_id": f"{selected_function}.csv"},
            "task": task,
            "parameter_fields": ["supplier", "category", "region", "quantity"] if target_field == "price" or target_field == "band" else ["quantity"],
            "target_fields": [target_field],
            "output_fields": ["supplier", target_field],
        }
    )
    plan = AnalysisPlan(selected_function=selected_function, reason="coverage", target_field=target_field)

    result = run_analysis_function(request_model, dataset, plan)

    assert result["analysis_type"] == selected_function
    assert result["predictions"]
    assert expected_prediction_key in result["predictions"][0]


def test_nearest_neighbor_similarity(tmp_path: Path):
    dataset = load_spreadsheet(_write_regression_csv(tmp_path / "similarity.csv"))
    request_model = validate_analysis_request(
        {
            "data_source": {"type": "uploaded_file", "file_id": "similarity.csv"},
            "task": "similarity/search",
            "parameter_fields": ["supplier", "category", "region", "quantity"],
            "input_parameters": {"supplier": "Acme", "category": "Transformer", "region": "UK", "quantity": 11},
            "output_fields": ["supplier", "category", "price"],
        }
    )
    plan = AnalysisPlan(selected_function="nearest_neighbor_similarity", reason="similarity")
    result = run_analysis_function(request_model, dataset, plan)
    assert result["analysis_type"] == "nearest_neighbor_similarity"
    assert result["predictions"]
    assert "similarity_distance" in result["predictions"][0]


def test_invalid_target_field(tmp_path: Path):
    dataset = load_spreadsheet(_write_regression_csv(tmp_path / "regression.csv"))
    request_model = validate_analysis_request(
        {
            "data_source": {"type": "uploaded_file", "file_id": "regression.csv"},
            "task": "regression",
            "parameter_fields": ["supplier", "quantity"],
            "target_fields": ["missing_price"],
        }
    )
    plan = AnalysisPlan(selected_function="random_forest_regression", reason="numeric target", target_field="missing_price")
    with pytest.raises(ValueError, match="missing_price"):
        run_analysis_function(request_model, dataset, plan)


def test_insufficient_rows_for_random_forest(tmp_path: Path):
    path = tmp_path / "small.csv"
    path.write_text("feature,target\n1,10\n2,12\n3,13\n4,15\n", encoding="utf-8")
    dataset = load_spreadsheet(path)
    request_model = validate_analysis_request(
        {
            "data_source": {"type": "uploaded_file", "file_id": "small.csv"},
            "task": "regression",
            "parameter_fields": ["feature"],
            "target_fields": ["target"],
        }
    )
    plan = AnalysisPlan(selected_function="random_forest_regression", reason="numeric target", target_field="target")
    with pytest.raises(ValueError, match="Insufficient rows"):
        run_analysis_function(request_model, dataset, plan)
