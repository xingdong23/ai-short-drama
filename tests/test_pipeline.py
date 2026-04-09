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
