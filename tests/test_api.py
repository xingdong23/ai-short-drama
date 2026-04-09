from pathlib import Path

from fastapi.testclient import TestClient

from api.app import app


client = TestClient(app)


def test_pipeline_status_endpoint_returns_success() -> None:
    response = client.get("/api/v1/pipeline/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["service"] == "ai-short-drama"


def test_pipeline_run_endpoint_executes_pipeline(tmp_path: Path) -> None:
    response = client.post(
        "/api/v1/pipeline/run",
        json={
            "theme": "city romance",
            "output_dir": str(tmp_path / "api_run"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert Path(payload["data"]["final_video_path"]).exists()
