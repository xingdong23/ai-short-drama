import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

from src.character.flux_generator import FluxReferenceGenerator
from src.compose.bgm import BGMMixer
from src.compose.ffmpeg_composer import FFmpegComposer
from src.compose.subtitle import SubtitleGenerator
from src.config import get_settings
from src.models.registry import ModelRegistry
from src.pipeline.state import PipelineState
from src.pipeline.tasks import TaskManager, TaskWorkspace
from src.scriptwriter.engine import ScriptwriterEngine
from src.scriptwriter.storyboard import Script
from src.video.shot_router import ShotRouter
from src.video.skyreels_engine import SkyReelsVideoEngine
from src.video.wan_engine import WanVideoEngine
from src.voice.cosyvoice_engine import CosyVoiceEngine
from src.voice.musetalk_engine import MuseTalkEngine


PIPELINE_STEPS = ["script", "character", "video", "voice", "compose"]


@dataclass(frozen=True)
class PipelineRequest:
    theme: str
    output_dir: Path


@dataclass(frozen=True)
class PipelineResult:
    output_dir: Path
    final_video_path: Path
    completed_steps: list[str]
    task_id: str | None = None
    task_file_path: Path | None = None
    directories: dict[str, Path] = field(default_factory=dict)


@dataclass(frozen=True)
class PipelineInspection:
    output_dir: Path
    task_id: str | None
    status: str
    current_step: str
    completed_steps: list[str]
    progress_percent: int
    theme: str | None
    started_at: str | None
    updated_at: str | None
    completed_at: str | None
    failed_at: str | None
    last_error: str | None
    script_path: Path | None
    final_video_path: Path | None
    manifest_path: Path | None
    task_file_path: Path | None
    directories: dict[str, Path]
    artifact_counts: dict[str, int]


