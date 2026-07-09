from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
PROMPT_DIR = DATA_DIR / "prompts"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "pricing-analysis-lab-dev-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'pricing_analysis_lab.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}

    APP_NAME = "Pricing Analysis Lab"
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5052"))
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

    DATA_DIR = Path(os.environ.get("DATA_DIR", DATA_DIR))
    UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", UPLOAD_DIR))
    PROMPT_DIR = Path(os.environ.get("PROMPT_DIR", PROMPT_DIR))
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_UPLOAD_EXTENSIONS = {".csv", ".xlsx"}
