from __future__ import annotations

from flask import Flask

from .config import Config
from .extensions import db
from .routes.admin import admin_bp
from .routes.analysis import analysis_bp
from .routes.api import api_bp
from .routes.history import history_bp
from .routes.settings import settings_bp
from .services.prompt_store import ensure_default_prompts
from .services.settings_store import ensure_default_settings


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    app.config["DATA_DIR"].mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_DIR"].mkdir(parents=True, exist_ok=True)
    app.config["PROMPT_DIR"].mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    with app.app_context():
        from . import models  # noqa: F401

        db.create_all()
        ensure_default_settings()
        ensure_default_prompts()

    app.register_blueprint(analysis_bp)
    app.register_blueprint(settings_bp, url_prefix="/settings")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(history_bp, url_prefix="/history")
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
