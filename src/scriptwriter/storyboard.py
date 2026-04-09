from dataclasses import asdict, dataclass
from typing import Literal


ShotType = Literal["establishing", "dialogue", "action", "transition"]


@dataclass(frozen=True)
class Shot:
    id: str
    type: ShotType
    prompt: str
    character: str | None
    dialogue: str | None
    duration: int
    camera: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Script:
    title: str
    theme: str
    scenes: list[Shot]

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "theme": self.theme,
            "scenes": [scene.to_dict() for scene in self.scenes],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "Script":
        raw_scenes = payload.get("scenes", [])
        if not isinstance(raw_scenes, list):
            raise TypeError("Script scenes must be a list")

        scenes = [
            Shot(
                id=str(scene["id"]),
                type=scene["type"],
                prompt=str(scene["prompt"]),
                character=scene.get("character"),
                dialogue=scene.get("dialogue"),
                duration=int(scene["duration"]),
                camera=str(scene["camera"]),
            )
            for scene in raw_scenes
            if isinstance(scene, dict)
        ]

        return cls(
            title=str(payload.get("title", "Untitled Episode")),
            theme=str(payload.get("theme", "untitled theme")),
            scenes=scenes,
        )
