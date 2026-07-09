from flask import Blueprint, render_template

from ..models import AnalysisRun


history_bp = Blueprint("history", __name__)


@history_bp.get("/")
def index():
    runs = AnalysisRun.query.order_by(AnalysisRun.created_at.desc()).all()
    return render_template("history/index.html", runs=runs)
