import sys
from pathlib import Path

from src.character.flux_generator import FluxReferenceGenerator
from src.models.base import ModelSpec
from src.scriptwriter.storyboard import Script, Shot


def sample_script() -> Script:
    return Script(
        title="Episode 1: Flux Test",
        theme="flux adapter",
        scenes=[
            Shot(
                id="shot_001",
                type="dialogue",
                prompt="A heroine stands under neon rain",
                character="xiaomei",
                dialogue="We have to move now.",
                duration=4,
                camera="close_up",
            ),
            Shot(
                id="shot_002",
                type="establishing",
                prompt="An empty skyline",
                character=None,
                dialogue=None,
                duration=3,
                camera="slow_pan",
            ),
        ],
    )


def test_flux_generator_uses_command_backend_when_configured(tmp_path: Path) -> None:
    backend_script = tmp_path / "mock_flux_backend.py"
    backend_script.write_text(
        "\n".join(
            [
                "import os",
                "import sys",
                "from pathlib import Path",
                "output = Path(sys.argv[1])",
                "character = sys.argv[2]",
                "output.write_text(f'backend=command\\ncharacter={character}\\nprompt={os.environ[\"AISD_SHOT_PROMPT\"]}', encoding='utf-8')",
            ]
        ),
        encoding="utf-8",
    )

    spec = ModelSpec(
        name="flux",
        type="image_generation",
        model_id="black-forest-labs/FLUX.1-dev",
        vram_mb=12000,
        extras={
            "backend": {
                "type": "command",
                "argv": [sys.executable, str(backend_script), "{output_path}", "{character}"],
                "fallback_to_placeholder": False,
            }
        },
    )
    generator = FluxReferenceGenerator(model_spec=spec)

    references = generator.generate_references(sample_script(), tmp_path / "references")

    assert list(references) == ["shot_001"]
    payload = references["shot_001"].read_text(encoding="utf-8")
    assert "backend=command" in payload
    assert "character=xiaomei" in payload
    assert "prompt=A heroine stands under neon rain" in payload


def test_flux_generator_falls_back_when_command_fails(tmp_path: Path) -> None:
    backend_script = tmp_path / "failing_flux_backend.py"
    backend_script.write_text("raise SystemExit(5)\n", encoding="utf-8")

    spec = ModelSpec(
        name="flux",
        type="image_generation",
        model_id="black-forest-labs/FLUX.1-dev",
        vram_mb=12000,
        extras={
            "backend": {
                "type": "command",
                "argv": [sys.executable, str(backend_script), "{output_path}"],
                "fallback_to_placeholder": True,
            }
        },
    )
    generator = FluxReferenceGenerator(model_spec=spec)

    references = generator.generate_references(sample_script(), tmp_path / "references")

    payload = references["shot_001"].read_text(encoding="utf-8")
    assert "generator=flux-placeholder-fallback" in payload
    assert "command_exit_code=5" in payload


def test_flux_generator_raises_when_command_fails_without_fallback(tmp_path: Path) -> None:
    backend_script = tmp_path / "failing_flux_backend.py"
    backend_script.write_text("raise SystemExit(7)\n", encoding="utf-8")

    spec = ModelSpec(
        name="flux",
        type="image_generation",
        model_id="black-forest-labs/FLUX.1-dev",
        vram_mb=12000,
        extras={
            "backend": {
                "type": "command",
                "argv": [sys.executable, str(backend_script), "{output_path}"],
                "fallback_to_placeholder": False,
            }
        },
    )
    generator = FluxReferenceGenerator(model_spec=spec)

    try:
        generator.generate_references(sample_script(), tmp_path / "references")
    except RuntimeError as exc:
        assert "exit code 7" in str(exc)
    else:
        raise AssertionError("Expected flux backend failure to propagate")
