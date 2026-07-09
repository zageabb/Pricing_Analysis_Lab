import json

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..services.analysis_service import analyse_payload
from ..services.dataset_profiler import profile_dataset
from ..services.data_sources import load_request_dataset
from ..services.plan_service import build_plan_preview
from ..services.saved_config_service import list_saved_configs, load_analysis_config, save_analysis_config
from ..services.spreadsheet_loader import SpreadsheetData
from ..services.upload_service import save_uploaded_dataset
from ..services.wizard_state import (
    get_plan_preview,
    get_result_preview,
    get_wizard_state,
    reset_wizard_state,
    save_wizard_state,
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
    wizard_state = get_wizard_state()
    file_id = request.args.get("file_id") or wizard_state["data_source"].get("file_id")
    dataset_profile = _empty_profile()
    dataset = None
    available_columns: list[str] = []
    if file_id:
        try:
            sheet_name = request.args.get("sheet_name") or wizard_state["data_source"].get("sheet_name")
            dataset = load_request_dataset(file_id, sheet_name=sheet_name)
            dataset_profile = profile_dataset(dataset)
            available_columns = [column["name"] for column in dataset_profile["columns"]]
        except Exception as exc:  # noqa: BLE001
            flash(str(exc))

    return render_template(
        "analysis/home.html",
        steps=steps,
        current_step=current_step,
        dataset_profile=dataset_profile,
        dataset=dataset,
        result_json=json.dumps(get_result_preview(), indent=2) if get_result_preview() else request.args.get("result_json"),
        plan_preview=get_plan_preview(),
        saved_configs=list_saved_configs(),
        wizard_state=wizard_state,
        selected_file_id=file_id,
        available_columns=available_columns,
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
    save_wizard_state(state)
    return redirect(url_for("analysis.home", file_id=record.file_name, step=2))


@analysis_bp.post("/wizard/update")
def update_wizard():
    state = update_wizard_state_from_form(request.form)
    next_step = request.form.get("next_step", type=int) or 2
    return redirect(url_for("analysis.home", file_id=state["data_source"]["file_id"], step=next_step))


@analysis_bp.post("/wizard/reset")
def reset_wizard():
    reset_wizard_state()
    flash("Wizard reset.")
    return redirect(url_for("analysis.home", step=1))


@analysis_bp.post("/wizard/save-config")
def save_config():
    state = update_wizard_state_from_form(request.form)
    config_name = request.form.get("config_name", "")
    save_analysis_config(config_name, state)
    flash(f"Saved analysis config: {config_name}")
    return redirect(url_for("analysis.home", file_id=state["data_source"]["file_id"], step=3))


@analysis_bp.post("/wizard/load-config/<int:config_id>")
def load_config(config_id: int):
    state = load_analysis_config(config_id)
    save_wizard_state(state)
    flash("Loaded saved analysis config.")
    return redirect(url_for("analysis.home", file_id=state["data_source"]["file_id"], step=2))


@analysis_bp.post("/wizard/plan")
def generate_plan():
    state = update_wizard_state_from_form(request.form)
    dataset_profile, plan_preview = build_plan_preview(state)
    set_plan_preview(plan_preview)
    available_columns = [column["name"] for column in dataset_profile["columns"]]
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
        dataset_profile=dataset_profile,
        dataset=load_request_dataset(state["data_source"]["file_id"], sheet_name=state["data_source"].get("sheet_name")),
        result_json=json.dumps(get_result_preview(), indent=2) if get_result_preview() else None,
        plan_preview=plan_preview,
        saved_configs=list_saved_configs(),
        wizard_state=state,
        selected_file_id=state["data_source"]["file_id"],
        available_columns=available_columns,
    )


@analysis_bp.post("/run")
def run():
    state = update_wizard_state_from_form(request.form)
    result = analyse_payload(state)
    set_result_preview(result)
    return redirect(
        url_for(
            "analysis.home",
            file_id=state["data_source"]["file_id"],
            step=7,
        )
    )


def _empty_profile() -> dict:
    return profile_dataset(
        SpreadsheetData(
            file_name="No dataset loaded",
            source_path=None,
            sheet_name=None,
            sheet_names=[],
            columns=[],
            rows=[],
        )
    )
