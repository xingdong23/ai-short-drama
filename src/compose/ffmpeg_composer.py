from pathlib import Path

from src.config import get_settings
from src.utils.binaries import resolve_binary


class FFmpegComposer:
    def __init__(self) -> None:
        settings = get_settings()
        self.ffmpeg = resolve_binary(
            explicit_path=settings.ffmpeg_path,
            env_var_name="AISD_FFMPEG_PATH",
            fallback_names=["ffmpeg"],
        )
        self.ffprobe = resolve_binary(
            explicit_path=settings.ffprobe_path,
            env_var_name="AISD_FFPROBE_PATH",
            fallback_names=["ffprobe"],
        )

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
            f"ffmpeg_path={self.ffmpeg.path if self.ffmpeg else 'none'}",
            f"ffprobe_path={self.ffprobe.path if self.ffprobe else 'none'}",
            f"subtitle_path={subtitle_path}",
            f"bgm_path={bgm_path}",
        ]
        payload.extend(f"clip={clip}" for clip in clips)
        output_path.write_text("\n".join(payload), encoding="utf-8")
        return output_path
