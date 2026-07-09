from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import error, request

from .settings_store import LLMSettings, get_llm_settings


@dataclass(slots=True)
class LLMMessage:
    role: str
    content: str


class LLMProvider(Protocol):
    def generate_json(self, messages: list[LLMMessage], schema_hint: dict[str, Any] | None = None) -> dict[str, Any]:
        ...


class DummyLLMProvider:
    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings

    def generate_json(self, messages: list[LLMMessage], schema_hint: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "provider": "dummy",
            "model": self.settings.model_name,
            "messages": [{"role": item.role, "content": item.content} for item in messages],
            "schema_hint": schema_hint or {},
        }


class OllamaCompatibleProvider:
    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings

    def generate_json(self, messages: list[LLMMessage], schema_hint: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {
            "model": self.settings.model_name,
            "stream": False,
            "format": "json" if self.settings.json_mode else "",
            "messages": [{"role": item.role, "content": item.content} for item in messages],
        }
        return _post_json(
            f"{self.settings.base_url.rstrip('/')}/api/chat",
            payload,
            timeout=self.settings.timeout,
        )


class OpenAICompatibleProvider:
    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings

    def generate_json(self, messages: list[LLMMessage], schema_hint: dict[str, Any] | None = None) -> dict[str, Any]:
        api_key = os.environ.get(self.settings.api_key_env, "")
        payload = {
            "model": self.settings.model_name,
            "temperature": self.settings.temperature,
            "top_p": self.settings.top_p,
            "max_tokens": self.settings.max_tokens,
            "response_format": {"type": "json_object"} if self.settings.json_mode else None,
            "messages": [{"role": item.role, "content": item.content} for item in messages],
        }
        payload = {key: value for key, value in payload.items() if value is not None}
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        return _post_json(
            f"{self.settings.base_url.rstrip('/')}/chat/completions",
            payload,
            timeout=self.settings.timeout,
            headers=headers,
        )


def build_llm_provider(settings: LLMSettings | None = None) -> LLMProvider:
    active_settings = settings or get_llm_settings()
    provider = active_settings.provider.lower()
    if provider in {"ollama", "dummy_ollama"}:
        return OllamaCompatibleProvider(active_settings)
    if provider in {"openai", "azure_openai", "openai_compatible"}:
        return OpenAICompatibleProvider(active_settings)
    return DummyLLMProvider(active_settings)


def _post_json(url: str, payload: dict[str, Any], timeout: int, headers: dict[str, str] | None = None) -> dict[str, Any]:
    encoded = json.dumps(payload).encode("utf-8")
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    req = request.Request(url, data=encoded, headers=request_headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.URLError as exc:
        raise RuntimeError(f"LLM provider request failed: {exc}") from exc
