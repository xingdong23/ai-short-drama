from dataclasses import dataclass

from src.models.registry import ModelRegistry
from src.scriptwriter.storyboard import Shot


@dataclass(frozen=True)
class RouteDecision:
    engine_name: str
    mode: str


class ShotRouter:
    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry

    def route(self, shot: Shot) -> RouteDecision:
        if shot.type == "transition" and "skyreels_13b" in self.registry.models:
            return RouteDecision(engine_name="skyreels_13b", mode="flf2v")
        if shot.type == "establishing":
            return RouteDecision(engine_name="wan21", mode="t2v")
        if shot.type in {"dialogue", "action"}:
            return RouteDecision(engine_name="wan21", mode="i2v")
        return RouteDecision(engine_name="wan21", mode="t2v")
