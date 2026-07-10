from __future__ import annotations

import json
import re
from typing import Any

from ..services.analysis_service import analyse_payload
from ..services.data_sources import load_request_dataset
from ..services.dataset_profiler import profile_dataset
from ..services.llm_provider import LLMMessage, build_llm_provider
from ..services.manual_plan_service import resolve_effective_plan
from ..services.orchestrator import create_analysis_plan
from ..services.request_validator import validate_analysis_request


ANALYSIS_FUNCTION_LABELS = {
    "auto": "Auto-select",
    "descriptive_statistics": "Descriptive statistics",
    "filtered_search": "Filtered search",
    "nearest_neighbor_similarity": "Nearest-neighbor similarity",
    "linear_regression": "Linear regression",
    "random_forest_regression": "Random forest regression",
    "gradient_boosting_regression": "Gradient boosting regression",
    "random_forest_classification": "Random forest classification",
    "gradient_boosting_classification": "Gradient boosting classification",
}


def available_analysis_functions() -> list[tuple[str, str]]:
    return [(key, label) for key, label in ANALYSIS_FUNCTION_LABELS.items()]


def handle_assistant_message(state: dict[str, Any], message: str) -> tuple[dict[str, Any], str]:
    text = message.strip()
    if not text:
        return state, (
            "Ask a dataset question or give an instruction such as "
            "'which field should be the target?', "
            "'add output field Project Name', or "
            "'what settings do you recommend?'."
        )

    command_reply = _apply_local_command(state, text)
    if command_reply:
        return state, command_reply

    file_id = state["data_source"].get("file_id")
    if not file_id:
        return state, "Upload a spreadsheet first so I can answer questions against the data."

    dataset = load_request_dataset(
        file_id,
        sheet_name=state["data_source"].get("sheet_name"),
        header_row=state["data_source"].get("header_row", 1),
    )
    profile = profile_dataset(dataset)

    if _is_settings_advice_request(text):
        return state, _build_settings_advice(state, profile)

    try:
        provider = build_llm_provider()
        response = provider.generate_json(
            [
                LLMMessage(
                    role="system",
                    content=(
                        "You are a pricing analysis copilot for a business user working with spreadsheet-based pricing data. "
                        "Be practical, specific, and concise. Prefer direct recommendations over vague advice. "
                        "If the user asks about setup, explain which fields, model choice, or settings you recommend and why. "
                        "Answer briefly in JSON with keys "
                        "'reply', optional 'suggestions', and optional 'settings_advice'. "
                        "If the user asks about configuration, include concrete settings advice."
                    ),
                ),
                LLMMessage(
                    role="user",
                    content=json.dumps(
                        {
                            "question": text,
                            "wizard_state": state,
                            "dataset_profile": {
                                "row_count": profile["row_count"],
                                "column_count": profile["column_count"],
                                "columns": profile["columns"],
                                "preview": profile["preview"][:5],
                            },
                        },
                        ensure_ascii=True,
                    ),
                ),
            ],
            schema_hint={"reply": "string", "suggestions": ["string"], "settings_advice": ["string"]},
        )
        reply = _extract_reply(response)
        if reply:
            return state, reply
    except Exception:
        pass

    return state, _fallback_data_answer(text, state, profile)


def _apply_local_command(state: dict[str, Any], message: str) -> str | None:
    normalized = " ".join(message.lower().split())

    if match := re.match(r"set header row to (\d+)", normalized):
        header_row = max(1, int(match.group(1)))
        state["data_source"]["header_row"] = header_row
        return f"Header row set to {header_row}."

    if normalized.startswith("set task to "):
        task = message.split("to", 1)[1].strip()
        state["task"] = task
        return f"Task set to '{task}'."

    if normalized.startswith("force analysis type to "):
        requested = _normalize_analysis_key(message.split("to", 1)[1].strip())
        if requested in ANALYSIS_FUNCTION_LABELS:
            state["model_preferences"]["forced_analysis_function"] = requested
            return f"Forced analysis function set to '{requested}'."
        return f"Unknown analysis function '{message.split('to', 1)[1].strip()}'."

    if normalized in {"clear forced analysis", "reset forced analysis", "force analysis type to auto"}:
        state["model_preferences"]["forced_analysis_function"] = "auto"
        return "Forced analysis function cleared."

    field_command = re.match(
        r"(add|remove)\s+(parameter|target|output|excluded)\s+field\s+(.+)",
        normalized,
    )
    if field_command:
        action, field_group, _ = field_command.groups()
        raw_field = message.split("field", 1)[1].strip()
        return _mutate_field_group(state, action, field_group, raw_field)

    parameter_match = re.match(r"set parameter value for\s+(.+?)\s+to\s+(.+)", message, re.IGNORECASE)
    if parameter_match:
        field_name = parameter_match.group(1).strip()
        field_value = parameter_match.group(2).strip()
        if field_name not in state["parameter_fields"]:
            state["parameter_fields"].append(field_name)
        state["input_parameters"][field_name] = field_value
        return f"Parameter '{field_name}' set to '{field_value}'."

    if normalized in {"what fields are selected", "show selected fields"}:
        return (
            f"Parameters: {', '.join(state['parameter_fields']) or 'none'} | "
            f"Targets: {', '.join(state['target_fields']) or 'none'} | "
            f"Outputs: {', '.join(state['output_fields']) or 'none'}."
        )

    if normalized in {"clear manual plan", "reset manual plan", "use generated plan"}:
        state["manual_plan"] = {}
        return "Manual plan edits cleared. The next generated plan will become the active plan."

    return None


