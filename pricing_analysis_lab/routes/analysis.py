import json

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..services.assistant_service import available_analysis_functions, handle_assistant_message
from ..services.analysis_service import analyse_payload
from ..services.dataset_profiler import profile_dataset
from ..services.data_sources import load_request_dataset
from ..services.plan_service import build_plan_preview
from ..services.saved_config_service import list_saved_configs, load_analysis_config, save_analysis_config
from ..services.spreadsheet_loader import SpreadsheetData
from ..services.upload_service import save_uploaded_dataset
from ..services.wizard_state import (
    add_assistant_chat_message,
    clear_assistant_chat,
    get_assistant_chat,
    get_plan_preview,
    get_result_preview,
    get_wizard_state,
    reset_wizard_state,
    save_wizard_state,
    set_manual_plan,
    set_plan_preview,
    set_result_preview,
    update_wizard_state_from_form,
)


analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.get("/")
def home():
    steps = [
        "Select spreadsheet",
        "Choose fields",
        "Enter parameters",
        "Generate model plan",
        "Review plan",
        "Run analysis",
        "Inspect results",
    ]
    current_step = max(1, min(7, request.args.get("step", default=1, type=int)))
    current_screen = request.args.get("screen") or _default_screen_for_step(current_step)
    wizard_state = get_wizard_state()
    active_plan = wizard_state.get("manual_plan") or get_plan_preview()
    file_id = request.args.get("file_id") or wizard_state["data_source"].get("file_id")
    result_preview = get_result_preview(request.args.get("request_id"))
    dataset_profile = _empty_profile()
    dataset = None
    available_columns: list[str] = []
    if file_id:
        try:
            sheet_name = request.args.get("sheet_name") or wizard_state["data_source"].get("sheet_name")
            header_row = request.args.get("header_row", type=int) or wizard_state["data_source"].get("header_row", 1)
            dataset = load_request_dataset(file_id, sheet_name=sheet_name, header_row=header_row)
            dataset_profile = profile_dataset(dataset)
            available_columns = [column["name"] for column in dataset_profile["columns"]]
        except Exception as exc:  # noqa: BLE001
            flash(str(exc))

    return render_template(
        "analysis/home.html",
        steps=steps,
        current_step=current_step,
        current_screen=current_screen,
        screens=_screen_definitions(),
        dataset_profile=dataset_profile,
        dataset=dataset,
        result_preview=result_preview,
        prediction_groups=_group_predictions(result_preview),
        result_json=json.dumps(result_preview, indent=2) if result_preview else request.args.get("result_json"),
        plan_preview=get_plan_preview(),
        active_plan=active_plan,
        saved_configs=list_saved_configs(),
        wizard_state=wizard_state,
        selected_file_id=file_id,
        available_columns=available_columns,
        available_analysis_functions=available_analysis_functions(),
        assistant_chat=get_assistant_chat(),
    )


@analysis_bp.post("/upload")
def upload():
    file_storage = request.files.get("spreadsheet")
    if file_storage is None:
        flash("Please choose a spreadsheet to upload.")
        return redirect(url_for("analysis.home"))
    record = save_uploaded_dataset(file_storage)
    state = get_wizard_state()
    state["data_source"]["file_id"] = record.file_name
    state["data_source"]["header_row"] = 1
    save_wizard_state(state)
    return redirect(url_for("analysis.home", file_id=record.file_name, step=2, screen="configure"))


@analysis_bp.post("/wizard/update")
def update_wizard():
    state = update_wizard_state_from_form(request.form)
    next_step = request.form.get("next_step", type=int) or 2
    return redirect(
        url_for(
            "analysis.home",
            file_id=state["data_source"]["file_id"],
            step=next_step,
            header_row=state["data_source"].get("header_row", 1),
            screen=request.form.get("screen") or "configure",
        )
    )


@analysis_bp.post("/wizard/reset")
def reset_wizard():
    reset_wizard_state()
    flash("Wizard reset.")
    return redirect(url_for("analysis.home", step=1, screen="intake"))


@analysis_bp.post("/wizard/save-config")
def save_config():
    state = update_wizard_state_from_form(request.form)
    config_name = request.form.get("config_name", "")
    save_analysis_config(config_name, state)
    flash(f"Saved analysis config: {config_name}")
    return redirect(
        url_for(
            "analysis.home",
            file_id=state["data_source"]["file_id"],
            step=3,
            header_row=state["data_source"].get("header_row", 1),
            screen="configure",
        )
    )


@analysis_bp.post("/wizard/load-config/<int:config_id>")
def load_config(config_id: int):
    state = load_analysis_config(config_id)
    save_wizard_state(state)
    flash("Loaded saved analysis config.")
    return redirect(
        url_for(
            "analysis.home",
            file_id=state["data_source"]["file_id"],
            step=2,
            header_row=state["data_source"].get("header_row", 1),
            screen="configure",
        )
    )


