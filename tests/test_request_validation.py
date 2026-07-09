import pytest

from pricing_analysis_lab.schemas import AnalysisRequest, request_schema
from pricing_analysis_lab.services.request_validator import collect_validation_errors, validate_analysis_request


def test_valid_analysis_request_parses():
    payload = {
        "data_source": {"type": "uploaded_file", "file_id": "example.xlsx", "sheet_name": "Sheet1"},
        "task": "auto",
        "parameter_fields": ["supplier", "category", "region", "quantity"],
        "input_parameters": {"category": "Transformer", "region": "UK", "quantity": 10},
        "target_fields": ["price"],
        "output_fields": ["supplier", "description", "price"],
        "excluded_fields": [],
        "model_preferences": {"preferred_model": "auto", "allow_llm_to_tune": True},
        "response_format": "human_and_json",
    }

    model = validate_analysis_request(payload)
    assert isinstance(model, AnalysisRequest)
    assert model.data_source.file_id == "example.xlsx"
    assert model.target_fields == ["price"]


def test_supervised_task_requires_target_field():
    payload = {
        "data_source": {"type": "uploaded_file", "file_id": "example.xlsx"},
        "task": "regression",
        "parameter_fields": ["supplier"],
    }

    errors = collect_validation_errors(payload)
    assert errors
    assert "Target fields are required" in errors[0]["msg"]


def test_request_schema_exposes_expected_shape():
    schema = request_schema()
    assert "properties" in schema
    assert "data_source" in schema["properties"]
    assert "response_format" in schema["properties"]


def test_extra_fields_are_rejected():
    payload = {
        "data_source": {"type": "uploaded_file", "file_id": "example.xlsx"},
        "task": "auto",
        "unexpected": True,
    }

    with pytest.raises(Exception):
        validate_analysis_request(payload)
