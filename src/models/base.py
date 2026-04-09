from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class InferenceResult:
    artifact_path: Path
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelSpec:
    name: str
    type: str
    model_id: str
    vram_mb: int
    extras: dict[str, Any] = field(default_factory=dict)


class InferenceEngine(Protocol):
    def load_model(self) -> None: ...

    def unload_model(self) -> None: ...

    def infer(self, inputs: dict[str, Any]) -> InferenceResult: ...

    @property
    def vram_required_mb(self) -> int: ...
