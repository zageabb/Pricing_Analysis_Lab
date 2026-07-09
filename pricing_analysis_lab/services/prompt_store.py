from __future__ import annotations

from pathlib import Path

from flask import current_app

from ..extensions import db
from ..models import PromptTemplate


DEFAULT_PROMPTS = {
    "system_prompt": "You are the orchestration layer for pricing data analysis.",
    "safety_guardrail_prompt": "Only use registered deterministic analysis functions.",
    "data_profiler_prompt": "Profile the spreadsheet and summarize its structure.",
    "orchestrator_prompt": "Choose the most suitable workflow for the request.",
    "model_selector_prompt": "Select the analysis function that best fits the data.",
    "feature_engineering_prompt": "Choose suitable features and preprocessing steps.",
    "parameter_tuning_prompt": "Choose conservative settings and explain tradeoffs.",
    "result_interpretation_prompt": "Explain results, caveats, and improvement ideas.",
    "json_output_prompt": "Return output that matches the application JSON schema.",
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
