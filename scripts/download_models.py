from pathlib import Path

from src.models.registry import ModelRegistry


def main() -> int:
    registry = ModelRegistry.from_yaml(Path("config/models.yaml"))
    for model in registry.models.values():
        print(f"{model.name}: {model.model_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
