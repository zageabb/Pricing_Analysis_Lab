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
    normalized_state = _normalize_wizard_state(state)
    if normalized_state != state:
        session[WIZARD_SESSION_KEY] = normalized_state
        session.modified = True
        state = normalized_state
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
    parameter_fields, input_parameters = _parse_parameter_rows(form)
    state["parameter_fields"] = _prefer_richest_list(
        parameter_fields,
        _parse_string_list(form.get("parameter_fields", "")),
        state.get("parameter_fields", []),
    )
    state["target_fields"] = _prefer_richest_list(
        _parse_field_rows(form, "target_field_name"),
        _parse_string_list(form.get("target_fields", "")),
        state.get("target_fields", []),
    )
    state["output_fields"] = _prefer_richest_list(
        _parse_field_rows(form, "output_field_name"),
        _parse_string_list(form.get("output_fields", "")),
        state.get("output_fields", []),
    )
    state["excluded_fields"] = _prefer_richest_list(
        _parse_field_rows(form, "excluded_field_name"),
        _parse_string_list(form.get("excluded_fields", "")),
        state.get("excluded_fields", []),
    )
    state["input_parameters"] = _merge_input_parameters(
        input_parameters,
        _parse_json_object(form.get("input_parameters", "{}")),
        state.get("input_parameters", {}),
    )
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


def _parse_string_list(value: str) -> list[str]:
    text = value.strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return _split_csv_text(text)
    if not isinstance(parsed, list):
        return _split_csv_text(text)
    normalized: list[str] = []
    for item in parsed:
        item_text = _normalize_field_name(item)
        if item_text:
            normalized.append(item_text)
    return normalized


def _parse_json_object(value: str) -> dict[str, Any]:
    text = value.strip()
    return json.loads(text) if text else {}


def _parse_field_rows(form, field_name: str) -> list[str]:
    if not hasattr(form, "getlist"):
        return []
    values = [_normalize_field_name(item) for item in form.getlist(field_name) if item and str(item).strip()]
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _parse_parameter_rows(form) -> tuple[list[str], dict[str, Any]]:
    if not hasattr(form, "getlist"):
        return [], {}
    names = form.getlist("parameter_field_name")
    values = form.getlist("parameter_field_value")
    parameter_fields: list[str] = []
    input_parameters: dict[str, Any] = {}
    for name, value in zip(names, values):
        clean_name = _normalize_field_name(name)
        clean_value = value.strip()
        if not clean_name:
            continue
        if clean_name not in parameter_fields:
            parameter_fields.append(clean_name)
        if clean_value:
            input_parameters[clean_name] = _coerce_scalar(clean_value)
    return parameter_fields, input_parameters


def _coerce_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if value.lstrip("+-").isdigit():
        return int(value)
    if value.count(".") == 1:
        left, right = value.split(".", 1)
        if left.lstrip("+-").isdigit() and right.isdigit():
            return float(value)
    return value


def _prefer_longer_list(primary: list[str], fallback: list[str]) -> list[str]:
    return primary if len(primary) >= len(fallback) else fallback


def _prefer_richest_list(primary: list[str], fallback: list[str], current: list[str]) -> list[str]:
    return _prefer_longer_list(_prefer_longer_list(primary, fallback), [_normalize_field_name(item) for item in current if _normalize_field_name(item)])


def _merge_input_parameters(primary: dict[str, Any], fallback: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    merged = {_normalize_field_name(key): value for key, value in current.items() if _normalize_field_name(key)}
    merged.update({_normalize_field_name(key): value for key, value in fallback.items() if _normalize_field_name(key)})
    merged.update(primary)
    return merged


def _normalize_field_name(value: Any) -> str:
    return str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


def _normalize_wizard_state(state: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(state)
    normalized["parameter_fields"] = [_normalize_field_name(item) for item in state.get("parameter_fields", []) if _normalize_field_name(item)]
    normalized["target_fields"] = [_normalize_field_name(item) for item in state.get("target_fields", []) if _normalize_field_name(item)]
    normalized["output_fields"] = [_normalize_field_name(item) for item in state.get("output_fields", []) if _normalize_field_name(item)]
    normalized["excluded_fields"] = [_normalize_field_name(item) for item in state.get("excluded_fields", []) if _normalize_field_name(item)]
    normalized["input_parameters"] = {
        _normalize_field_name(key): value
        for key, value in state.get("input_parameters", {}).items()
        if _normalize_field_name(key)
    }
    return normalized
