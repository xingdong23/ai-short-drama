from pathlib import Path

from src.scriptwriter.storyboard import Shot


class MuseTalkEngine:
    def lip_sync(
        self,
        shot: Shot,
        clip_path: Path,
        output_dir: Path,
        audio_path: Path | None = None,
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        synced_path = output_dir / f"{shot.id}.mp4"
        synced_path.write_text(
            "\n".join(
                [
                    "engine=musetalk",
                    f"shot_id={shot.id}",
                    f"source_clip={clip_path}",
                    f"audio_path={audio_path or 'none'}",
                ]
            ),
            encoding="utf-8",
        )
        return synced_path
