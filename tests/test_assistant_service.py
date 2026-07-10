from pricing_analysis_lab.services.assistant_service import handle_assistant_message


def test_assistant_command_adds_output_field():
    state = {
        "data_source": {"type": "uploaded_file", "file_id": "pricing.csv", "sheet_name": None, "header_row": 1},
        "task": "auto",
        "parameter_fields": [],
        "input_parameters": {},
        "target_fields": [],
        "output_fields": [],
        "excluded_fields": [],
        "filter_parameters": {},
        "model_preferences": {"preferred_model": "auto", "allow_llm_to_tune": True, "forced_analysis_function": "auto"},
        "response_format": "human_and_json",
    }

    updated, reply = handle_assistant_message(state, "add output field Project Name")

    assert updated["output_fields"] == ["Project Name"]
    assert "Added 'Project Name'" in reply


def test_assistant_command_forces_analysis_type():
    state = {
        "data_source": {"type": "uploaded_file", "file_id": "pricing.csv", "sheet_name": None, "header_row": 1},
        "task": "auto",
        "parameter_fields": [],
        "input_parameters": {},
        "target_fields": [],
        "output_fields": [],
        "excluded_fields": [],
        "filter_parameters": {},
        "model_preferences": {"preferred_model": "auto", "allow_llm_to_tune": True, "forced_analysis_function": "auto"},
        "response_format": "human_and_json",
    }

    updated, reply = handle_assistant_message(state, "force analysis type to linear_regression")

    assert updated["model_preferences"]["forced_analysis_function"] == "linear_regression"
    assert "linear_regression" in reply


def test_assistant_can_give_settings_advice():
    state = {
        "data_source": {"type": "uploaded_file", "file_id": "pricing.csv", "sheet_name": None, "header_row": 1},
        "task": "regression",
        "parameter_fields": ["quantity"],
        "input_parameters": {"quantity": 10},
        "target_fields": ["price"],
        "output_fields": ["price"],
        "excluded_fields": [],
        "filter_parameters": {},
        "model_preferences": {"preferred_model": "auto", "allow_llm_to_tune": True, "forced_analysis_function": "auto"},
        "manual_plan": {},
        "response_format": "human_and_json",
    }
    profile = {
        "row_count": 10,
        "column_count": 2,
        "columns": [
            {"name": "quantity", "inferred_type": "numeric"},
            {"name": "price", "inferred_type": "numeric"},
        ],
        "preview": [],
    }

    from pricing_analysis_lab.services.assistant_service import _build_settings_advice

    reply = _build_settings_advice(state, profile)

    assert "Settings advice" in reply
    assert "linear_regression" in reply
