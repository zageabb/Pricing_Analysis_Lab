import json

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..services.analysis_service import analyse_payload
from ..services.dataset_profiler import profile_dataset
from ..services.data_sources import load_request_dataset
from ..services.spreadsheet_loader import SpreadsheetData
from ..services.upload_service import save_uploaded_dataset


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
    file_id = request.args.get("file_id")
    dataset_profile = _empty_profile()
    dataset = None
    if file_id:
        try:
            dataset = load_request_dataset(file_id, sheet_name=request.args.get("sheet_name"))
            dataset_profile = profile_dataset(dataset)
        except Exception as exc:  # noqa: BLE001
            flash(str(exc))

    return render_template(
        "analysis/home.html",
        steps=steps,
        dataset_profile=dataset_profile,
        dataset=dataset,
        result_json=request.args.get("result_json"),
        selected_file_id=file_id,
    )


@analysis_bp.post("/upload")
def upload():
    file_storage = request.files.get("spreadsheet")
    if file_storage is None:
        flash("Please choose a spreadsheet to upload.")
        return redirect(url_for("analysis.home"))
    record = save_uploaded_dataset(file_storage)
    return redirect(url_for("analysis.home", file_id=record.file_name))


@analysis_bp.post("/run")
def run():
    file_id = request.form.get("file_id", "").strip()
    payload = {
        "data_source": {
            "type": "uploaded_file",
            "file_id": file_id,
            "sheet_name": request.form.get("sheet_name") or None,
        },
        "task": request.form.get("task", "auto"),
        "parameter_fields": _split_csv_text(request.form.get("parameter_fields", "")),
        "input_parameters": _parse_json_object(request.form.get("input_parameters", "{}")),
        "target_fields": _split_csv_text(request.form.get("target_fields", "")),
        "output_fields": _split_csv_text(request.form.get("output_fields", "")),
        "excluded_fields": _split_csv_text(request.form.get("excluded_fields", "")),
        "filter_parameters": _parse_json_object(request.form.get("filter_parameters", "{}")),
        "model_preferences": {
            "preferred_model": request.form.get("preferred_model", "auto"),
            "allow_llm_to_tune": request.form.get("allow_llm_to_tune") == "on",
        },
        "response_format": "human_and_json",
    }
    result = analyse_payload(payload)
    return redirect(
        url_for(
            "analysis.home",
            file_id=file_id,
            result_json=json.dumps(result),
        )
    )


def _split_csv_text(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_json_object(value: str) -> dict:
    text = value.strip()
    return json.loads(text) if text else {}


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
