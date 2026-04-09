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
    assert payload["data"]["run"] is None


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

    status_response = client.get(
        "/api/v1/pipeline/status",
        params={"output_dir": str(tmp_path / "api_run")},
    )
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["success"] is True
    assert status_payload["data"]["run"]["current_step"] == "complete"
    assert status_payload["data"]["run"]["progress_percent"] == 100
    assert Path(status_payload["data"]["run"]["manifest_path"]).exists()
