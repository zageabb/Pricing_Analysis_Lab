from __future__ import annotations

import json
from typing import Any

from ..extensions import db
from ..models import SavedAnalysisConfig


def list_saved_configs() -> list[SavedAnalysisConfig]:
    return SavedAnalysisConfig.query.order_by(SavedAnalysisConfig.updated_at.desc()).all()


def save_analysis_config(name: str, payload: dict[str, Any]) -> SavedAnalysisConfig:
    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("Configuration name is required.")
    record = SavedAnalysisConfig.query.filter_by(name=normalized_name).one_or_none()
    serialized = json.dumps(payload)
    if record is None:
        record = SavedAnalysisConfig(name=normalized_name, config_json=serialized)
    else:
        record.config_json = serialized
    db.session.add(record)
    db.session.commit()
    return record


def load_analysis_config(config_id: int) -> dict[str, Any]:
    record = db.session.get(SavedAnalysisConfig, config_id)
    if record is None:
        raise ValueError(f"Saved analysis config {config_id} was not found.")
    return json.loads(record.config_json)