@analysis_bp.post("/wizard/plan")
def generate_plan():
    state = update_wizard_state_from_form(request.form)
    dataset_profile, plan_preview = build_plan_preview(state)
    set_plan_preview(plan_preview)
    set_manual_plan(plan_preview)
    state = get_wizard_state()
    available_columns = [column["name"] for column in dataset_profile["columns"]]
    result_preview = get_result_preview(request.args.get("request_id"))
    flash("Generated analysis plan.")
    return render_template(
        "analysis/home.html",
        steps=[
            "Select spreadsheet",
            "Choose fields",
            "Enter parameters",
            "Generate model plan",
            "Review plan",
            "Run analysis",
            "Inspect results",
        ],
        current_step=5,
        current_screen="plan",
        screens=_screen_definitions(),
        dataset_profile=dataset_profile,
        dataset=load_request_dataset(
            state["data_source"]["file_id"],
            sheet_name=state["data_source"].get("sheet_name"),
            header_row=state["data_source"].get("header_row", 1),
        ),
        result_preview=result_preview,
        prediction_groups=_group_predictions(result_preview),
        result_json=json.dumps(result_preview, indent=2) if result_preview else None,
        plan_preview=plan_preview,
        active_plan=state.get("manual_plan") or plan_preview,
        saved_configs=list_saved_configs(),
        wizard_state=state,
        selected_file_id=state["data_source"]["file_id"],
        available_columns=available_columns,
        available_analysis_functions=available_analysis_functions(),
        assistant_chat=get_assistant_chat(),
    )


@analysis_bp.post("/run")
def run():
    state = update_wizard_state_from_form(request.form)
    result = analyse_payload(state)
    result_plan = result.get("llm_plan")
    if isinstance(result_plan, dict):
        set_plan_preview(result_plan)
        set_manual_plan(result_plan)
    set_result_preview(result)
    return redirect(
        url_for(
            "analysis.home",
            file_id=state["data_source"]["file_id"],
            step=7,
            header_row=state["data_source"].get("header_row", 1),
            screen="results",
            request_id=result.get("request_id"),
        )
    )


@analysis_bp.post("/assistant")
def assistant():
    state = update_wizard_state_from_form(request.form)
    message = request.form.get("assistant_message", "").strip()
    if not message:
        flash("Enter a question or command for the data assistant.")
        return redirect(
            url_for(
                "analysis.home",
                file_id=state["data_source"]["file_id"],
                step=request.form.get("step", type=int) or 4,
                header_row=state["data_source"].get("header_row", 1),
                screen=request.form.get("return_screen") or request.form.get("screen") or "plan",
                chat=request.form.get("chat") or "open",
            )
        )

    add_assistant_chat_message("user", message)
    updated_state, reply = handle_assistant_message(state, message)
    save_wizard_state(updated_state)
    add_assistant_chat_message("assistant", reply)
    flash("Assistant updated the workspace.")
    return redirect(
        url_for(
            "analysis.home",
            file_id=updated_state["data_source"]["file_id"],
            step=request.form.get("step", type=int) or 4,
            header_row=updated_state["data_source"].get("header_row", 1),
            screen=request.form.get("return_screen") or request.form.get("screen") or "plan",
            chat=request.form.get("chat") or "open",
        )
    )


@analysis_bp.post("/assistant/clear")
def clear_assistant():
    state = get_wizard_state()
    clear_assistant_chat()
    flash("Assistant chat cleared.")
    return redirect(
        url_for(
            "analysis.home",
            file_id=state["data_source"].get("file_id"),
            step=request.form.get("step", type=int) or 4,
            header_row=state["data_source"].get("header_row", 1),
            screen=request.form.get("return_screen") or request.form.get("screen") or "plan",
            chat=request.form.get("chat") or "open",
        )
    )


def _empty_profile() -> dict:
    return profile_dataset(
        SpreadsheetData(
            file_name="No dataset loaded",
            source_path=None,
            sheet_name=None,
            header_row=1,
            sheet_names=[],
            columns=[],
            rows=[],
        )
    )


def _screen_definitions() -> list[dict[str, str]]:
    return [
        {"key": "intake", "label": "Ingest"},
        {"key": "configure", "label": "Configure"},
        {"key": "plan", "label": "Plan"},
        {"key": "data", "label": "Data"},
        {"key": "results", "label": "Results"},
    ]


def _default_screen_for_step(step: int) -> str:
    if step <= 1:
        return "intake"
    if step <= 4:
        return "configure"
    if step == 5:
        return "plan"
    if step == 6:
        return "data"
    return "results"


def _group_predictions(result_preview: dict | None) -> dict[str, list[dict]]:
    if not isinstance(result_preview, dict):
        return {"scenario": [], "evaluation": [], "match": [], "other": []}

    grouped = {"scenario": [], "evaluation": [], "match": [], "other": []}
    for item in result_preview.get("predictions", []):
        if not isinstance(item, dict):
            grouped["other"].append({"value": item})
            continue
        scope = str(item.get("prediction_scope", "")).strip().lower()
        if scope in grouped:
            grouped[scope].append(item)
        else:
            grouped["other"].append(item)
    return grouped