class PipelineEngine:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.task_manager = TaskManager(settings.output_dir)
        self.registry = ModelRegistry.from_yaml(settings.config_dir / "models.yaml")
        self.scriptwriter = ScriptwriterEngine()
        self.reference_generator = FluxReferenceGenerator(self.registry.get("flux"))
        self.router = ShotRouter(self.registry)
        self.wan_engine = WanVideoEngine(self.registry.get("wan21"))
        self.skyreels_engine = SkyReelsVideoEngine()
        self.tts_engine = CosyVoiceEngine(self.registry.get("cosyvoice"))
        self.lip_sync_engine = MuseTalkEngine(self.registry.get("musetalk"))
        self.subtitle_generator = SubtitleGenerator()
        self.bgm_mixer = BGMMixer()
        self.composer = FFmpegComposer()

    def create_task(self, theme: str | None = None) -> TaskWorkspace:
        return self.task_manager.create(theme=theme)

    def run(self, request: PipelineRequest) -> PipelineResult:
        return self._execute(output_dir=request.output_dir, theme=request.theme, task_id=None)

    def run_task(self, theme: str, task_id: str | None = None) -> PipelineResult:
        workspace = self.task_manager.resolve(task_id) if task_id else self.create_task(theme=theme)
        self.task_manager.update_theme(workspace.task_id, theme)
        return self._execute(output_dir=workspace.task_dir, theme=theme, task_id=workspace.task_id)

    def resume(self, output_dir: Path) -> PipelineResult:
        return self._execute(output_dir=output_dir, theme=None, task_id=None)

    def resume_task(self, task_id: str) -> PipelineResult:
        workspace = self.task_manager.resolve(task_id)
        return self._execute(output_dir=workspace.task_dir, theme=None, task_id=workspace.task_id)

    def inspect(self, output_dir: Path) -> PipelineInspection:
        return self._build_inspection(output_dir, task_id=None)

    def inspect_task(self, task_id: str) -> PipelineInspection:
        workspace = self.task_manager.resolve(task_id)
        return self._build_inspection(workspace.task_dir, task_id=workspace.task_id)

    def generate_script_task(self, task_id: str, theme: str) -> tuple[TaskWorkspace, Script]:
        workspace = self.task_manager.update_theme(task_id, theme)
        script = self._execute_stage(
            workspace=workspace,
            step="script",
            next_step="character",
            theme=theme,
            action=lambda: self._generate_script(workspace, theme),
        )
        return workspace, script

    def generate_references_task(
        self,
        task_id: str,
        script: Script | None = None,
    ) -> tuple[TaskWorkspace, dict[str, Path]]:
        workspace, resolved_script = self._resolve_task_script(task_id, script)
        references = self._execute_stage(
            workspace=workspace,
            step="character",
            next_step="video",
            theme=resolved_script.theme,
            action=lambda: self.reference_generator.generate_references(
                resolved_script,
                workspace.references_dir,
            ),
        )
        return workspace, references

    def generate_video_task(
        self,
        task_id: str,
        script: Script | None = None,
    ) -> tuple[TaskWorkspace, dict[str, Path]]:
        workspace, resolved_script = self._resolve_task_script(task_id, script)
        clip_paths = self._execute_stage(
            workspace=workspace,
            step="video",
            next_step="voice",
            theme=resolved_script.theme,
            action=lambda: self._generate_video_clips(workspace, resolved_script),
        )
        return workspace, clip_paths

    def synthesize_voice_task(
        self,
        task_id: str,
        script: Script | None = None,
    ) -> tuple[TaskWorkspace, dict[str, Path], dict[str, Path]]:
        workspace, resolved_script = self._resolve_task_script(task_id, script)
        audio_paths, synced_paths = self._execute_stage(
            workspace=workspace,
            step="voice",
            next_step="compose",
            theme=resolved_script.theme,
            action=lambda: self._generate_voice_artifacts(workspace, resolved_script),
        )
        return workspace, audio_paths, synced_paths

    def compose_task(
        self,
        task_id: str,
        script: Script | None = None,
    ) -> tuple[TaskWorkspace, Path, Path, Path]:
        workspace, resolved_script = self._resolve_task_script(task_id, script)
        final_video_path, subtitle_path, bgm_path = self._execute_stage(
            workspace=workspace,
            step="compose",
            next_step="complete",
            theme=resolved_script.theme,
            finalize=True,
            action=lambda: self._compose_final_video(workspace, resolved_script),
        )
        return workspace, final_video_path, subtitle_path, bgm_path

    def _execute(
        self,
        output_dir: Path,
        theme: str | None,
        task_id: str | None,
    ) -> PipelineResult:
        self._ensure_layout(output_dir)
        state_path = output_dir / "state.json"
        state = PipelineState.load(state_path)
        self._write_manifest(output_dir, task_id=task_id)

        script = self._load_existing_script(output_dir)
        if script is None and theme is None:
            raise ValueError("Resume requires an existing script.json")

        try:
            if "script" not in state.completed:
                if theme is None:
                    raise ValueError("Theme is required for a fresh pipeline run")
                state.mark_running("script", theme=theme, task_id=task_id)
                state.save(state_path)
                self._write_manifest(output_dir, task_id=task_id)
                script = self.scriptwriter.generate(theme)
                self._write_script(output_dir, script)
                self._update_task_theme(task_id, theme)
                state.mark_completed("script", "character")
                state.save(state_path)
                self._write_manifest(output_dir, task_id=task_id)

            if script is None:
                raise RuntimeError("Script must be available before continuing")

            references_dir = output_dir / "references"
            clips_dir = output_dir / "clips"
            audio_dir = output_dir / "audio"
            synced_dir = output_dir / "synced"
            compose_dir = output_dir / "compose"

            if "character" not in state.completed:
                state.mark_running("character", theme=script.theme, task_id=task_id)
                state.save(state_path)
                self._write_manifest(output_dir, task_id=task_id)
                self.reference_generator.generate_references(script, references_dir)
                state.mark_completed("character", "video")
                state.save(state_path)
                self._write_manifest(output_dir, task_id=task_id)

            clip_paths: list[Path] = []
            if "video" not in state.completed:
                state.mark_running("video", theme=script.theme, task_id=task_id)
                state.save(state_path)
                self._write_manifest(output_dir, task_id=task_id)
                for scene in script.scenes:
                    reference_candidate = references_dir / f"{scene.id}.txt"
                    reference_path = reference_candidate if reference_candidate.exists() else None
                    decision = self.router.route(scene)
                    engine = (
                        self.skyreels_engine
                        if decision.engine_name.startswith("skyreels")
                        else self.wan_engine
                    )
                    clip_paths.append(
                        engine.generate(
                            shot=scene,
                            output_dir=clips_dir,
                            mode=decision.mode,
                            reference_path=reference_path,
                        )
                    )
                state.mark_completed("video", "voice")
                state.save(state_path)
                self._write_manifest(output_dir, task_id=task_id)
            else:
                clip_paths = sorted(clips_dir.glob("*.mp4"))

            synced_paths: list[Path] = []
            if "voice" not in state.completed:
                state.mark_running("voice", theme=script.theme, task_id=task_id)
                state.save(state_path)
                self._write_manifest(output_dir, task_id=task_id)
                for scene in script.scenes:
                    clip_path = clips_dir / f"{scene.id}.mp4"
                    if scene.dialogue:
                        audio_path = self.tts_engine.synthesize(scene, audio_dir)
                        synced_paths.append(
                            self.lip_sync_engine.lip_sync(
                                shot=scene,
                                clip_path=clip_path,
                                output_dir=synced_dir,
                                audio_path=audio_path,
                            )
                        )
                    else:
                        synced_paths.append(
                            self.lip_sync_engine.lip_sync(
                                shot=scene,
                                clip_path=clip_path,
                                output_dir=synced_dir,
                            )
                        )
                state.mark_completed("voice", "compose")
                state.save(state_path)
                self._write_manifest(output_dir, task_id=task_id)
            else:
                synced_paths = sorted(synced_dir.glob("*.mp4"))

            final_video_path = output_dir / "final.mp4"
            if "compose" not in state.completed:
                state.mark_running("compose", theme=script.theme, task_id=task_id)
                state.save(state_path)
                self._write_manifest(output_dir, task_id=task_id)
                subtitle_path = self.subtitle_generator.generate(script, compose_dir)
                bgm_path = self.bgm_mixer.select_track(compose_dir)
                self.composer.compose(
                    clips=synced_paths or clip_paths,
                    subtitle_path=subtitle_path,
                    bgm_path=bgm_path,
                    output_path=final_video_path,
                )
                state.mark_completed("compose", "complete")
                state.mark_finished()
                state.save(state_path)
                self._write_manifest(output_dir, task_id=task_id)

            return PipelineResult(
                output_dir=output_dir,
                final_video_path=final_video_path,
                completed_steps=list(state.completed),
                task_id=task_id,
                task_file_path=(output_dir / "task.json") if (output_dir / "task.json").exists() else None,
                directories=self._workspace_directories(output_dir),
            )
        except Exception as exc:
            state.mark_failed(state.current_step, str(exc))
            state.save(state_path)
            self._write_manifest(output_dir, task_id=task_id)
            raise

    def _ensure_layout(self, output_dir: Path) -> None:
        for directory in [
            output_dir,
            output_dir / "references",
            output_dir / "clips",
            output_dir / "audio",
            output_dir / "synced",
            output_dir / "compose",
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def _workspace_directories(self, output_dir: Path) -> dict[str, Path]:
        return {
            "references": output_dir / "references",
            "clips": output_dir / "clips",
            "audio": output_dir / "audio",
            "synced": output_dir / "synced",
            "compose": output_dir / "compose",
        }

    def _load_existing_script(self, output_dir: Path) -> Script | None:
        script_path = output_dir / "script.json"
        if not script_path.exists():
            return None
        payload = json.loads(script_path.read_text(encoding="utf-8"))
        return Script.from_dict(payload)

    def _write_script(self, output_dir: Path, script: Script) -> None:
        script_path = output_dir / "script.json"
        script_path.write_text(
            json.dumps(script.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _generate_script(self, workspace: TaskWorkspace, theme: str) -> Script:
        script = self.scriptwriter.generate(theme)
        self._write_script(workspace.task_dir, script)
        self._update_task_theme(workspace.task_id, theme)
        return script

    def _resolve_task_script(
        self,
        task_id: str,
        script: Script | None,
    ) -> tuple[TaskWorkspace, Script]:
        workspace = self.task_manager.resolve(task_id)
        if script is not None:
            self._write_script(workspace.task_dir, script)
            self._update_task_theme(workspace.task_id, script.theme)
            return workspace, script

        existing_script = self._load_existing_script(workspace.task_dir)
        if existing_script is None:
            raise ValueError("Task does not have script.json yet")
        self._update_task_theme(workspace.task_id, existing_script.theme)
        return workspace, existing_script

    def _execute_stage(
        self,
        workspace: TaskWorkspace,
        step: str,
        next_step: str,
        action,
        *,
        theme: str | None = None,
        finalize: bool = False,
    ):
        state = PipelineState.load(workspace.state_path)
        try:
            state.mark_running(step, theme=theme, task_id=workspace.task_id)
            self._save_task_state(workspace, state)
            result = action()
            state.mark_completed(step, next_step)
            if finalize:
                state.mark_finished()
            self._save_task_state(workspace, state)
            return result
        except Exception as exc:
            state.mark_failed(step, str(exc))
            self._save_task_state(workspace, state)
            raise

    def _save_task_state(self, workspace: TaskWorkspace, state: PipelineState) -> None:
        state.save(workspace.state_path)
        self._write_manifest(workspace.task_dir, task_id=workspace.task_id)

    def _update_task_theme(self, task_id: str | None, theme: str | None) -> None:
        if task_id is None:
            return
        self.task_manager.update_theme(task_id, theme)

    def _generate_video_clips(
        self,
        workspace: TaskWorkspace,
        script: Script,
    ) -> dict[str, Path]:
        clip_paths: dict[str, Path] = {}
        for scene in script.scenes:
            reference_candidate = workspace.references_dir / f"{scene.id}.txt"
            reference_path = reference_candidate if reference_candidate.exists() else None
            decision = self.router.route(scene)
            engine = (
                self.skyreels_engine
                if decision.engine_name.startswith("skyreels")
                else self.wan_engine
            )
            clip_paths[scene.id] = engine.generate(
                shot=scene,
                output_dir=workspace.clips_dir,
                mode=decision.mode,
                reference_path=reference_path,
            )
        return clip_paths

    def _generate_voice_artifacts(
        self,
        workspace: TaskWorkspace,
        script: Script,
    ) -> tuple[dict[str, Path], dict[str, Path]]:
        audio_paths: dict[str, Path] = {}
        synced_paths: dict[str, Path] = {}
        for scene in script.scenes:
            clip_path = workspace.clips_dir / f"{scene.id}.mp4"
            audio_path = None
            if scene.dialogue:
                audio_path = self.tts_engine.synthesize(scene, workspace.audio_dir)
                audio_paths[scene.id] = audio_path

            synced_paths[scene.id] = self.lip_sync_engine.lip_sync(
                shot=scene,
                clip_path=clip_path,
                output_dir=workspace.synced_dir,
                audio_path=audio_path,
            )
        return audio_paths, synced_paths

    def _compose_final_video(
        self,
        workspace: TaskWorkspace,
        script: Script,
    ) -> tuple[Path, Path, Path]:
        subtitle_path = self.subtitle_generator.generate(script, workspace.compose_dir)
        bgm_path = self.bgm_mixer.select_track(workspace.compose_dir)
        synced_candidates = sorted(workspace.synced_dir.glob("*.mp4"))
        clips = synced_candidates or [workspace.clips_dir / f"{scene.id}.mp4" for scene in script.scenes]
        final_video_path = self.composer.compose(
            clips=clips,
            subtitle_path=subtitle_path,
            bgm_path=bgm_path,
            output_path=workspace.final_video_path,
        )
        return final_video_path, subtitle_path, bgm_path

    def _build_inspection(self, output_dir: Path, task_id: str | None) -> PipelineInspection:
        state = PipelineState.load(output_dir / "state.json")
        task_payload = self._load_task_payload(output_dir)
        resolved_task_id = (
            task_id
            or state.task_id
            or self._maybe_string(task_payload.get("task_id"))
        )
        progress_percent = int((len(state.completed) / len(PIPELINE_STEPS)) * 100)
        script_path = output_dir / "script.json"
        final_video_path = output_dir / "final.mp4"
        manifest_path = output_dir / "manifest.json"
        task_file_path = output_dir / "task.json"

        return PipelineInspection(
            output_dir=output_dir,
            task_id=resolved_task_id,
            status=state.status,
            current_step=state.current_step,
            completed_steps=list(state.completed),
            progress_percent=progress_percent,
            theme=state.theme,
            started_at=state.started_at,
            updated_at=state.updated_at,
            completed_at=state.completed_at,
            failed_at=state.failed_at,
            last_error=state.last_error,
            script_path=script_path if script_path.exists() else None,
            final_video_path=final_video_path if final_video_path.exists() else None,
            manifest_path=manifest_path if manifest_path.exists() else None,
            task_file_path=task_file_path if task_file_path.exists() else None,
            directories=self._workspace_directories(output_dir),
            artifact_counts={
                "references": self._count_files(output_dir / "references"),
                "clips": self._count_files(output_dir / "clips"),
                "audio": self._count_files(output_dir / "audio"),
                "synced": self._count_files(output_dir / "synced"),
                "compose": self._count_files(output_dir / "compose"),
            },
        )

    def _write_manifest(self, output_dir: Path, task_id: str | None) -> None:
        inspection = self._build_inspection(output_dir, task_id=task_id)
        manifest_path = output_dir / "manifest.json"
        manifest_payload = {
            "task_id": inspection.task_id,
            "output_dir": str(inspection.output_dir),
            "task_dir": str(inspection.output_dir),
            "status": inspection.status,
            "current_step": inspection.current_step,
            "completed_steps": inspection.completed_steps,
            "progress_percent": inspection.progress_percent,
            "theme": inspection.theme,
            "started_at": inspection.started_at,
            "updated_at": inspection.updated_at,
            "completed_at": inspection.completed_at,
            "failed_at": inspection.failed_at,
            "last_error": inspection.last_error,
            "script_path": str(inspection.script_path) if inspection.script_path else None,
            "final_video_path": str(inspection.final_video_path) if inspection.final_video_path else None,
            "task_file_path": str(inspection.task_file_path) if inspection.task_file_path else None,
            "directories": {
                name: str(path)
                for name, path in inspection.directories.items()
            },
            "artifact_counts": inspection.artifact_counts,
        }
        manifest_path.write_text(
            json.dumps(manifest_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_task_payload(self, output_dir: Path) -> dict[str, object]:
        task_file_path = output_dir / "task.json"
        if not task_file_path.exists():
            return {}
        return json.loads(task_file_path.read_text(encoding="utf-8"))

    def _count_files(self, directory: Path) -> int:
        if not directory.exists():
            return 0
        return sum(1 for path in directory.iterdir() if path.is_file())

    @staticmethod
    def _maybe_string(value: object) -> str | None:
        return value if isinstance(value, str) else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI short drama pipeline scaffold")
    parser.add_argument("--input", help="Story theme for a fresh run")
    parser.add_argument("--output", help="Output directory for a fresh run")
    parser.add_argument("--resume", help="Resume from an existing run directory")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    engine = PipelineEngine()

    if args.resume:
        result = engine.resume(Path(args.resume))
    else:
        if not args.input or not args.output:
            raise SystemExit("--input and --output are required unless --resume is used")
        result = engine.run(PipelineRequest(theme=args.input, output_dir=Path(args.output)))

    print(result.final_video_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
