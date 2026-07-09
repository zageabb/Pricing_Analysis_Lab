from __future__ import annotations

import json
from typing import Any

from flask import session


WIZARD_SESSION_KEY = "analysis_wizard_state"


def default_wizard_state() -> dict[str, Any]:
    return {
        "data_source": {"type": "uploaded_file", "file_id": "", "sheet_name": None},
        "task": "auto",
        "parameter_fields": [],
        "input_parameters": {},
        "target_fields": [],
        "output_fields": [],
        "excluded_fields": [],
        "filter_parameters": {},
        "model_preferences": {"preferred_model": "auto", "allow_llm_to_tune": True},
        "response_format": "human_and_json",
    }


def get_wizard_state() -> dict[str, Any]:
    state = session.get(WIZARD_SESSION_KEY)
    if not isinstance(state, dict):
        state = default_wizard_state()
        session[WIZARD_SESSION_KEY] = state
    return state


def save_wizard_state(state: dict[str, Any]) -> None:
    session[WIZARD_SESSION_KEY] = state
    session.modified = True


def reset_wizard_state() -> dict[str, Any]:
    state = default_wizard_state()
    save_wizard_state(state)
    session.pop("analysis_plan_preview", None)
    session.pop("analysis_result_preview", None)
    return state


def update_wizard_state_from_form(form) -> dict[str, Any]:
    state = get_wizard_state()
    state["data_source"]["file_id"] = form.get("file_id", state["data_source"].get("file_id", "")).strip()
    state["data_source"]["sheet_name"] = form.get("sheet_name") or None
    state["task"] = form.get("task", state.get("task", "auto"))
    state["parameter_fields"] = _split_csv_text(form.get("parameter_fields", ""))
    state["target_fields"] = _split_csv_text(form.get("target_fields", ""))
    state["output_fields"] = _split_csv_text(form.get("output_fields", ""))
    state["excluded_fields"] = _split_csv_text(form.get("excluded_fields", ""))
    state["input_parameters"] = _parse_json_object(form.get("input_parameters", "{}"))
    state["filter_parameters"] = _parse_json_object(form.get("filter_parameters", "{}"))
    state["model_preferences"] = {
        "preferred_model": form.get("preferred_model", "auto"),
        "allow_llm_to_tune": form.get("allow_llm_to_tune") == "on",
    }
    save_wizard_state(state)
    return state


def set_plan_preview(plan: dict[str, Any]) -> None:
    session["analysis_plan_preview"] = plan
    session.modified = True


def get_plan_preview() -> dict[str, Any] | None:
    value = session.get("analysis_plan_preview")
    return value if isinstance(value, dict) else None


def set_result_preview(result: dict[str, Any]) -> None:
    session["analysis_result_preview"] = result
    session.modified = True


def get_result_preview() -> dict[str, Any] | None:
    value = session.get("analysis_result_preview")
    return value if isinstance(value, dict) else None


def _split_csv_text(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_json_object(value: str) -> dict[str, Any]:
    text = value.strip()
    return json.loads(text) if text else {}
