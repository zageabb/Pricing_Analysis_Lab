from __future__ import annotations

import json
from typing import Any

from flask import session


WIZARD_SESSION_KEY = "analysis_wizard_state"
ASSISTANT_CHAT_SESSION_KEY = "analysis_assistant_chat"
RESULT_REQUEST_ID_SESSION_KEY = "analysis_result_request_id"


def default_wizard_state() -> dict[str, Any]:
    return {
        "data_source": {"type": "uploaded_file", "file_id": "", "sheet_name": None, "header_row": 1},
        "task": "auto",
        "parameter_fields": [],
        "input_parameters": {},
        "target_fields": [],
        "output_fields": [],
        "excluded_fields": [],
        "filter_parameters": {},
        "model_preferences": {
            "preferred_model": "auto",
            "allow_llm_to_tune": True,
            "forced_analysis_function": "auto",
        },
        "manual_plan": {},
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
    session.pop(RESULT_REQUEST_ID_SESSION_KEY, None)
    session.pop(ASSISTANT_CHAT_SESSION_KEY, None)
    return state


def update_wizard_state_from_form(form) -> dict[str, Any]:
    state = get_wizard_state()
    state["data_source"]["file_id"] = form.get("file_id", state["data_source"].get("file_id", "")).strip()
    state["data_source"]["sheet_name"] = form.get("sheet_name") or None
    state["data_source"]["header_row"] = _parse_header_row(
        form.get("header_row"),
        state["data_source"].get("header_row", 1),
    )
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
        "forced_analysis_function": form.get("forced_analysis_function", "auto"),
    }
    state["manual_plan"] = _parse_manual_plan(form, state.get("manual_plan", {}))
    save_wizard_state(state)
    return state


def set_plan_preview(plan: dict[str, Any]) -> None:
    session["analysis_plan_preview"] = plan
    session.modified = True


def get_plan_preview() -> dict[str, Any] | None:
    value = session.get("analysis_plan_preview")
    return value if isinstance(value, dict) else None


def set_result_preview(result: dict[str, Any]) -> None:
    request_id = str(result.get("request_id", "")).strip()
    if request_id:
        session[RESULT_REQUEST_ID_SESSION_KEY] = request_id
        session.pop("analysis_result_preview", None)
    else:
        session["analysis_result_preview"] = result
    session.modified = True


def get_result_preview(request_id: str | None = None) -> dict[str, Any] | None:
    requested_id = (request_id or session.get(RESULT_REQUEST_ID_SESSION_KEY) or "").strip()
    if requested_id:
        result = _load_result_preview_from_history(requested_id)
        if result is not None:
            session[RESULT_REQUEST_ID_SESSION_KEY] = requested_id
            session.modified = True
            return result

    value = session.get("analysis_result_preview")
    return value if isinstance(value, dict) else None


def get_assistant_chat() -> list[dict[str, str]]:
    value = session.get(ASSISTANT_CHAT_SESSION_KEY, [])
    if not isinstance(value, list):
        value = []
        session[ASSISTANT_CHAT_SESSION_KEY] = value
    return [item for item in value if isinstance(item, dict)]


def add_assistant_chat_message(role: str, content: str) -> None:
    history = get_assistant_chat()
    history.append({"role": role, "content": content})
    session[ASSISTANT_CHAT_SESSION_KEY] = history[-12:]
    session.modified = True


def clear_assistant_chat() -> None:
    session[ASSISTANT_CHAT_SESSION_KEY] = []
    session.modified = True


def set_manual_plan(plan: dict[str, Any]) -> None:
    state = get_wizard_state()
    state["manual_plan"] = _normalize_manual_plan(plan)
    save_wizard_state(state)


def _load_result_preview_from_history(request_id: str) -> dict[str, Any] | None:
    from ..models import AnalysisRun

    run = AnalysisRun.query.filter_by(request_id=request_id).order_by(AnalysisRun.id.desc()).first()
    if run is None or not run.response_json:
        return None
    try:
        value = json.loads(run.response_json)
    except json.JSONDecodeError:
        return None
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


