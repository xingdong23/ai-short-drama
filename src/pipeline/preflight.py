from dataclasses import dataclass
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from src.config import AppSettings
from src.utils.binaries import BinaryResolution, resolve_binary


@dataclass(frozen=True)
class PreflightCheck:
    status: str
    detail: str
    path: Path | None = None
    source: str | None = None


@dataclass(frozen=True)
class PreflightReport:
    placeholder_mode: bool
    checks: dict[str, PreflightCheck]


class PreflightChecker:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def run(self) -> PreflightReport:
        pipeline_config_path = self.settings.config_dir / "pipeline.yaml"
        models_config_path = self.settings.config_dir / "models.yaml"
        characters_config_path = self.settings.config_dir / "characters.yaml"

        ffmpeg = resolve_binary(
            explicit_path=self.settings.ffmpeg_path,
            env_var_name="AISD_FFMPEG_PATH",
            fallback_names=["ffmpeg"],
        )
        ffprobe = resolve_binary(
            explicit_path=self.settings.ffprobe_path,
            env_var_name="AISD_FFPROBE_PATH",
            fallback_names=["ffprobe"],
        )
        placeholder_mode = self._load_placeholder_mode(pipeline_config_path)

        return PreflightReport(
            placeholder_mode=placeholder_mode,
            checks={
                "pipeline_config": self._config_check(pipeline_config_path),
                "models_config": self._config_check(models_config_path),
                "characters_config": self._config_check(characters_config_path),
                "ffmpeg": self._binary_check(ffmpeg, "ffmpeg"),
                "ffprobe": self._binary_check(ffprobe, "ffprobe"),
            },
        )

    def _load_placeholder_mode(self, path: Path) -> bool:
        if not path.exists():
            return False
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        pipeline = payload.get("pipeline", {})
        if not isinstance(pipeline, dict):
            return False
        placeholder_mode = pipeline.get("placeholder_mode", False)
        return bool(placeholder_mode)

    def _config_check(self, path: Path) -> PreflightCheck:
        if path.exists():
            return PreflightCheck(status="ok", detail=f"Found {path.name}", path=path)
        return PreflightCheck(status="missing", detail=f"Missing {path.name}")

    def _binary_check(
        self,
        resolution: BinaryResolution | None,
        binary_name: str,
    ) -> PreflightCheck:
        if resolution is None:
            return PreflightCheck(status="missing", detail=f"{binary_name} not found")
        return PreflightCheck(
            status="ok",
            detail=f"{binary_name} resolved via {resolution.source}",
            path=resolution.path,
            source=resolution.source,
        )
