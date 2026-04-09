import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.models.base import ModelSpec
from src.scriptwriter.storyboard import Shot


@dataclass(frozen=True)
class CommandBackendConfig:
    argv: list[str]
    env: dict[str, str]
    fallback_to_placeholder: bool


class WanVideoEngine:
    def __init__(self, model_spec: ModelSpec | None = None) -> None:
        self.model_spec = model_spec

    def generate(
        self,
        shot: Shot,
        output_dir: Path,
        mode: str,
        reference_path: Path | None = None,
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        clip_path = output_dir / f"{shot.id}.mp4"
        backend = self._command_backend()
        if backend is not None:
            return self._generate_via_command(
                backend=backend,
                shot=shot,
                output_path=clip_path,
                mode=mode,
                reference_path=reference_path,
            )

        return self._write_placeholder_output(
            clip_path=clip_path,
            shot=shot,
            mode=mode,
            reference_path=reference_path,
        )

    def _generate_via_command(
        self,
        backend: CommandBackendConfig,
        shot: Shot,
        output_path: Path,
        mode: str,
        reference_path: Path | None,
    ) -> Path:
        fields = self._template_fields(
            shot=shot,
            output_path=output_path,
            mode=mode,
            reference_path=reference_path,
        )
        argv = [part.format(**fields) for part in backend.argv]
        env = os.environ.copy()
        env.update({key: value.format(**fields) for key, value in backend.env.items()})
        env.update(
            {
                "AISD_SHOT_ID": shot.id,
                "AISD_SHOT_PROMPT": shot.prompt,
                "AISD_OUTPUT_PATH": str(output_path),
                "AISD_MODE": mode,
                "AISD_REFERENCE_PATH": str(reference_path or ""),
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
                f"Wan command backend failed with exit code {completed.returncode}: "
                f"{completed.stderr.strip() or completed.stdout.strip() or 'no output'}"
            )

        return self._write_placeholder_output(
            clip_path=output_path,
            shot=shot,
            mode=mode,
            reference_path=reference_path,
            backend_label="placeholder-fallback",
            extra_lines=[
                f"command_exit_code={completed.returncode}",
                f"command_stdout={completed.stdout.strip()}",
                f"command_stderr={completed.stderr.strip()}",
            ],
        )

    def _write_placeholder_output(
        self,
        clip_path: Path,
        shot: Shot,
        mode: str,
        reference_path: Path | None,
        backend_label: str = "placeholder",
        extra_lines: list[str] | None = None,
    ) -> Path:
        clip_path.write_text(
            "\n".join(
                [
                    "engine=wan21",
                    f"backend={backend_label}",
                    f"mode={mode}",
                    f"shot_id={shot.id}",
                    f"prompt={shot.prompt}",
                    f"reference={reference_path or 'none'}",
                    *list(extra_lines or []),
                ]
            ),
            encoding="utf-8",
        )
        return clip_path

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

        fallback = backend.get("fallback_to_placeholder", True)
        return CommandBackendConfig(
            argv=list(raw_argv),
            env=dict(raw_env),
            fallback_to_placeholder=bool(fallback),
        )

    def _template_fields(
        self,
        shot: Shot,
        output_path: Path,
        mode: str,
        reference_path: Path | None,
    ) -> dict[str, str]:
        model_id = self.model_spec.model_id if self.model_spec is not None else "wan21-placeholder"
        return {
            "output_path": str(output_path),
            "mode": mode,
            "prompt": shot.prompt,
            "reference_path": str(reference_path or ""),
            "model_id": model_id,
            "shot_id": shot.id,
            "duration": str(shot.duration),
            "camera": shot.camera,
        }
