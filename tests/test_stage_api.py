from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from api.app import app


client = TestClient(app)


def create_task(theme: str = "stage api") -> dict[str, Any]:
    response = client.post(
        "/api/v1/pipeline/tasks",
        json={"theme": theme},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    return payload["data"]


def sample_script_payload() -> dict[str, Any]:
    return {
        "title": "Episode 1: Test",
        "theme": "stage api",
        "scenes": [
            {
                "id": "shot_001",
                "type": "dialogue",
                "prompt": "A tense cafe conversation",
                "character": "xiaomei",
                "dialogue": "We should keep moving.",
                "duration": 4,
                "camera": "close_up",
            },
            {
                "id": "shot_002",
                "type": "transition",
                "prompt": "Rainy skyline transition",
                "character": None,
                "dialogue": None,
                "duration": 2,
                "camera": "push_in",
            },
        ],
    }


def test_script_generate_endpoint_returns_script_and_writes_file() -> None:
    task = create_task("office revenge")

    response = client.post(
        "/api/v1/script/generate",
        json={
            "theme": "office revenge",
            "task_id": task["task_id"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["script"]["theme"] == "office revenge"
    assert payload["data"]["task_id"] == task["task_id"]

    script_path = Path(payload["data"]["script_path"])
    assert script_path.exists()
    assert script_path.name == "script.json"
    assert task["task_id"] in str(script_path)


def test_character_reference_endpoint_generates_reference_files() -> None:
    task = create_task()

    response = client.post(
        "/api/v1/character/reference",
        json={
            "task_id": task["task_id"],
            "script": sample_script_payload(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["reference_paths"]
    assert payload["data"]["task_id"] == task["task_id"]

    for path in payload["data"]["reference_paths"].values():
        assert Path(path).exists()

    reference_text = Path(payload["data"]["reference_paths"]["shot_001"]).read_text(encoding="utf-8")
    assert "generator=flux-wrapper-placeholder" in reference_text


def test_character_train_endpoint_generates_weights_file(tmp_path: Path) -> None:
    response = client.post(
        "/api/v1/character/train",
        json={
            "character_name": "xiaomei",
            "output_dir": str(tmp_path / "lora_stage"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    weights_path = Path(payload["data"]["weights_path"])
    assert weights_path.exists()
    assert weights_path.name == "xiaomei.safetensors"


def test_video_generate_endpoint_creates_clip_files() -> None:
    task = create_task()

    response = client.post(
        "/api/v1/video/generate",
        json={
            "task_id": task["task_id"],
            "script": sample_script_payload(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert len(payload["data"]["clip_paths"]) == 2
    assert payload["data"]["task_id"] == task["task_id"]

    for path in payload["data"]["clip_paths"].values():
        assert Path(path).exists()

    wan_clip_text = Path(payload["data"]["clip_paths"]["shot_001"]).read_text(encoding="utf-8")
    assert "backend=wan-wrapper-placeholder" in wan_clip_text


def test_voice_synthesize_endpoint_creates_audio_and_synced_files() -> None:
    task = create_task()

    response = client.post(
        "/api/v1/voice/synthesize",
        json={
            "task_id": task["task_id"],
            "script": sample_script_payload(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["task_id"] == task["task_id"]
    assert Path(payload["data"]["synced_paths"]["shot_001"]).exists()
    assert Path(payload["data"]["synced_paths"]["shot_002"]).exists()
    assert Path(payload["data"]["audio_paths"]["shot_001"]).exists()
    assert "shot_002" not in payload["data"]["audio_paths"]
    audio_text = Path(payload["data"]["audio_paths"]["shot_001"]).read_text(encoding="utf-8")
    synced_text = Path(payload["data"]["synced_paths"]["shot_001"]).read_text(encoding="utf-8")
    assert "backend=cosyvoice-wrapper-placeholder" in audio_text
    assert "backend=musetalk-wrapper-placeholder" in synced_text


def test_compose_final_endpoint_creates_final_video_and_subtitles() -> None:
    task = create_task()

    response = client.post(
        "/api/v1/compose/final",
        json={
            "task_id": task["task_id"],
            "script": sample_script_payload(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["task_id"] == task["task_id"]
    assert Path(payload["data"]["final_video_path"]).exists()
    assert Path(payload["data"]["subtitle_path"]).exists()
    assert Path(payload["data"]["bgm_path"]).exists()
