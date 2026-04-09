from pathlib import Path


class FFmpegComposer:
    def compose(
        self,
        clips: list[Path],
        subtitle_path: Path,
        bgm_path: Path,
        output_path: Path,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            "composer=ffmpeg-placeholder",
            f"subtitle_path={subtitle_path}",
            f"bgm_path={bgm_path}",
        ]
        payload.extend(f"clip={clip}" for clip in clips)
        output_path.write_text("\n".join(payload), encoding="utf-8")
        return output_path
