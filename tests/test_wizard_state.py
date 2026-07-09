from werkzeug.datastructures import MultiDict

from pricing_analysis_lab.services.wizard_state import _parse_parameter_rows, update_wizard_state_from_form


def test_parse_parameter_rows_from_form():
    form = MultiDict(
        [
            ("parameter_field_name", "supplier"),
            ("parameter_field_value", "Acme"),
            ("parameter_field_name", "quantity"),
            ("parameter_field_value", "12"),
            ("parameter_field_name", ""),
            ("parameter_field_value", ""),
        ]
    )
    fields, params = _parse_parameter_rows(form)
    assert fields == ["supplier", "quantity"]
    assert params == {"supplier": "Acme", "quantity": 12}


def test_update_wizard_state_from_selector_rows(app):
    with app.test_request_context():
        form = MultiDict(
            [
                ("file_id", "pricing.csv"),
                ("task", "auto"),
                ("parameter_field_name", "supplier"),
                ("parameter_field_value", "Acme"),
                ("output_field_name", "price"),
                ("target_field_name", "price"),
                ("excluded_field_name", "notes"),
                ("preferred_model", "auto"),
            ]
        )
        state = update_wizard_state_from_form(form)
        assert state["parameter_fields"] == ["supplier"]
        assert state["input_parameters"] == {"supplier": "Acme"}
        assert state["output_fields"] == ["price"]
        assert state["target_fields"] == ["price"]
        assert state["excluded_fields"] == ["notes"]


def test_secondary_actions_submit_live_wizard_form(app):
    client = app.test_client()
    with client.session_transaction() as session:
        session["analysis_wizard_state"] = {
            "data_source": {"type": "uploaded_file", "file_id": "missing.csv", "sheet_name": None},
            "task": "auto",
            "parameter_fields": [],
            "input_parameters": {},
            "target_fields": ["price", "margin"],
            "output_fields": ["sku", "price"],
            "excluded_fields": [],
            "filter_parameters": {},
            "model_preferences": {"preferred_model": "auto", "allow_llm_to_tune": True},
            "response_format": "human_and_json",
        }

    response = client.get("/")
    html = response.get_data(as_text=True)

    assert 'id="wizard-form"' in html
    assert 'form="wizard-form"' in html
    assert 'formaction="/wizard/save-config"' in html
    assert 'formaction="/wizard/plan"' in html
    assert 'formaction="/run"' in html


def test_update_wizard_state_prefers_richer_hidden_field_snapshots(app):
    with app.test_request_context():
        form = MultiDict(
            [
                ("file_id", "pricing.csv"),
                ("task", "auto"),
                ("target_field_name", "price"),
                ("target_fields", '["price", "margin"]'),
                ("output_field_name", "sku"),
                ("output_fields", '["sku", "price", "margin"]'),
                ("parameter_field_name", "supplier"),
                ("parameter_field_value", "Acme"),
                ("parameter_fields", '["supplier", "quantity"]'),
                ("input_parameters", '{"supplier": "Acme", "quantity": 12}'),
                ("preferred_model", "auto"),
            ]
        )
        state = update_wizard_state_from_form(form)
        assert state["target_fields"] == ["price", "margin"]
        assert state["output_fields"] == ["sku", "price", "margin"]
        assert state["parameter_fields"] == ["supplier", "quantity"]
        assert state["input_parameters"] == {"supplier": "Acme", "quantity": 12}


def test_update_wizard_state_preserves_field_names_with_commas(app):
    with app.test_request_context():
        form = MultiDict(
            [
                ("file_id", "pricing.csv"),
                ("task", "auto"),
                ("parameter_fields", '["Power, Rated", "Voltage"]'),
                ("target_fields", '["Sales Price, GBP"]'),
                ("output_fields", '["Sales Price, GBP", "Margin, Percent"]'),
                ("input_parameters", '{"Power, Rated": 120000}'),
                ("preferred_model", "auto"),
            ]
        )
        state = update_wizard_state_from_form(form)
        assert state["parameter_fields"] == ["Power, Rated", "Voltage"]
        assert state["target_fields"] == ["Sales Price, GBP"]
        assert state["output_fields"] == ["Sales Price, GBP", "Margin, Percent"]
        assert state["input_parameters"] == {"Power, Rated": 120000}


def test_update_wizard_state_normalizes_windows_newlines_in_field_names(app):
    with app.test_request_context():
        form = MultiDict(
            [
                ("file_id", "pricing.csv"),
                ("task", "auto"),
                ("target_fields", '["Unit Price (Source) \\r\\n(FCA/EXW)"]'),
                ("output_fields", '["Project Name", "Unit Price (Source) \\r\\n(FCA/EXW)"]'),
                ("parameter_fields", '["Minimum Rated Power (Active)", "Primary Voltage"]'),
                ("input_parameters", '{"Minimum Rated Power (Active)": 120000, "Primary Voltage": 220}'),
                ("preferred_model", "auto"),
            ]
        )
        state = update_wizard_state_from_form(form)
        assert state["target_fields"] == ["Unit Price (Source) \n(FCA/EXW)"]
        assert state["output_fields"] == ["Project Name", "Unit Price (Source) \n(FCA/EXW)"]


def test_get_wizard_state_normalizes_existing_session_field_names(app):
    with app.test_request_context():
        from flask import session

        session["analysis_wizard_state"] = {
            "data_source": {"type": "uploaded_file", "file_id": "pricing.csv", "sheet_name": None},
            "task": "auto",
            "parameter_fields": ["Minimum Rated Power (Active)"],
            "input_parameters": {"Primary Voltage\r\nLevel": 220},
            "target_fields": ["Unit Price (Source) \r\n(FCA/EXW)"],
            "output_fields": ["Project Name", "Unit Price (Source) \r\n(FCA/EXW)"],
            "excluded_fields": [],
            "filter_parameters": {},
            "model_preferences": {"preferred_model": "auto", "allow_llm_to_tune": True},
            "response_format": "human_and_json",
        }

        state = update_wizard_state_from_form(MultiDict([("file_id", "pricing.csv"), ("task", "auto"), ("preferred_model", "auto")]))
        assert state["target_fields"] == ["Unit Price (Source) \n(FCA/EXW)"]
        assert state["output_fields"] == ["Project Name", "Unit Price (Source) \n(FCA/EXW)"]
        assert state["input_parameters"] == {"Primary Voltage\nLevel": 220}
