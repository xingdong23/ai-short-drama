import sys
from pathlib import Path

from src.models.base import ModelSpec
from src.scriptwriter.storyboard import Shot
from src.video.wan_engine import WanVideoEngine


def sample_shot() -> Shot:
    return Shot(
        id="shot_001",
        type="dialogue",
        prompt="A nervous confession in a quiet cafe",
        character="xiaomei",
        dialogue="I should have told you earlier.",
        duration=4,
        camera="close_up",
    )


def test_wan_engine_uses_command_backend_when_configured(tmp_path: Path) -> None:
    backend_script = tmp_path / "mock_wan_backend.py"
    backend_script.write_text(
        "\n".join(
            [
                "import os",
                "import sys",
                "from pathlib import Path",
                "output = Path(sys.argv[1])",
                "mode = sys.argv[2]",
                "output.write_text(f'backend=command\\nmode={mode}\\nprompt={os.environ[\"AISD_SHOT_PROMPT\"]}', encoding='utf-8')",
            ]
        ),
        encoding="utf-8",
    )

    spec = ModelSpec(
        name="wan21",
        type="video_generation",
        model_id="Wan-AI/Wan2.1-I2V-14B-480P",
        vram_mb=20000,
        extras={
            "backend": {
                "type": "command",
                "argv": [sys.executable, str(backend_script), "{output_path}", "{mode}"],
                "fallback_to_placeholder": False,
            }
        },
    )
    engine = WanVideoEngine(model_spec=spec)

    clip_path = engine.generate(sample_shot(), tmp_path / "clips", mode="i2v")

    assert clip_path.exists()
    payload = clip_path.read_text(encoding="utf-8")
    assert "backend=command" in payload
    assert "mode=i2v" in payload
    assert "prompt=A nervous confession in a quiet cafe" in payload


def test_wan_engine_falls_back_to_placeholder_when_command_fails(tmp_path: Path) -> None:
    backend_script = tmp_path / "failing_backend.py"
    backend_script.write_text("raise SystemExit(2)\n", encoding="utf-8")

    spec = ModelSpec(
        name="wan21",
        type="video_generation",
        model_id="Wan-AI/Wan2.1-I2V-14B-480P",
        vram_mb=20000,
        extras={
            "backend": {
                "type": "command",
                "argv": [sys.executable, str(backend_script), "{output_path}"],
                "fallback_to_placeholder": True,
            }
        },
    )
    engine = WanVideoEngine(model_spec=spec)

    clip_path = engine.generate(sample_shot(), tmp_path / "clips", mode="i2v")

    assert clip_path.exists()
    payload = clip_path.read_text(encoding="utf-8")
    assert "backend=placeholder-fallback" in payload
    assert "command_exit_code=2" in payload


def test_wan_engine_raises_when_command_fails_without_fallback(tmp_path: Path) -> None:
    backend_script = tmp_path / "failing_backend.py"
    backend_script.write_text("raise SystemExit(3)\n", encoding="utf-8")

    spec = ModelSpec(
        name="wan21",
        type="video_generation",
        model_id="Wan-AI/Wan2.1-I2V-14B-480P",
        vram_mb=20000,
        extras={
            "backend": {
                "type": "command",
                "argv": [sys.executable, str(backend_script), "{output_path}"],
                "fallback_to_placeholder": False,
            }
        },
    )
    engine = WanVideoEngine(model_spec=spec)

    try:
        engine.generate(sample_shot(), tmp_path / "clips", mode="i2v")
    except RuntimeError as exc:
        assert "exit code 3" in str(exc)
    else:
        raise AssertionError("Expected wan engine command backend to fail")
