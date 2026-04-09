from pathlib import Path

from src.scriptwriter.storyboard import Shot


class WanVideoEngine:
    def generate(
        self,
        shot: Shot,
        output_dir: Path,
        mode: str,
        reference_path: Path | None = None,
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        clip_path = output_dir / f"{shot.id}.mp4"
        clip_path.write_text(
            "\n".join(
                [
                    "engine=wan21",
                    f"mode={mode}",
                    f"shot_id={shot.id}",
                    f"prompt={shot.prompt}",
                    f"reference={reference_path or 'none'}",
                ]
            ),
            encoding="utf-8",
        )
        return clip_path
