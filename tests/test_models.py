from pathlib import Path

from src.models.registry import ModelRegistry


def test_model_registry_loads_default_models() -> None:
    registry = ModelRegistry.from_yaml(Path("config/models.yaml"))

    assert "flux" in registry.models
    assert "wan21" in registry.models
    assert registry.get("flux").vram_mb == 12000
    assert registry.get("wan21").type == "video_generation"
