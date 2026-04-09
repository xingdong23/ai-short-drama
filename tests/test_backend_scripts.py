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


def test_flux_backend_script_can_delegate_to_external_command(tmp_path: Path) -> None:
    output_path = tmp_path / "flux_reference_delegate.txt"
    delegate_script = tmp_path / "delegate_flux.py"
    delegate_script.write_text(
        "\n".join(
            [
                "import os",
                "import sys",
                "from pathlib import Path",
                "Path(sys.argv[1]).write_text(",
                "    f'generator=flux-delegate\\ncharacter={sys.argv[2]}\\nprompt={os.environ[\"AISD_SHOT_PROMPT\"]}',",
                "    encoding='utf-8',",
                ")",
            ]
        ),
        encoding="utf-8",
    )

    env = os.environ.copy()
    env.update(
        {
            "AISD_SHOT_PROMPT": "A heroine under neon rain",
            "AISD_CHARACTER": "xiaomei",
            "AISD_MODEL_ID": "flux-model",
            "AISD_FLUX_DELEGATE_CMD": f"{sys.executable} {delegate_script} {{output_path}} {{character}}",
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
    assert "generator=flux-delegate" in payload
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


def test_wan_backend_script_can_delegate_to_external_command(tmp_path: Path) -> None:
    output_path = tmp_path / "wan_clip_delegate.mp4"
    delegate_script = tmp_path / "delegate_wan.py"
    delegate_script.write_text(
        "\n".join(
            [
                "import os",
                "import sys",
                "from pathlib import Path",
                "Path(sys.argv[1]).write_text(",
                "    f'backend=wan-delegate\\nmode={sys.argv[2]}\\nreference={os.environ[\"AISD_REFERENCE_PATH\"]}',",
                "    encoding='utf-8',",
                ")",
            ]
        ),
        encoding="utf-8",
    )

    env = os.environ.copy()
    env.update(
        {
            "AISD_SHOT_PROMPT": "A quiet confession",
            "AISD_REFERENCE_PATH": "/tmp/reference.txt",
            "AISD_MODEL_ID": "wan-model",
            "AISD_WAN_DELEGATE_CMD": f"{sys.executable} {delegate_script} {{output_path}} {{mode}}",
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
    assert "backend=wan-delegate" in payload
    assert "mode=i2v" in payload
