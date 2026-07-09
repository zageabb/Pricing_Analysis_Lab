from flask import Blueprint, render_template


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
    return render_template("analysis/home.html", steps=steps)
