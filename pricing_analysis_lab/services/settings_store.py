from __future__ import annotations

import json

from ..extensions import db
from ..models import AppSetting


DEFAULT_SETTINGS = {
    "llm.provider": "ollama",
    "llm.base_url": "http://127.0.0.1:11434",
    "llm.api_key_env": "OPENAI_API_KEY",
    "llm.model_name": "llama3.2",
    "llm.temperature": 0.2,
    "llm.top_p": 0.95,
    "llm.max_tokens": 2000,
    "llm.timeout": 120,
    "llm.retry_count": 2,
    "llm.streaming": False,
    "llm.json_mode": True,
}


def ensure_default_settings() -> None:
    for key, value in DEFAULT_SETTINGS.items():
        setting = AppSetting.query.filter_by(key=key).one_or_none()
        if setting is None:
            db.session.add(AppSetting(key=key, value=json.dumps(value)))
    db.session.commit()


def list_settings() -> list[AppSetting]:
    return AppSetting.query.order_by(AppSetting.key.asc()).all()
