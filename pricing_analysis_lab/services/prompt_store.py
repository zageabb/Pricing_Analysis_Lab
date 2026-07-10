from __future__ import annotations

from pathlib import Path

from flask import current_app

from ..extensions import db
from ..models import PromptTemplate


DEFAULT_PROMPTS = {
    "system_prompt": (
        "You are the orchestration layer for pricing data analysis. Help a business user move from spreadsheet data "
        "to a sensible analysis plan, conservative settings, and an understandable result."
    ),
    "safety_guardrail_prompt": (
        "Only use registered deterministic analysis functions. If the request is underspecified, prefer a cautious "
        "recommendation and explain what additional fields or settings would improve confidence."
    ),
    "data_profiler_prompt": (
        "Profile the spreadsheet, identify likely numeric, categorical, and text columns, and highlight fields that "
        "look useful as parameters, targets, outputs, filters, or identifiers."
    ),
    "orchestrator_prompt": (
        "Choose the most suitable workflow for the request. Prefer the simplest reliable approach first, and explain "
        "why it fits the selected fields, row count, and target availability."
    ),
    "model_selector_prompt": (
        "Select the analysis function that best fits the data and user intent. If supervised modeling is weak, say so "
        "clearly and recommend a safer alternative."
    ),
    "feature_engineering_prompt": (
        "Choose suitable features and preprocessing steps. Call out weak feature coverage, missing targets, leakage "
        "risks, and any fields that should be excluded."
    ),
    "parameter_tuning_prompt": (
        "Choose conservative settings, explain tradeoffs in plain English, and suggest when the user should keep auto "
        "mode versus forcing a model or editing the plan manually."
    ),
    "result_interpretation_prompt": (
        "Explain results in business language, then note caveats, reliability limits, and the next improvements that "
        "would most strengthen the analysis."
    ),
    "json_output_prompt": (
        "Return output that matches the application JSON schema exactly, while keeping textual fields concise, specific, "
        "and useful to a spreadsheet-based pricing workflow."
    ),
}


def ensure_default_prompts() -> None:
    prompt_dir: Path = current_app.config["PROMPT_DIR"]
    for name, body in DEFAULT_PROMPTS.items():
        path = prompt_dir / f"{name}.md"
        if not path.exists():
            path.write_text(body + "\n", encoding="utf-8")
        template = PromptTemplate.query.filter_by(name=name).one_or_none()
        if template is None:
            db.session.add(PromptTemplate(name=name, path=str(path)))
    db.session.commit()


def list_prompt_templates() -> list[PromptTemplate]:
    return PromptTemplate.query.order_by(PromptTemplate.name.asc()).all()


def get_prompt_text(name: str) -> str:
    template = PromptTemplate.query.filter_by(name=name).one()
    return Path(template.path).read_text(encoding="utf-8")


def save_prompt_text(name: str, body: str) -> PromptTemplate:
    template = PromptTemplate.query.filter_by(name=name).one()
    Path(template.path).write_text(body.rstrip() + "\n", encoding="utf-8")
    db.session.add(template)
    db.session.commit()
    return template
