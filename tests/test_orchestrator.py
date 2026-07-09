from pricing_analysis_lab.services.orchestrator import create_analysis_plan
from pricing_analysis_lab.services.request_validator import validate_analysis_request


def test_orchestrator_prefers_linear_regression_for_requested_model():
    request_model = validate_analysis_request(
        {
            "data_source": {"type": "uploaded_file", "file_id": "example.csv"},
            "task": "regression",
            "parameter_fields": ["quantity"],
            "target_fields": ["price"],
            "model_preferences": {"preferred_model": "linear_regression", "allow_llm_to_tune": True},
        }
    )
    dataset_profile = {
        "row_count": 12,
        "columns": [
            {"name": "quantity", "inferred_type": "numeric"},
            {"name": "price", "inferred_type": "numeric"},
        ],
    }
    plan = create_analysis_plan(request_model, dataset_profile)
    assert plan.selected_function == "linear_regression"


def test_orchestrator_uses_similarity_function_for_search_requests():
    request_model = validate_analysis_request(
        {
            "data_source": {"type": "uploaded_file", "file_id": "example.csv"},
            "task": "similarity/search",
            "parameter_fields": ["supplier", "quantity"],
            "input_parameters": {"supplier": "Acme", "quantity": 10},
        }
    )
    dataset_profile = {
        "row_count": 10,
        "columns": [
            {"name": "supplier", "inferred_type": "category"},
            {"name": "quantity", "inferred_type": "numeric"},
        ],
    }
    plan = create_analysis_plan(request_model, dataset_profile)
    assert plan.selected_function == "nearest_neighbor_similarity"


def test_orchestrator_uses_small_sample_regression_baseline_in_auto_mode():
    request_model = validate_analysis_request(
        {
            "data_source": {"type": "uploaded_file", "file_id": "example.csv"},
            "task": "auto",
            "parameter_fields": ["quantity", "supplier"],
            "target_fields": ["price"],
            "model_preferences": {"preferred_model": "auto", "allow_llm_to_tune": True},
        }
    )
    dataset_profile = {
        "row_count": 5,
        "columns": [
            {"name": "supplier", "inferred_type": "category"},
            {"name": "quantity", "inferred_type": "numeric"},
            {"name": "price", "inferred_type": "numeric"},
        ],
    }
    plan = create_analysis_plan(request_model, dataset_profile)
    assert plan.selected_function == "linear_regression"
    assert plan.target_field == "price"
    assert plan.feature_fields == ["quantity", "supplier"]


def test_orchestrator_preserves_field_intent_for_non_supervised_fallback():
    request_model = validate_analysis_request(
        {
            "data_source": {"type": "uploaded_file", "file_id": "example.csv"},
            "task": "auto",
            "parameter_fields": ["supplier", "quantity"],
            "output_fields": ["supplier", "price"],
            "excluded_fields": ["notes"],
            "model_preferences": {"preferred_model": "auto", "allow_llm_to_tune": True},
        }
    )
    dataset_profile = {
        "row_count": 2,
        "columns": [
            {"name": "supplier", "inferred_type": "category"},
            {"name": "quantity", "inferred_type": "numeric"},
            {"name": "price", "inferred_type": "numeric"},
            {"name": "notes", "inferred_type": "text"},
        ],
    }
    plan = create_analysis_plan(request_model, dataset_profile)
    assert plan.selected_function == "nearest_neighbor_similarity"
    assert plan.target_field == "price"
    assert plan.feature_fields == ["supplier", "quantity"]