def _mutate_field_group(state: dict[str, Any], action: str, field_group: str, field_name: str) -> str:
    mapping = {
        "parameter": "parameter_fields",
        "target": "target_fields",
        "output": "output_fields",
        "excluded": "excluded_fields",
    }
    key = mapping[field_group]
    values = state[key]
    if action == "add":
        if field_name not in values:
            values.append(field_name)
        return f"Added '{field_name}' to {field_group} fields."
    if field_name in values:
        values.remove(field_name)
        if key == "parameter_fields":
            state["input_parameters"].pop(field_name, None)
        return f"Removed '{field_name}' from {field_group} fields."
    return f"'{field_name}' was not in {field_group} fields."


def _normalize_analysis_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _extract_reply(response: dict[str, Any]) -> str:
    if "reply" in response and isinstance(response["reply"], str):
        reply = response["reply"].strip()
        suggestions = response.get("suggestions", [])
        settings_advice = response.get("settings_advice", [])
        if isinstance(suggestions, list) and suggestions:
            reply += "\n\nSuggestions: " + "; ".join(str(item) for item in suggestions[:3])
        if isinstance(settings_advice, list) and settings_advice:
            reply += "\n\nSettings advice: " + "; ".join(str(item) for item in settings_advice[:4])
        return reply
    if "message" in response and isinstance(response["message"], dict):
        content = response["message"].get("content")
        if isinstance(content, str):
            return content.strip()
    if "choices" in response and isinstance(response["choices"], list) and response["choices"]:
        content = response["choices"][0].get("message", {}).get("content")
        if isinstance(content, str):
            return content.strip()
    return ""


def _fallback_data_answer(question: str, state: dict[str, Any], profile: dict[str, Any]) -> str:
    lower = question.lower()
    if "how many rows" in lower or "row count" in lower:
        return f"The active dataset has {profile['row_count']} rows and {profile['column_count']} columns."
    if "what columns" in lower or "which columns" in lower:
        columns = ", ".join(column["name"] for column in profile["columns"][:12])
        return f"Detected columns include: {columns}."
    if "what is selected" in lower or "current setup" in lower:
        return (
            f"Task: {state['task']}. Parameters: {', '.join(state['parameter_fields']) or 'none'}. "
            f"Targets: {', '.join(state['target_fields']) or 'none'}. "
            f"Outputs: {', '.join(state['output_fields']) or 'none'}."
        )
    return (
        "I can answer dataset questions, recommend fields and settings, and apply commands. "
        "Try 'which field should be the target?', 'add output field Project Name', "
        "'set header row to 3', 'force analysis type to linear_regression', or "
        "'what settings do you recommend for this dataset?'."
    )


def _is_settings_advice_request(message: str) -> bool:
    normalized = message.lower()
    cues = (
        "settings",
        "recommend",
        "advice",
        "tune",
        "configuration",
        "config",
        "model plan",
    )
    return any(cue in normalized for cue in cues)


def _build_settings_advice(state: dict[str, Any], profile: dict[str, Any]) -> str:
    request_model = validate_analysis_request(state)
    base_plan = create_analysis_plan(request_model, profile)
    plan = resolve_effective_plan(base_plan.model_dump(), state.get("manual_plan"))
    advice: list[str] = []
    advice.append(f"Current best fit is '{plan.selected_function}' because {plan.reason.lower()}")
    if not state.get("target_fields"):
        advice.append("Add at least one target field if you want supervised prediction instead of descriptive or similarity analysis")
    if profile.get("row_count", 0) < 25:
        advice.append("Keep the model simple because the row count is small; linear or filtered approaches will be more stable")
    if state["model_preferences"].get("forced_analysis_function", "auto") == "auto":
        advice.append("Only force the analysis type when you want to override the planner; otherwise auto mode will adapt to the dataset")
    if not plan.feature_fields:
        advice.append("Choose more parameter fields so the planner has stronger predictive inputs to work with")
    if plan.selected_function in {"random_forest_regression", "random_forest_classification", "gradient_boosting_regression", "gradient_boosting_classification"}:
        advice.append("Review model settings like test_size, n_estimators, and min_samples_leaf before running a heavier model")
    return "Settings advice:\n- " + "\n- ".join(advice[:5])
