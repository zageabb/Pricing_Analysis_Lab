from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

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


@dataclass(slots=True)
class LLMSettings:
    provider: str
    base_url: str
    api_key_env: str
    model_name: str
    temperature: float
    top_p: float
    max_tokens: int
    timeout: int
    retry_count: int
    streaming: bool
    json_mode: bool


def ensure_default_settings() -> None:
    for key, value in DEFAULT_SETTINGS.items():
        setting = AppSetting.query.filter_by(key=key).one_or_none()
        if setting is None:
            db.session.add(AppSetting(key=key, value=json.dumps(value)))
    db.session.commit()


def list_settings() -> list[AppSetting]:
    return AppSetting.query.order_by(AppSetting.key.asc()).all()


def get_setting(key: str, default: Any | None = None) -> Any:
    setting = AppSetting.query.filter_by(key=key).one_or_none()
    if setting is None:
        return default
    return json.loads(setting.value)


def set_setting(key: str, value: Any) -> AppSetting:
    setting = AppSetting.query.filter_by(key=key).one_or_none()
    serialized = json.dumps(value)
    if setting is None:
        setting = AppSetting(key=key, value=serialized)
    else:
        setting.value = serialized
    db.session.add(setting)
    db.session.commit()
    return setting


def get_llm_settings() -> LLMSettings:
    return LLMSettings(
        provider=get_setting("llm.provider", DEFAULT_SETTINGS["llm.provider"]),
        base_url=get_setting("llm.base_url", DEFAULT_SETTINGS["llm.base_url"]),
        api_key_env=get_setting("llm.api_key_env", DEFAULT_SETTINGS["llm.api_key_env"]),
        model_name=get_setting("llm.model_name", DEFAULT_SETTINGS["llm.model_name"]),
        temperature=float(get_setting("llm.temperature", DEFAULT_SETTINGS["llm.temperature"])),
        top_p=float(get_setting("llm.top_p", DEFAULT_SETTINGS["llm.top_p"])),
        max_tokens=int(get_setting("llm.max_tokens", DEFAULT_SETTINGS["llm.max_tokens"])),
        timeout=int(get_setting("llm.timeout", DEFAULT_SETTINGS["llm.timeout"])),
        retry_count=int(get_setting("llm.retry_count", DEFAULT_SETTINGS["llm.retry_count"])),
        streaming=bool(get_setting("llm.streaming", DEFAULT_SETTINGS["llm.streaming"])),
        json_mode=bool(get_setting("llm.json_mode", DEFAULT_SETTINGS["llm.json_mode"])),
    )


def update_llm_settings(payload: dict[str, Any]) -> LLMSettings:
    for key, value in payload.items():
        set_setting(f"llm.{key}", value)
    return get_llm_settings()
