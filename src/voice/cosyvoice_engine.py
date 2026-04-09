from pathlib import Path

from src.scriptwriter.storyboard import Shot


class CosyVoiceEngine:
    def synthesize(self, shot: Shot, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / f"{shot.id}.wav"
        audio_path.write_text(
            "\n".join(
                [
                    "engine=cosyvoice",
                    f"shot_id={shot.id}",
                    f"dialogue={shot.dialogue or ''}",
                ]
            ),
            encoding="utf-8",
        )
        return audio_path
