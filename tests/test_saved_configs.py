from pathlib import Path

from pricing_analysis_lab import create_app
from pricing_analysis_lab.extensions import db
from pricing_analysis_lab.services.saved_config_service import (
    list_saved_configs,
    load_analysis_config,
    save_analysis_config,
)


def test_save_and_load_analysis_config(tmp_path: Path):
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'saved_configs.db'}",
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        payload = {
            "data_source": {"type": "uploaded_file", "file_id": "pricing.csv", "sheet_name": None},
            "task": "regression",
            "parameter_fields": ["supplier", "quantity"],
            "target_fields": ["price"],
            "output_fields": ["supplier", "price"],
            "excluded_fields": [],
            "input_parameters": {"supplier": "Acme", "quantity": 10},
            "filter_parameters": {},
            "model_preferences": {"preferred_model": "auto", "allow_llm_to_tune": True},
            "response_format": "human_and_json",
        }
        record = save_analysis_config("baseline", payload)
        loaded = load_analysis_config(record.id)

        assert loaded["task"] == "regression"
        assert loaded["target_fields"] == ["price"]
        assert list_saved_configs()[0].name == "baseline"
