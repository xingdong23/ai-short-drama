import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


TASK_STAGE_DIRS = ("references", "clips", "audio", "synced", "compose")


@dataclass(frozen=True)
class TaskWorkspace:
    task_id: str
    task_dir: Path
    created_at: str | None = None
    theme: str | None = None

    @property
    def task_file_path(self) -> Path:
        return self.task_dir / "task.json"

    @property
    def state_path(self) -> Path:
        return self.task_dir / "state.json"

    @property
    def manifest_path(self) -> Path:
        return self.task_dir / "manifest.json"

    @property
    def script_path(self) -> Path:
        return self.task_dir / "script.json"

    @property
    def final_video_path(self) -> Path:
        return self.task_dir / "final.mp4"

    @property
    def references_dir(self) -> Path:
        return self.task_dir / "references"

    @property
    def clips_dir(self) -> Path:
        return self.task_dir / "clips"

    @property
    def audio_dir(self) -> Path:
        return self.task_dir / "audio"

    @property
    def synced_dir(self) -> Path:
        return self.task_dir / "synced"

    @property
    def compose_dir(self) -> Path:
        return self.task_dir / "compose"

    def directories(self) -> dict[str, Path]:
        return {
            "references": self.references_dir,
            "clips": self.clips_dir,
            "audio": self.audio_dir,
            "synced": self.synced_dir,
            "compose": self.compose_dir,
        }


class TaskManager:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir

    def create(self, theme: str | None = None) -> TaskWorkspace:
        task_id = self._generate_task_id()
        workspace = TaskWorkspace(
            task_id=task_id,
            task_dir=self.root_dir / task_id,
            created_at=self._timestamp(),
            theme=theme,
        )
        self._ensure_layout(workspace)
        self._write_metadata(workspace, theme=theme)
        return workspace

    def resolve(self, task_id: str) -> TaskWorkspace:
        task_dir = self.root_dir / task_id
        task_file_path = task_dir / "task.json"
        if not task_dir.exists():
            raise FileNotFoundError(f"Task '{task_id}' does not exist")

        payload: dict[str, object] = {}
        if task_file_path.exists():
            payload = json.loads(task_file_path.read_text(encoding="utf-8"))

        workspace = TaskWorkspace(
            task_id=task_id,
            task_dir=task_dir,
            created_at=self._maybe_string(payload.get("created_at")),
            theme=self._maybe_string(payload.get("theme")),
        )
        self._ensure_layout(workspace)
        if not task_file_path.exists():
            self._write_metadata(workspace, theme=workspace.theme)
        return workspace

    def update_theme(self, task_id: str, theme: str | None) -> TaskWorkspace:
        workspace = self.resolve(task_id)
        self._write_metadata(workspace, theme=theme)
        return TaskWorkspace(
            task_id=workspace.task_id,
            task_dir=workspace.task_dir,
            created_at=workspace.created_at,
            theme=theme,
        )

    def _write_metadata(self, workspace: TaskWorkspace, theme: str | None) -> None:
        workspace.task_dir.mkdir(parents=True, exist_ok=True)
        existing_payload: dict[str, object] = {}
        if workspace.task_file_path.exists():
            existing_payload = json.loads(workspace.task_file_path.read_text(encoding="utf-8"))

        created_at = self._maybe_string(existing_payload.get("created_at")) or workspace.created_at or self._timestamp()
        payload = {
            "task_id": workspace.task_id,
            "task_dir": str(workspace.task_dir),
            "created_at": created_at,
            "updated_at": self._timestamp(),
            "theme": theme,
            "script_path": str(workspace.script_path),
            "state_path": str(workspace.state_path),
            "manifest_path": str(workspace.manifest_path),
            "final_video_path": str(workspace.final_video_path),
            "task_file_path": str(workspace.task_file_path),
            "directories": {
                name: str(path)
                for name, path in workspace.directories().items()
            },
        }
        workspace.task_file_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _ensure_layout(self, workspace: TaskWorkspace) -> None:
        workspace.task_dir.mkdir(parents=True, exist_ok=True)
        for directory in workspace.directories().values():
            directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _generate_task_id() -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        return f"task-{timestamp}-{secrets.token_hex(3)}"

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _maybe_string(value: object) -> str | None:
        return value if isinstance(value, str) else None
