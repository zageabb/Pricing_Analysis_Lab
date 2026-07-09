from pathlib import Path

from pricing_analysis_lab import create_app
from pricing_analysis_lab.services.llm_provider import DummyLLMProvider, build_llm_provider
from pricing_analysis_lab.services.prompt_store import get_prompt_text
from pricing_analysis_lab.services.settings_store import get_llm_settings, update_llm_settings


def test_settings_loading_and_update(tmp_path):
    app = _make_app(tmp_path)

    with app.app_context():
        settings = get_llm_settings()
        assert settings.provider

        updated = update_llm_settings(
            {
                "provider": "dummy",
                "base_url": "http://localhost:11434",
                "api_key_env": "TEST_KEY",
                "model_name": "test-model",
                "temperature": 0.1,
                "top_p": 0.9,
                "max_tokens": 400,
                "timeout": 30,
                "retry_count": 1,
                "streaming": True,
                "json_mode": True,
            }
        )
        assert updated.provider == "dummy"
        assert build_llm_provider(updated).__class__ is DummyLLMProvider


def test_prompt_loading(tmp_path):
    app = _make_app(tmp_path)

    with app.app_context():
        body = get_prompt_text("orchestrator_prompt")
        assert "workflow" in body.lower() or "orchestration" in body.lower()


def _make_app(tmp_path: Path):
    db_path = tmp_path / "app.db"
    data_dir = tmp_path / "data"
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        DATA_DIR=data_dir,
        UPLOAD_DIR=data_dir / "uploads",
        PROMPT_DIR=data_dir / "prompts",
    )
    return app
