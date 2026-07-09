from pricing_analysis_lab import create_app


def test_app_factory_creates_health_endpoint(tmp_path):
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'test.db'}",
        DATA_DIR=tmp_path / "data",
        UPLOAD_DIR=tmp_path / "data" / "uploads",
        PROMPT_DIR=tmp_path / "data" / "prompts",
    )

    client = app.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
