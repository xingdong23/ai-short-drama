from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    project_name: str = "ai-short-drama"
    api_v1_prefix: str = "/api/v1"
    config_dir: Path = Path("config")
    output_dir: Path = Path("output")
    ffmpeg_path: Path | None = None
    ffprobe_path: Path | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AISD_",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
