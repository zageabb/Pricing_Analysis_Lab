from flask import Blueprint, render_template

from ..services.dataset_profiler import profile_dataset
from ..services.spreadsheet_loader import SpreadsheetData


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
    empty_profile = profile_dataset(
        SpreadsheetData(
            file_name="No dataset loaded",
            source_path=None,  # type: ignore[arg-type]
            sheet_name=None,
            sheet_names=[],
            columns=[],
            rows=[],
        )
    )
    return render_template("analysis/home.html", steps=steps, dataset_profile=empty_profile)
