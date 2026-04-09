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
    assert manifest["current_step"] == "complete"
    assert manifest["progress_percent"] == 100
    assert manifest["final_video_path"] == str(output_dir / "final.mp4")
    assert manifest["artifact_counts"]["clips"] >= 1


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

    assert inspection.current_step == "video"
    assert inspection.completed_steps == ["script", "character"]
    assert inspection.progress_percent == 40
    assert inspection.script_path == output_dir / "script.json"
    assert inspection.final_video_path is None
    assert inspection.artifact_counts["references"] == 1
