from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from api.app import app


client = TestClient(app)


def create_task(theme: str = "api task") -> dict[str, Any]:
    response = client.post(
        "/api/v1/pipeline/tasks",
        json={"theme": theme},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    return payload["data"]


def test_pipeline_status_endpoint_returns_success() -> None:
    response = client.get("/api/v1/pipeline/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["service"] == "ai-short-drama"
    assert payload["data"]["run"] is None


def test_pipeline_preflight_endpoint_returns_check_summary() -> None:
    response = client.get("/api/v1/pipeline/preflight")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["checks"]["models_config"]["status"] in {"ok", "missing"}
    assert payload["data"]["checks"]["ffmpeg"]["status"] in {"ok", "missing"}
    assert payload["data"]["checks"]["ffprobe"]["status"] in {"ok", "missing"}
    assert isinstance(payload["data"]["placeholder_mode"], bool)


def test_pipeline_task_create_endpoint_allocates_task_workspace() -> None:
    task = create_task()

    assert task["task_id"]
    assert Path(task["task_dir"]).is_dir()
    assert Path(task["task_file_path"]).exists()
    assert Path(task["directories"]["references"]).is_dir()
    assert Path(task["directories"]["clips"]).is_dir()


def test_pipeline_run_endpoint_executes_pipeline() -> None:
    response = client.post(
        "/api/v1/pipeline/run",
        json={
            "theme": "city romance",
            "task_id": create_task("city romance")["task_id"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["task_id"]
    assert Path(payload["data"]["task_dir"]).is_dir()
    assert Path(payload["data"]["final_video_path"]).exists()

    status_response = client.get(
        "/api/v1/pipeline/status",
        params={"task_id": payload["data"]["task_id"]},
    )
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["success"] is True
    assert status_payload["data"]["run"]["task_id"] == payload["data"]["task_id"]
    assert status_payload["data"]["run"]["status"] == "completed"
    assert status_payload["data"]["run"]["current_step"] == "complete"
    assert status_payload["data"]["run"]["progress_percent"] == 100
    assert status_payload["data"]["run"]["started_at"] is not None
    assert status_payload["data"]["run"]["completed_at"] is not None
    assert status_payload["data"]["run"]["failed_at"] is None
    assert status_payload["data"]["run"]["last_error"] is None
    assert Path(status_payload["data"]["run"]["manifest_path"]).exists()
    assert Path(status_payload["data"]["run"]["directories"]["references"]).is_dir()
