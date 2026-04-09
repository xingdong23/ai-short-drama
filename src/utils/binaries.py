import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BinaryResolution:
    path: Path
    source: str


def resolve_binary(
    explicit_path: Path | None,
    env_var_name: str,
    fallback_names: list[str],
) -> BinaryResolution | None:
    if explicit_path is not None and explicit_path.exists():
        return BinaryResolution(path=explicit_path, source="explicit")

    env_value = os.getenv(env_var_name)
    if env_value:
        env_path = Path(env_value)
        if env_path.exists():
            return BinaryResolution(path=env_path, source="env")

    for name in fallback_names:
        resolved = shutil.which(name)
        if resolved:
            return BinaryResolution(path=Path(resolved), source="path")

    return None
