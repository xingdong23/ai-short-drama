from pathlib import Path

from src.scriptwriter.storyboard import Script


class SubtitleGenerator:
    def generate(self, script: Script, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        subtitle_path = output_dir / "subtitles.srt"

        lines: list[str] = []
        current_second = 0
        cue_index = 1
        for scene in script.scenes:
            if not scene.dialogue:
                current_second += scene.duration
                continue

            start = self._format_timestamp(current_second)
            current_second += scene.duration
            end = self._format_timestamp(current_second)
            lines.extend([str(cue_index), f"{start} --> {end}", scene.dialogue, ""])
            cue_index += 1

        subtitle_path.write_text("\n".join(lines), encoding="utf-8")
        return subtitle_path

    def _format_timestamp(self, total_seconds: int) -> str:
        minutes, seconds = divmod(total_seconds, 60)
        return f"00:{minutes:02d}:{seconds:02d},000"