def _parse_manual_plan(form, current: dict[str, Any]) -> dict[str, Any]:
    current_plan = current if isinstance(current, dict) else {}
    selected_function = _normalize_field_name(form.get("plan_selected_function", ""))
    reason = _normalize_field_name(form.get("plan_reason", ""))
    target_field = _normalize_field_name(form.get("plan_target_field", ""))
    feature_fields = _parse_string_list(form.get("plan_feature_fields", ""))
    model_settings_text = form.get("plan_model_settings", "")
    preprocessing_text = form.get("plan_preprocessing", "")
    validation_text = form.get("plan_validation", "")

    has_editor_fields = any(
        [
            selected_function,
            reason,
            target_field,
            feature_fields,
            model_settings_text.strip(),
            preprocessing_text.strip(),
            validation_text.strip(),
        ]
    )
    if has_editor_fields:
        model_settings = _parse_json_object(model_settings_text) if model_settings_text.strip() else current_plan.get("model_settings", {})
        if not isinstance(model_settings, dict):
            model_settings = {}
        if form.get("plan_notebook_compatible") == "on":
            model_settings["notebook_compatible"] = True
        else:
            model_settings.pop("notebook_compatible", None)
        return _normalize_manual_plan(
            {
                "selected_function": selected_function or current_plan.get("selected_function", "descriptive_statistics"),
                "reason": reason or current_plan.get("reason", ""),
                "target_field": target_field or None,
                "feature_fields": feature_fields or current_plan.get("feature_fields", []),
                "model_settings": model_settings,
                "preprocessing": _parse_json_object(preprocessing_text) if preprocessing_text.strip() else current_plan.get("preprocessing", {}),
                "validation": _parse_json_object(validation_text) if validation_text.strip() else current_plan.get("validation", {}),
            }
        )

    raw_plan = form.get("manual_plan")
    if raw_plan is not None:
        try:
            return _normalize_manual_plan(_parse_json_object(raw_plan))
        except json.JSONDecodeError:
            return _normalize_manual_plan(current_plan)
    return _normalize_manual_plan(current_plan)


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
    normalized["data_source"] = {
        **state.get("data_source", {}),
        "header_row": _parse_header_row(
            state.get("data_source", {}).get("header_row"),
            1,
        ),
    }
    normalized["parameter_fields"] = [_normalize_field_name(item) for item in state.get("parameter_fields", []) if _normalize_field_name(item)]
    normalized["target_fields"] = [_normalize_field_name(item) for item in state.get("target_fields", []) if _normalize_field_name(item)]
    normalized["output_fields"] = [_normalize_field_name(item) for item in state.get("output_fields", []) if _normalize_field_name(item)]
    normalized["excluded_fields"] = [_normalize_field_name(item) for item in state.get("excluded_fields", []) if _normalize_field_name(item)]
    normalized["input_parameters"] = {
        _normalize_field_name(key): value
        for key, value in state.get("input_parameters", {}).items()
        if _normalize_field_name(key)
    }
    preferences = dict(state.get("model_preferences", {}))
    preferences.setdefault("preferred_model", "auto")
    preferences.setdefault("allow_llm_to_tune", True)
    preferences.setdefault("forced_analysis_function", "auto")
    normalized["model_preferences"] = preferences
    normalized["manual_plan"] = _normalize_manual_plan(state.get("manual_plan", {}))
    return normalized


def _parse_header_row(value: Any, fallback: int) -> int:
    if value in (None, ""):
        return max(1, int(fallback))
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return max(1, int(fallback))
    return max(1, parsed)


def _normalize_manual_plan(plan: Any) -> dict[str, Any]:
    if not isinstance(plan, dict):
        return {}
    feature_fields = []
    if isinstance(plan.get("feature_fields"), list):
        feature_fields = [_normalize_field_name(item) for item in plan.get("feature_fields", []) if _normalize_field_name(item)]
    normalized = {
        "selected_function": _normalize_field_name(plan.get("selected_function", "")),
        "reason": _normalize_field_name(plan.get("reason", "")),
        "target_field": _normalize_field_name(plan.get("target_field", "")) or None,
        "feature_fields": feature_fields,
        "model_settings": plan.get("model_settings", {}) if isinstance(plan.get("model_settings"), dict) else {},
        "preprocessing": plan.get("preprocessing", {}) if isinstance(plan.get("preprocessing"), dict) else {},
        "validation": plan.get("validation", {}) if isinstance(plan.get("validation"), dict) else {},
    }
    return normalized if any(
        [
            normalized["selected_function"],
            normalized["reason"],
            normalized["target_field"],
            normalized["feature_fields"],
            normalized["model_settings"],
            normalized["preprocessing"],
            normalized["validation"],
        ]
    ) else {}
