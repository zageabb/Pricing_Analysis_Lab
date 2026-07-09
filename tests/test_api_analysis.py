from pathlib import Path

from pricing_analysis_lab import create_app
from pricing_analysis_lab.extensions import db
from pricing_analysis_lab.services.prompt_store import ensure_default_prompts
from pricing_analysis_lab.services.settings_store import ensure_default_settings


def test_api_analyse_success(tmp_path: Path):
    app = _make_app(tmp_path)
    csv_path = app.config["UPLOAD_DIR"] / "pricing.csv"
    csv_path.write_text(
        "supplier,category,region,quantity,price\n"
        "Acme,Transformer,UK,10,100\n"
        "Acme,Transformer,UK,20,180\n"
        "Bravo,Transformer,DE,10,110\n"
        "Bravo,Cable,DE,30,210\n"
        "Cora,Cable,UK,15,140\n"
        "Cora,Switch,UK,40,260\n"
        "Delta,Switch,DE,25,190\n"
        "Delta,Transformer,FR,35,250\n"
        "Echo,Cable,FR,50,320\n"
        "Echo,Switch,UK,45,300\n",
        encoding="utf-8",
    )

    client = app.test_client()
    response = client.post(
        "/api/analyse",
        json={
            "data_source": {"type": "uploaded_file", "file_id": "pricing.csv"},
            "task": "auto",
            "parameter_fields": ["supplier", "category", "region", "quantity"],
            "input_parameters": {"supplier": "Acme", "category": "Transformer", "region": "UK", "quantity": 12},
            "target_fields": ["price"],
            "output_fields": ["supplier", "price"],
        },
    )
    body = response.get_json()
    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["analysis_type"] == "random_forest_regression"
    assert "dataset_profile" in body
    assert "llm_plan" in body


def test_api_analyse_error_for_missing_target(tmp_path: Path):
    app = _make_app(tmp_path)
    csv_path = app.config["UPLOAD_DIR"] / "pricing.csv"
    csv_path.write_text("feature,target\n1,10\n2,12\n3,13\n4,15\n", encoding="utf-8")

    client = app.test_client()
    response = client.post(
        "/api/analyse",
        json={
            "data_source": {"type": "uploaded_file", "file_id": "pricing.csv"},
            "task": "regression",
            "parameter_fields": ["feature"],
            "target_fields": ["missing"],
        },
    )
    body = response.get_json()
    assert response.status_code == 400
    assert body["status"] == "error"
    assert body["errors"]


def _make_app(tmp_path: Path):
    db_path = tmp_path / "api.db"
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
