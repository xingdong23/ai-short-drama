import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from src.models.base import ModelSpec
from src.scriptwriter.storyboard import Shot


@dataclass(frozen=True)
class CommandBackendConfig:
    argv: list[str]
    env: dict[str, str]
    fallback_to_placeholder: bool


class CosyVoiceEngine:
    def __init__(self, model_spec: ModelSpec | None = None) -> None:
        self.model_spec = model_spec

    def synthesize(self, shot: Shot, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / f"{shot.id}.wav"
        backend = self._command_backend()
        if backend is not None:
            return self._synthesize_via_command(
                backend=backend,
                shot=shot,
                output_path=audio_path,
            )

        return self._write_placeholder_output(audio_path, shot)

    def _synthesize_via_command(
        self,
        backend: CommandBackendConfig,
        shot: Shot,
        output_path: Path,
    ) -> Path:
        fields = self._template_fields(shot, output_path)
        argv = [part.format(**fields) for part in backend.argv]
        env = os.environ.copy()
        env.update({key: value.format(**fields) for key, value in backend.env.items()})
        env.update(
            {
                "AISD_SHOT_ID": shot.id,
                "AISD_SHOT_DIALOGUE": shot.dialogue or "",
                "AISD_OUTPUT_PATH": str(output_path),
                "AISD_CHARACTER": shot.character or "",
                "AISD_MODEL_ID": fields["model_id"],
            }
        )

        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        if completed.returncode == 0 and output_path.exists():
            return output_path

        if not backend.fallback_to_placeholder:
            raise RuntimeError(
                f"CosyVoice command backend failed with exit code {completed.returncode}: "
                f"{completed.stderr.strip() or completed.stdout.strip() or 'no output'}"
            )

        return self._write_placeholder_output(
            output_path,
            shot,
            backend_label="placeholder-fallback",
            extra_lines=[
                f"command_exit_code={completed.returncode}",
                f"command_stdout={completed.stdout.strip()}",
                f"command_stderr={completed.stderr.strip()}",
            ],
        )

    def _write_placeholder_output(
        self,
        audio_path: Path,
        shot: Shot,
        backend_label: str = "placeholder",
        extra_lines: list[str] | None = None,
    ) -> Path:
        audio_path.write_text(
            "\n".join(
                [
                    "engine=cosyvoice",
                    f"backend={backend_label}",
                    f"shot_id={shot.id}",
                    f"character={shot.character or ''}",
                    f"dialogue={shot.dialogue or ''}",
                    *list(extra_lines or []),
                ]
            ),
            encoding="utf-8",
        )
        return audio_path

    def _command_backend(self) -> CommandBackendConfig | None:
        if self.model_spec is None:
            return None
        backend = self.model_spec.extras.get("backend")
        if not isinstance(backend, dict):
            return None
        if backend.get("type") != "command":
            return None

        raw_argv = backend.get("argv", [])
        raw_env = backend.get("env", {})
        if not isinstance(raw_argv, list) or not all(isinstance(item, str) for item in raw_argv):
            return None
        if not isinstance(raw_env, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in raw_env.items()
        ):
            return None

        return CommandBackendConfig(
            argv=list(raw_argv),
            env=dict(raw_env),
            fallback_to_placeholder=bool(backend.get("fallback_to_placeholder", True)),
        )

    def _template_fields(self, shot: Shot, output_path: Path) -> dict[str, str]:
        model_id = self.model_spec.model_id if self.model_spec is not None else "cosyvoice-placeholder"
        project_root = Path(__file__).resolve().parents[2]
        return {
            "output_path": str(output_path),
            "dialogue": shot.dialogue or "",
            "character": shot.character or "",
            "model_id": model_id,
            "shot_id": shot.id,
            "prompt": shot.prompt,
            "duration": str(shot.duration),
            "camera": shot.camera,
            "python_executable": sys.executable,
            "project_root": str(project_root),
        }
