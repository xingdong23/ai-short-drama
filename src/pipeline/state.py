import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PipelineState:
    current_step: str = "script"
    completed: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "PipelineState":
        if not path.exists():
            return cls()

        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            current_step=str(payload.get("current_step", "script")),
            completed=[str(item) for item in payload.get("completed", [])],
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "current_step": self.current_step,
                    "completed": self.completed,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def mark_completed(self, step: str, next_step: str) -> None:
        if step not in self.completed:
            self.completed.append(step)
        self.current_step = next_step
