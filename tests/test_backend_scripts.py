import os
import subprocess
import sys
from pathlib import Path


def test_flux_backend_script_writes_reference_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "flux_reference.txt"
    env = os.environ.copy()
    env.update(
        {
            "AISD_SHOT_PROMPT": "A heroine under neon rain",
            "AISD_CHARACTER": "xiaomei",
            "AISD_MODEL_ID": "flux-model",
        }
    )

    subprocess.run(
        [
            sys.executable,
            "scripts/run_flux_backend.py",
            str(output_path),
            "xiaomei",
        ],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )

    assert output_path.exists()
    payload = output_path.read_text(encoding="utf-8")
    assert "generator=flux-wrapper-placeholder" in payload
    assert "character=xiaomei" in payload


def test_wan_backend_script_writes_clip_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "wan_clip.mp4"
    env = os.environ.copy()
    env.update(
        {
            "AISD_SHOT_PROMPT": "A quiet confession",
            "AISD_REFERENCE_PATH": "/tmp/reference.txt",
            "AISD_MODEL_ID": "wan-model",
        }
    )

    subprocess.run(
        [
            sys.executable,
            "scripts/run_wan_backend.py",
            str(output_path),
            "i2v",
        ],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )

    assert output_path.exists()
    payload = output_path.read_text(encoding="utf-8")
    assert "backend=wan-wrapper-placeholder" in payload
    assert "mode=i2v" in payload
