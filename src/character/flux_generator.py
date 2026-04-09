from pathlib import Path

from src.models.base import InferenceResult
from src.scriptwriter.storyboard import Script


class FluxReferenceGenerator:
    def generate_references(self, script: Script, output_dir: Path) -> dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        references: dict[str, Path] = {}

        for scene in script.scenes:
            if scene.character is None:
                continue

            reference_path = output_dir / f"{scene.id}.txt"
            reference_path.write_text(
                "\n".join(
                    [
                        f"character={scene.character}",
                        f"prompt={scene.prompt}",
                        "generator=flux-placeholder",
                    ]
                ),
                encoding="utf-8",
            )
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
