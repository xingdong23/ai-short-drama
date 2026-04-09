import json
from pathlib import Path

from src.pipeline.engine import PipelineEngine, PipelineRequest


def test_pipeline_run_creates_expected_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "episode_01"

    engine = PipelineEngine()
    result = engine.run(
        PipelineRequest(
            theme="campus romance",
            output_dir=output_dir,
        )
    )

    assert result.final_video_path == output_dir / "final.mp4"
    assert result.final_video_path.exists()
    assert (output_dir / "script.json").exists()
    assert (output_dir / "references").is_dir()
    assert (output_dir / "clips").is_dir()
    assert (output_dir / "audio").is_dir()
    assert (output_dir / "synced").is_dir()

    state = json.loads((output_dir / "state.json").read_text())
    assert state["completed"] == ["script", "character", "video", "voice", "compose"]
    assert state["current_step"] == "complete"

    manifest = json.loads((output_dir / "manifest.json").read_text())
    assert manifest["status"] == "completed"
    assert manifest["current_step"] == "complete"
    assert manifest["progress_percent"] == 100
    assert manifest["started_at"] is not None
    assert manifest["completed_at"] is not None
    assert manifest["failed_at"] is None
    assert manifest["last_error"] is None
    assert manifest["final_video_path"] == str(output_dir / "final.mp4")
    assert manifest["artifact_counts"]["clips"] >= 1

    reference_text = (output_dir / "references" / "shot_002.txt").read_text(encoding="utf-8")
    clip_text = (output_dir / "clips" / "shot_002.mp4").read_text(encoding="utf-8")
    assert "generator=flux-wrapper-placeholder" in reference_text
    assert "backend=wan-wrapper-placeholder" in clip_text


def test_pipeline_resume_finishes_remaining_steps(tmp_path: Path) -> None:
    output_dir = tmp_path / "resume_case"
    output_dir.mkdir(parents=True)
    (output_dir / "references").mkdir()

    (output_dir / "state.json").write_text(
        json.dumps(
            {
                "current_step": "character",
                "completed": ["script"],
            }
        )
    )
    (output_dir / "script.json").write_text(
        json.dumps(
            {
                "title": "Recovered",
                "theme": "resume flow",
                "scenes": [
                    {
                        "id": "shot_001",
                        "type": "dialogue",
                        "prompt": "A character looks out the window",
                        "character": "xiaomei",
                        "dialogue": "We can continue from here.",
                        "duration": 4,
                        "camera": "close_up",
                    }
                ],
            }
        )
    )

    engine = PipelineEngine()
    result = engine.resume(output_dir)

    assert result.final_video_path == output_dir / "final.mp4"
    assert result.final_video_path.exists()

    state = json.loads((output_dir / "state.json").read_text())
    assert state["completed"] == ["script", "character", "video", "voice", "compose"]
    assert state["current_step"] == "complete"


def test_pipeline_inspect_reports_partial_progress(tmp_path: Path) -> None:
    output_dir = tmp_path / "inspect_case"
    output_dir.mkdir(parents=True)
    (output_dir / "references").mkdir()
    (output_dir / "clips").mkdir()
    (output_dir / "audio").mkdir()
    (output_dir / "synced").mkdir()
    (output_dir / "compose").mkdir()

    (output_dir / "state.json").write_text(
        json.dumps(
            {
                "current_step": "video",
                "completed": ["script", "character"],
            }
        )
    )
    (output_dir / "script.json").write_text(
        json.dumps(
            {
                "title": "Inspection Run",
                "theme": "inspection",
                "scenes": [
                    {
                        "id": "shot_001",
                        "type": "dialogue",
                        "prompt": "A late-night confrontation",
                        "character": "xiaomei",
                        "dialogue": "We are not done yet.",
                        "duration": 4,
                        "camera": "close_up",
                    }
                ],
            }
        )
    )
    (output_dir / "references" / "shot_001.txt").write_text("reference", encoding="utf-8")

    inspection = PipelineEngine().inspect(output_dir)

    assert inspection.status in {"pending", "running"}
    assert inspection.current_step == "video"
    assert inspection.completed_steps == ["script", "character"]
    assert inspection.progress_percent == 40
    assert inspection.script_path == output_dir / "script.json"
    assert inspection.final_video_path is None
    assert inspection.artifact_counts["references"] == 1


def test_pipeline_records_failed_run_state(tmp_path: Path, monkeypatch) -> None:
    output_dir = tmp_path / "failed_case"
    engine = PipelineEngine()

    def raise_reference_failure(*args, **kwargs):
        raise RuntimeError("reference generation exploded")

    monkeypatch.setattr(
        engine.reference_generator,
        "generate_references",
        raise_reference_failure,
    )

    try:
        engine.run(PipelineRequest(theme="failure case", output_dir=output_dir))
    except RuntimeError as exc:
        assert str(exc) == "reference generation exploded"
    else:
        raise AssertionError("Pipeline run should have failed")

    state = json.loads((output_dir / "state.json").read_text())
    assert state["status"] == "failed"
    assert state["current_step"] == "character"
    assert state["completed"] == ["script"]
    assert state["started_at"] is not None
    assert state["failed_at"] is not None
    assert state["last_error"] == "reference generation exploded"

    manifest = json.loads((output_dir / "manifest.json").read_text())
    assert manifest["status"] == "failed"
    assert manifest["current_step"] == "character"
    assert manifest["progress_percent"] == 20
    assert manifest["last_error"] == "reference generation exploded"
    assert manifest["final_video_path"] is None
