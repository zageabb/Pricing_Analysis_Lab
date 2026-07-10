def test_clear_assistant_chat_keeps_workspace_state(app):
    client = app.test_client()
    with client.session_transaction() as session:
        session["analysis_wizard_state"] = {
            "data_source": {"type": "uploaded_file", "file_id": "pricing.csv", "sheet_name": None, "header_row": 2},
            "task": "auto",
            "parameter_fields": ["supplier"],
            "input_parameters": {"supplier": "Acme"},
            "target_fields": ["price"],
            "output_fields": ["supplier", "price"],
            "excluded_fields": [],
            "filter_parameters": {},
            "model_preferences": {"preferred_model": "auto", "allow_llm_to_tune": True, "forced_analysis_function": "auto"},
            "response_format": "human_and_json",
        }
        session["analysis_assistant_chat"] = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]

    response = client.post("/assistant/clear", data={"step": "4"}, follow_redirects=False)

    assert response.status_code == 302
    assert "screen=plan" in response.location
    with client.session_transaction() as session:
        assert session["analysis_assistant_chat"] == []
        assert session["analysis_wizard_state"]["target_fields"] == ["price"]


def test_plan_screen_shows_manual_plan_editor(app):
    client = app.test_client()
    with client.session_transaction() as session:
        session["analysis_wizard_state"] = {
            "data_source": {"type": "uploaded_file", "file_id": "pricing.csv", "sheet_name": None, "header_row": 1},
            "task": "regression",
            "parameter_fields": ["quantity"],
            "input_parameters": {"quantity": 10},
            "target_fields": ["price"],
            "output_fields": ["price"],
            "excluded_fields": [],
            "filter_parameters": {},
            "model_preferences": {"preferred_model": "auto", "allow_llm_to_tune": True, "forced_analysis_function": "auto"},
            "manual_plan": {
                "selected_function": "linear_regression",
                "reason": "Manual override",
                "target_field": "price",
                "feature_fields": ["quantity"],
                "model_settings": {"fit_intercept": True},
                "preprocessing": {"scale_numeric": True},
                "validation": {"use_train_test_split": True},
            },
            "response_format": "human_and_json",
        }
        session["analysis_plan_preview"] = session["analysis_wizard_state"]["manual_plan"]

    response = client.get("/?screen=plan&step=5&file_id=pricing.csv")
    html = response.get_data(as_text=True)

    assert "Editable Model Plan" in html
    assert 'name="plan_selected_function"' in html
    assert 'name="plan_model_settings"' in html
    assert "AI Chat" in html
