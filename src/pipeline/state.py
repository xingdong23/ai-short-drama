import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class PipelineState:
    current_step: str = "script"
    completed: list[str] = field(default_factory=list)
    status: str = "pending"
    started_at: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None
    failed_at: str | None = None
    last_error: str | None = None
    theme: str | None = None

    @classmethod
    def load(cls, path: Path) -> "PipelineState":
        if not path.exists():
            return cls()

        payload = json.loads(path.read_text(encoding="utf-8"))
        current_step = str(payload.get("current_step", "script"))
        completed = [str(item) for item in payload.get("completed", [])]
        status = payload.get("status")
        if not isinstance(status, str):
            status = cls._infer_status(current_step, completed)
        return cls(
            current_step=current_step,
            completed=completed,
            status=status,
            started_at=cls._maybe_string(payload.get("started_at")),
            updated_at=cls._maybe_string(payload.get("updated_at")),
            completed_at=cls._maybe_string(payload.get("completed_at")),
            failed_at=cls._maybe_string(payload.get("failed_at")),
            last_error=cls._maybe_string(payload.get("last_error")),
            theme=cls._maybe_string(payload.get("theme")),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "current_step": self.current_step,
                    "completed": self.completed,
                    "status": self.status,
                    "started_at": self.started_at,
                    "updated_at": self.updated_at,
                    "completed_at": self.completed_at,
                    "failed_at": self.failed_at,
                    "last_error": self.last_error,
                    "theme": self.theme,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def mark_running(self, step: str, theme: str | None = None) -> None:
        now = self._timestamp()
        if self.started_at is None:
            self.started_at = now
        self.updated_at = now
        self.status = "running"
        self.current_step = step
        self.failed_at = None
        self.last_error = None
        if theme is not None:
            self.theme = theme

    def mark_completed(self, step: str, next_step: str) -> None:
        if step not in self.completed:
            self.completed.append(step)
        self.current_step = next_step
        self.updated_at = self._timestamp()

    def mark_finished(self) -> None:
        now = self._timestamp()
        self.status = "completed"
        self.current_step = "complete"
        self.updated_at = now
        self.completed_at = now
        self.failed_at = None
        self.last_error = None

    def mark_failed(self, step: str, error_message: str) -> None:
        now = self._timestamp()
        self.status = "failed"
        self.current_step = step
        self.updated_at = now
        self.failed_at = now
        self.last_error = error_message

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _maybe_string(value: object) -> str | None:
        return value if isinstance(value, str) else None

    @staticmethod
    def _infer_status(current_step: str, completed: list[str]) -> str:
        if current_step == "complete":
            return "completed"
        if completed:
            return "running"
        return "pending"
