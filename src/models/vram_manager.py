from dataclasses import dataclass, field

from src.models.base import ModelSpec


@dataclass
class VRAMManager:
    total_vram_mb: int = 24_000
    loaded_models: dict[str, ModelSpec] = field(default_factory=dict)

    @property
    def used_vram_mb(self) -> int:
        return sum(model.vram_mb for model in self.loaded_models.values())

    @property
    def available_vram_mb(self) -> int:
        return self.total_vram_mb - self.used_vram_mb

    def can_load(self, model: ModelSpec) -> bool:
        return model.vram_mb <= self.available_vram_mb

    def load(self, model: ModelSpec) -> None:
        if not self.can_load(model):
            raise RuntimeError(
                f"Insufficient VRAM for {model.name}: "
                f"need {model.vram_mb}MB, have {self.available_vram_mb}MB"
            )
        self.loaded_models[model.name] = model

    def unload(self, model_name: str) -> None:
        self.loaded_models.pop(model_name, None)

    def unload_all(self) -> None:
        self.loaded_models.clear()
