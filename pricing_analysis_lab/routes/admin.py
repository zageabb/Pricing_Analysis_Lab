from flask import Blueprint, render_template

from ..services.prompt_store import list_prompt_templates


admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/prompts")
def prompts():
    return render_template("admin/prompts.html", prompts=list_prompt_templates())
