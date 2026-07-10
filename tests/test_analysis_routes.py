import json

from pricing_analysis_lab.routes import analysis as analysis_routes
from pricing_analysis_lab.extensions import db
from pricing_analysis_lab.models import AnalysisRun


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


def test_results_screen_loads_persisted_run_by_request_id(app):
    with app.app_context():
        db.session.add(
            AnalysisRun(
                request_id="run-123",
                status="success",
                analysis_type="linear_regression",
                request_json="{}",
                response_json=json.dumps(
                    {
                        "status": "success",
                        "request_id": "run-123",
                        "analysis_type": "linear_regression",
                        "interpretation": {
                            "summary": "Result loaded from run history.",
                            "reasons": [],
                            "caveats": [],
                            "improvement_suggestions": [],
                        },
                    }
                ),
            )
        )
        db.session.commit()

    client = app.test_client()
    response = client.get("/?screen=results&step=7&request_id=run-123")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Latest Analysis Output" in html
    assert "run-123" in html
    assert "Result loaded from run history." in html


def test_results_screen_separates_scenario_and_evaluation_predictions(app):
    with app.app_context():
        db.session.add(
            AnalysisRun(
                request_id="run-789",
                status="success",
                analysis_type="random_forest_regression",
                request_json="{}",
                response_json=json.dumps(
                    {
                        "status": "success",
                        "request_id": "run-789",
                        "analysis_type": "random_forest_regression",
                        "predictions": [
                            {"prediction_scope": "evaluation", "predicted_value": 101, "actual_value": 100},
                            {"prediction_scope": "scenario", "predicted_value": 118},
                        ],
                        "interpretation": {
                            "summary": "Separated predictions.",
                            "reasons": [],
                            "caveats": [],
                            "improvement_suggestions": [],
                        },
                    }
                ),
            )
        )
        db.session.commit()

    client = app.test_client()
    response = client.get("/?screen=results&step=7&request_id=run-789")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Your Scenario Prediction" in html
    assert "Evaluation Sample" in html
    assert "Matching Rows" not in html


def test_run_route_persists_effective_plan_for_results_screen(app, monkeypatch):
    def fake_analyse_payload(_state):
        return {
            "status": "success",
            "request_id": "run-456",
            "analysis_type": "linear_regression",
            "llm_plan": {
                "selected_function": "linear_regression",
                "reason": "Manual override for baseline comparison.",
                "target_field": "price",
                "feature_fields": ["quantity"],
                "model_settings": {"fit_intercept": True},
                "preprocessing": {"scale_numeric": True},
                "validation": {"use_train_test_split": True},
            },
            "interpretation": {"summary": "Used manual plan.", "reasons": [], "caveats": [], "improvement_suggestions": []},
        }

    monkeypatch.setattr(analysis_routes, "analyse_payload", fake_analyse_payload)

    client = app.test_client()
    response = client.post(
        "/run",
        data={
            "file_id": "pricing.csv",
            "task": "regression",
            "preferred_model": "auto",
            "manual_plan": '{"selected_function": "gradient_boosting_regression", "reason": "Generated plan"}',
            "plan_selected_function": "linear_regression",
            "plan_reason": "Manual override for baseline comparison.",
            "plan_target_field": "price",
            "plan_feature_fields": "quantity",
            "plan_model_settings": '{"fit_intercept": true}',
            "plan_preprocessing": '{"scale_numeric": true}',
            "plan_validation": '{"use_train_test_split": true}',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "request_id=run-456" in response.location
    with client.session_transaction() as session:
        assert session["analysis_plan_preview"]["selected_function"] == "linear_regression"
        assert session["analysis_wizard_state"]["manual_plan"]["selected_function"] == "linear_regression"
