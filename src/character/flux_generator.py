import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from src.models.base import InferenceResult
from src.models.base import ModelSpec
from src.scriptwriter.storyboard import Script, Shot


@dataclass(frozen=True)
class CommandBackendConfig:
    argv: list[str]
    env: dict[str, str]
    fallback_to_placeholder: bool


class FluxReferenceGenerator:
    def __init__(self, model_spec: ModelSpec | None = None) -> None:
        self.model_spec = model_spec

    def generate_references(self, script: Script, output_dir: Path) -> dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        references: dict[str, Path] = {}

        for scene in script.scenes:
            if scene.character is None:
                continue

            reference_path = output_dir / f"{scene.id}.txt"
            backend = self._command_backend()
            if backend is not None:
                references[scene.id] = self._generate_via_command(
                    backend=backend,
                    shot=scene,
                    output_path=reference_path,
                )
                continue

            self._write_placeholder_output(reference_path, scene)
            references[scene.id] = reference_path

        return references

    def load_model(self) -> None:
        return None

    def unload_model(self) -> None:
        return None

    def infer(self, inputs: dict[str, object]) -> InferenceResult:
        path = Path(str(inputs["artifact_path"]))
        path.write_text("flux-placeholder", encoding="utf-8")
        return InferenceResult(artifact_path=path)

    @property
    def vram_required_mb(self) -> int:
        return 12_000

    def _generate_via_command(
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
                "AISD_SHOT_PROMPT": shot.prompt,
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
                f"Flux command backend failed with exit code {completed.returncode}: "
                f"{completed.stderr.strip() or completed.stdout.strip() or 'no output'}"
            )

        return self._write_placeholder_output(
            output_path,
            shot,
            generator_label="flux-placeholder-fallback",
            extra_lines=[
                f"command_exit_code={completed.returncode}",
                f"command_stdout={completed.stdout.strip()}",
                f"command_stderr={completed.stderr.strip()}",
            ],
        )

    def _write_placeholder_output(
        self,
        reference_path: Path,
        shot: Shot,
        generator_label: str = "flux-placeholder",
        extra_lines: list[str] | None = None,
    ) -> Path:
        reference_path.write_text(
            "\n".join(
                [
                    f"character={shot.character}",
                    f"prompt={shot.prompt}",
                    f"generator={generator_label}",
                    *list(extra_lines or []),
                ]
            ),
            encoding="utf-8",
        )
        return reference_path

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
        model_id = self.model_spec.model_id if self.model_spec is not None else "flux-placeholder"
        project_root = Path(__file__).resolve().parents[2]
        return {
            "output_path": str(output_path),
            "prompt": shot.prompt,
            "character": shot.character or "",
            "model_id": model_id,
            "shot_id": shot.id,
            "duration": str(shot.duration),
            "camera": shot.camera,
            "python_executable": sys.executable,
            "project_root": str(project_root),
        }
