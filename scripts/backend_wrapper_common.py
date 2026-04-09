import os
import shlex
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_template_fields(output_path: Path, **extra: str) -> dict[str, str]:
    fields = {
        "output_path": str(output_path),
        "prompt": os.getenv("AISD_SHOT_PROMPT", ""),
        "shot_id": os.getenv("AISD_SHOT_ID", ""),
        "dialogue": os.getenv("AISD_SHOT_DIALOGUE", ""),
        "character": os.getenv("AISD_CHARACTER", ""),
        "reference_path": os.getenv("AISD_REFERENCE_PATH", ""),
        "source_clip_path": os.getenv("AISD_SOURCE_CLIP_PATH", ""),
        "audio_path": os.getenv("AISD_AUDIO_PATH", ""),
        "model_id": os.getenv("AISD_MODEL_ID", ""),
        "python_executable": sys.executable,
        "project_root": str(PROJECT_ROOT),
    }
    fields.update(extra)
    return fields


def run_delegate_command(delegate_env_var: str, fields: dict[str, str]) -> int | None:
    command_template = os.getenv(delegate_env_var, "").strip()
    if not command_template:
        return None

    argv = shlex.split(command_template.format(**fields))
    completed = subprocess.run(argv, check=False)
    if completed.returncode != 0:
        return completed.returncode

    if not Path(fields["output_path"]).exists():
        print(
            f"{delegate_env_var} completed successfully but did not create {fields['output_path']}",
            file=sys.stderr,
        )
        return 1

    return 0
