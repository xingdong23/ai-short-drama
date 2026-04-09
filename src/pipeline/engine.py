import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from src.character.flux_generator import FluxReferenceGenerator
from src.compose.bgm import BGMMixer
from src.compose.ffmpeg_composer import FFmpegComposer
from src.compose.subtitle import SubtitleGenerator
from src.config import get_settings
from src.models.registry import ModelRegistry
from src.pipeline.state import PipelineState
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


@dataclass(frozen=True)
class PipelineInspection:
    output_dir: Path
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
    artifact_counts: dict[str, int]


class PipelineEngine:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.registry = ModelRegistry.from_yaml(settings.config_dir / "models.yaml")
        self.scriptwriter = ScriptwriterEngine()
        self.reference_generator = FluxReferenceGenerator()
        self.router = ShotRouter(self.registry)
        self.wan_engine = WanVideoEngine()
        self.skyreels_engine = SkyReelsVideoEngine()
        self.tts_engine = CosyVoiceEngine()
        self.lip_sync_engine = MuseTalkEngine()
        self.subtitle_generator = SubtitleGenerator()
        self.bgm_mixer = BGMMixer()
        self.composer = FFmpegComposer()

    def run(self, request: PipelineRequest) -> PipelineResult:
        return self._execute(output_dir=request.output_dir, theme=request.theme)

    def resume(self, output_dir: Path) -> PipelineResult:
        return self._execute(output_dir=output_dir, theme=None)

    def inspect(self, output_dir: Path) -> PipelineInspection:
        return self._build_inspection(output_dir)

    def _execute(self, output_dir: Path, theme: str | None) -> PipelineResult:
        self._ensure_layout(output_dir)
        state_path = output_dir / "state.json"
        state = PipelineState.load(state_path)
        self._write_manifest(output_dir)

        script = self._load_existing_script(output_dir)
        if script is None and theme is None:
            raise ValueError("Resume requires an existing script.json")

        try:
            if "script" not in state.completed:
                if theme is None:
                    raise ValueError("Theme is required for a fresh pipeline run")
                state.mark_running("script", theme=theme)
                state.save(state_path)
                self._write_manifest(output_dir)
                script = self.scriptwriter.generate(theme)
                self._write_script(output_dir, script)
                state.mark_completed("script", "character")
                state.save(state_path)
                self._write_manifest(output_dir)

            if script is None:
                raise RuntimeError("Script must be available before continuing")

            references_dir = output_dir / "references"
            clips_dir = output_dir / "clips"
            audio_dir = output_dir / "audio"
            synced_dir = output_dir / "synced"
            compose_dir = output_dir / "compose"

            if "character" not in state.completed:
                state.mark_running("character")
                state.save(state_path)
                self._write_manifest(output_dir)
                self.reference_generator.generate_references(script, references_dir)
                state.mark_completed("character", "video")
                state.save(state_path)
                self._write_manifest(output_dir)

            clip_paths: list[Path] = []
            if "video" not in state.completed:
                state.mark_running("video")
                state.save(state_path)
                self._write_manifest(output_dir)
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
                self._write_manifest(output_dir)
            else:
                clip_paths = sorted(clips_dir.glob("*.mp4"))

            synced_paths: list[Path] = []
            if "voice" not in state.completed:
                state.mark_running("voice")
                state.save(state_path)
                self._write_manifest(output_dir)
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
                self._write_manifest(output_dir)
            else:
                synced_paths = sorted(synced_dir.glob("*.mp4"))

            final_video_path = output_dir / "final.mp4"
            if "compose" not in state.completed:
                state.mark_running("compose")
                state.save(state_path)
                self._write_manifest(output_dir)
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
                self._write_manifest(output_dir)

            return PipelineResult(
                output_dir=output_dir,
                final_video_path=final_video_path,
                completed_steps=list(state.completed),
            )
        except Exception as exc:
            state.mark_failed(state.current_step, str(exc))
            state.save(state_path)
            self._write_manifest(output_dir)
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

    def _build_inspection(self, output_dir: Path) -> PipelineInspection:
        state = PipelineState.load(output_dir / "state.json")
        progress_percent = int((len(state.completed) / len(PIPELINE_STEPS)) * 100)
        script_path = output_dir / "script.json"
        final_video_path = output_dir / "final.mp4"
        manifest_path = output_dir / "manifest.json"

        return PipelineInspection(
            output_dir=output_dir,
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
            artifact_counts={
                "references": self._count_files(output_dir / "references"),
                "clips": self._count_files(output_dir / "clips"),
                "audio": self._count_files(output_dir / "audio"),
                "synced": self._count_files(output_dir / "synced"),
                "compose": self._count_files(output_dir / "compose"),
            },
        )

    def _write_manifest(self, output_dir: Path) -> None:
        inspection = self._build_inspection(output_dir)
        manifest_path = output_dir / "manifest.json"
        manifest_payload = {
            "output_dir": str(inspection.output_dir),
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
            "artifact_counts": inspection.artifact_counts,
        }
        manifest_path.write_text(
            json.dumps(manifest_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _count_files(self, directory: Path) -> int:
        if not directory.exists():
            return 0
        return sum(1 for path in directory.iterdir() if path.is_file())


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
