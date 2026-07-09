from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..services.prompt_store import get_prompt_text, list_prompt_templates, save_prompt_text


admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/prompts")
def prompts():
    prompts = list_prompt_templates()
    prompt_bodies = {prompt.name: get_prompt_text(prompt.name) for prompt in prompts}
    return render_template("admin/prompts.html", prompts=prompts, prompt_bodies=prompt_bodies)


@admin_bp.post("/prompts/<prompt_name>")
def save_prompt(prompt_name: str):
    save_prompt_text(prompt_name, request.form.get("body", ""))
    flash(f"Saved prompt: {prompt_name}")
    return redirect(url_for("admin.prompts"))
