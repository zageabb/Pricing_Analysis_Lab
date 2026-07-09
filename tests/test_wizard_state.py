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
