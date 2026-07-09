from flask import Blueprint, render_template

from ..services.prompt_store import list_prompt_templates
from ..services.settings_store import list_settings


settings_bp = Blueprint("settings", __name__)


@settings_bp.get("/")
def index():
    return render_template(
        "settings/index.html",
        settings=list_settings(),
        prompts=list_prompt_templates(),
    )
