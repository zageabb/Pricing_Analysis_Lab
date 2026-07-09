from pathlib import Path

import pytest

from pricing_analysis_lab import create_app
from pricing_analysis_lab.extensions import db
from pricing_analysis_lab.services.prompt_store import ensure_default_prompts
from pricing_analysis_lab.services.settings_store import ensure_default_settings


@pytest.fixture
def app(tmp_path: Path):
    db_path = tmp_path / "test.db"
    data_dir = tmp_path / "data"
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        DATA_DIR=data_dir,
        UPLOAD_DIR=data_dir / "uploads",
        PROMPT_DIR=data_dir / "prompts",
    )
    app.config["DATA_DIR"].mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_DIR"].mkdir(parents=True, exist_ok=True)
    app.config["PROMPT_DIR"].mkdir(parents=True, exist_ok=True)
    with app.app_context():
        db.drop_all()
        db.create_all()
        ensure_default_settings()
        ensure_default_prompts()
    return app
