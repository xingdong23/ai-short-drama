import sys
from pathlib import Path

from src.models.base import ModelSpec
from src.scriptwriter.storyboard import Shot
from src.voice.cosyvoice_engine import CosyVoiceEngine
from src.voice.musetalk_engine import MuseTalkEngine


def sample_shot() -> Shot:
    return Shot(
        id="shot_001",
        type="dialogue",
        prompt="A quiet confession in the studio",
        character="xiaomei",
        dialogue="I finally know what to say.",
        duration=4,
        camera="close_up",
    )


def test_cosyvoice_engine_uses_command_backend_when_configured(tmp_path: Path) -> None:
    backend_script = tmp_path / "mock_cosyvoice_backend.py"
    backend_script.write_text(
        "\n".join(
            [
                "import os",
                "import sys",
                "from pathlib import Path",
                "output = Path(sys.argv[1])",
                "output.write_text(f'backend=command\\ndialogue={os.environ[\"AISD_SHOT_DIALOGUE\"]}', encoding='utf-8')",
            ]
        ),
        encoding="utf-8",
    )

    spec = ModelSpec(
        name="cosyvoice",
        type="tts",
        model_id="FunAudioLLM/CosyVoice2-0.5B",
        vram_mb=2000,
        extras={
            "backend": {
                "type": "command",
                "argv": [sys.executable, str(backend_script), "{output_path}"],
                "fallback_to_placeholder": False,
            }
        },
    )
    engine = CosyVoiceEngine(model_spec=spec)

    audio_path = engine.synthesize(sample_shot(), tmp_path / "audio")

    assert audio_path.exists()
    payload = audio_path.read_text(encoding="utf-8")
    assert "backend=command" in payload
    assert "dialogue=I finally know what to say." in payload


def test_cosyvoice_engine_falls_back_when_command_fails(tmp_path: Path) -> None:
    backend_script = tmp_path / "failing_cosyvoice_backend.py"
    backend_script.write_text("raise SystemExit(4)\n", encoding="utf-8")

    spec = ModelSpec(
        name="cosyvoice",
        type="tts",
        model_id="FunAudioLLM/CosyVoice2-0.5B",
        vram_mb=2000,
        extras={
            "backend": {
                "type": "command",
                "argv": [sys.executable, str(backend_script), "{output_path}"],
                "fallback_to_placeholder": True,
            }
        },
    )
    engine = CosyVoiceEngine(model_spec=spec)

    audio_path = engine.synthesize(sample_shot(), tmp_path / "audio")

    payload = audio_path.read_text(encoding="utf-8")
    assert "backend=placeholder-fallback" in payload
    assert "command_exit_code=4" in payload


def test_musetalk_engine_uses_command_backend_when_configured(tmp_path: Path) -> None:
    backend_script = tmp_path / "mock_musetalk_backend.py"
    backend_script.write_text(
        "\n".join(
            [
                "import os",
                "import sys",
                "from pathlib import Path",
                "output = Path(sys.argv[1])",
                "output.write_text(f'backend=command\\nsource_clip={os.environ[\"AISD_SOURCE_CLIP_PATH\"]}\\naudio_path={os.environ[\"AISD_AUDIO_PATH\"]}', encoding='utf-8')",
            ]
        ),
        encoding="utf-8",
    )

    spec = ModelSpec(
        name="musetalk",
        type="lip_sync",
        model_id="musetalk-v1.5",
        vram_mb=4000,
        extras={
            "backend": {
                "type": "command",
                "argv": [sys.executable, str(backend_script), "{output_path}"],
                "fallback_to_placeholder": False,
            }
        },
    )
    engine = MuseTalkEngine(model_spec=spec)
    clip_path = tmp_path / "clips" / "shot_001.mp4"
    clip_path.parent.mkdir(parents=True, exist_ok=True)
    clip_path.write_text("clip", encoding="utf-8")
    audio_path = tmp_path / "audio" / "shot_001.wav"
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    audio_path.write_text("audio", encoding="utf-8")

    synced_path = engine.lip_sync(
        shot=sample_shot(),
        clip_path=clip_path,
        output_dir=tmp_path / "synced",
        audio_path=audio_path,
    )

    assert synced_path.exists()
    payload = synced_path.read_text(encoding="utf-8")
    assert "backend=command" in payload
    assert f"source_clip={clip_path}" in payload
    assert f"audio_path={audio_path}" in payload


def test_musetalk_engine_falls_back_when_command_fails(tmp_path: Path) -> None:
    backend_script = tmp_path / "failing_musetalk_backend.py"
    backend_script.write_text("raise SystemExit(6)\n", encoding="utf-8")

    spec = ModelSpec(
        name="musetalk",
        type="lip_sync",
        model_id="musetalk-v1.5",
        vram_mb=4000,
        extras={
            "backend": {
                "type": "command",
                "argv": [sys.executable, str(backend_script), "{output_path}"],
                "fallback_to_placeholder": True,
            }
        },
    )
    engine = MuseTalkEngine(model_spec=spec)
    clip_path = tmp_path / "clips" / "shot_001.mp4"
    clip_path.parent.mkdir(parents=True, exist_ok=True)
    clip_path.write_text("clip", encoding="utf-8")

    synced_path = engine.lip_sync(
        shot=sample_shot(),
        clip_path=clip_path,
        output_dir=tmp_path / "synced",
    )

    payload = synced_path.read_text(encoding="utf-8")
    assert "backend=placeholder-fallback" in payload
    assert "command_exit_code=6" in payload
