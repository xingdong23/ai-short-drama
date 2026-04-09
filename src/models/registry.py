from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from src.models.base import ModelSpec


@dataclass
class ModelRegistry:
    models: dict[str, ModelSpec]

    @classmethod
    def from_yaml(cls, path: Path) -> "ModelRegistry":
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        model_entries = payload.get("models", {})
        models: dict[str, ModelSpec] = {}

        for name, raw_spec in model_entries.items():
            spec: dict[str, Any] = dict(raw_spec)
            model_id = str(spec.pop("model_id", name))
            vram_mb = int(spec.pop("vram_mb", 0))
            model_type = str(spec.pop("type"))
            models[name] = ModelSpec(
                name=name,
                type=model_type,
                model_id=model_id,
                vram_mb=vram_mb,
                extras=spec,
            )

        return cls(models=models)

    def get(self, name: str) -> ModelSpec:
        return self.models[name]
