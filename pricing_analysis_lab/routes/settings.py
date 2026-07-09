from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..services.prompt_store import list_prompt_templates
from ..services.settings_store import get_llm_settings, list_settings, update_llm_settings


settings_bp = Blueprint("settings", __name__)


@settings_bp.get("/")
def index():
    return render_template(
        "settings/index.html",
        settings=list_settings(),
        prompts=list_prompt_templates(),
        llm_settings=get_llm_settings(),
    )


@settings_bp.post("/")
def save():
    payload = {
        "provider": request.form.get("provider", "ollama"),
        "base_url": request.form.get("base_url", "").strip(),
        "api_key_env": request.form.get("api_key_env", "").strip(),
        "model_name": request.form.get("model_name", "").strip(),
        "temperature": float(request.form.get("temperature", "0.2")),
        "top_p": float(request.form.get("top_p", "0.95")),
        "max_tokens": int(request.form.get("max_tokens", "2000")),
        "timeout": int(request.form.get("timeout", "120")),
        "retry_count": int(request.form.get("retry_count", "2")),
        "streaming": request.form.get("streaming") == "on",
        "json_mode": request.form.get("json_mode") == "on",
    }
    update_llm_settings(payload)
    flash("LLM settings saved.")
    return redirect(url_for("settings.index"))
