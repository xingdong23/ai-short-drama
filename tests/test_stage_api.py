from pathlib import Path

from fastapi.testclient import TestClient

from api.app import app


client = TestClient(app)


def sample_script_payload() -> dict[str, object]:
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


def test_script_generate_endpoint_returns_script_and_writes_file(tmp_path: Path) -> None:
    response = client.post(
        "/api/v1/script/generate",
        json={
            "theme": "office revenge",
            "output_dir": str(tmp_path / "script_stage"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["script"]["theme"] == "office revenge"

    script_path = Path(payload["data"]["script_path"])
    assert script_path.exists()
    assert script_path.name == "script.json"


def test_character_reference_endpoint_generates_reference_files(tmp_path: Path) -> None:
    response = client.post(
        "/api/v1/character/reference",
        json={
            "script": sample_script_payload(),
            "output_dir": str(tmp_path / "references_stage"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["reference_paths"]

    for path in payload["data"]["reference_paths"].values():
        assert Path(path).exists()


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


def test_video_generate_endpoint_creates_clip_files(tmp_path: Path) -> None:
    references_dir = tmp_path / "video_refs"
    references_dir.mkdir(parents=True)
    (references_dir / "shot_001.txt").write_text("reference", encoding="utf-8")

    response = client.post(
        "/api/v1/video/generate",
        json={
            "script": sample_script_payload(),
            "output_dir": str(tmp_path / "video_stage"),
            "references_dir": str(references_dir),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert len(payload["data"]["clip_paths"]) == 2

    for path in payload["data"]["clip_paths"].values():
        assert Path(path).exists()


def test_voice_synthesize_endpoint_creates_audio_and_synced_files(tmp_path: Path) -> None:
    clips_dir = tmp_path / "voice_clips"
    clips_dir.mkdir(parents=True)
    (clips_dir / "shot_001.mp4").write_text("clip 1", encoding="utf-8")
    (clips_dir / "shot_002.mp4").write_text("clip 2", encoding="utf-8")

    response = client.post(
        "/api/v1/voice/synthesize",
        json={
            "script": sample_script_payload(),
            "clips_dir": str(clips_dir),
            "output_dir": str(tmp_path / "voice_stage"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert Path(payload["data"]["synced_paths"]["shot_001"]).exists()
    assert Path(payload["data"]["synced_paths"]["shot_002"]).exists()
    assert Path(payload["data"]["audio_paths"]["shot_001"]).exists()
    assert "shot_002" not in payload["data"]["audio_paths"]


def test_compose_final_endpoint_creates_final_video_and_subtitles(tmp_path: Path) -> None:
    synced_dir = tmp_path / "synced"
    synced_dir.mkdir(parents=True)
    (synced_dir / "shot_001.mp4").write_text("synced 1", encoding="utf-8")
    (synced_dir / "shot_002.mp4").write_text("synced 2", encoding="utf-8")

    response = client.post(
        "/api/v1/compose/final",
        json={
            "script": sample_script_payload(),
            "clips_dir": str(synced_dir),
            "output_dir": str(tmp_path / "compose_stage"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert Path(payload["data"]["final_video_path"]).exists()
    assert Path(payload["data"]["subtitle_path"]).exists()
    assert Path(payload["data"]["bgm_path"]).exists()
