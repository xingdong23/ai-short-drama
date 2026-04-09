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

    def _execute(self, output_dir: Path, theme: str | None) -> PipelineResult:
        self._ensure_layout(output_dir)
        state_path = output_dir / "state.json"
        state = PipelineState.load(state_path)

        script = self._load_existing_script(output_dir)
        if script is None and theme is None:
            raise ValueError("Resume requires an existing script.json")

        if "script" not in state.completed:
            if theme is None:
                raise ValueError("Theme is required for a fresh pipeline run")
            script = self.scriptwriter.generate(theme)
            self._write_script(output_dir, script)
            state.mark_completed("script", "character")
            state.save(state_path)

        if script is None:
            raise RuntimeError("Script must be available before continuing")

        references_dir = output_dir / "references"
        clips_dir = output_dir / "clips"
        audio_dir = output_dir / "audio"
        synced_dir = output_dir / "synced"
        compose_dir = output_dir / "compose"

        if "character" not in state.completed:
            self.reference_generator.generate_references(script, references_dir)
            state.mark_completed("character", "video")
            state.save(state_path)

        clip_paths: list[Path] = []
        if "video" not in state.completed:
            for scene in script.scenes:
                reference_candidate = references_dir / f"{scene.id}.txt"
                reference_path = reference_candidate if reference_candidate.exists() else None
                decision = self.router.route(scene)
                engine = self.skyreels_engine if decision.engine_name.startswith("skyreels") else self.wan_engine
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
        else:
            clip_paths = sorted(clips_dir.glob("*.mp4"))

        synced_paths: list[Path] = []
        if "voice" not in state.completed:
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
        else:
            synced_paths = sorted(synced_dir.glob("*.mp4"))

        final_video_path = output_dir / "final.mp4"
        if "compose" not in state.completed:
            subtitle_path = self.subtitle_generator.generate(script, compose_dir)
            bgm_path = self.bgm_mixer.select_track(compose_dir)
            self.composer.compose(
                clips=synced_paths or clip_paths,
                subtitle_path=subtitle_path,
                bgm_path=bgm_path,
                output_path=final_video_path,
            )
            state.mark_completed("compose", "complete")
            state.save(state_path)

        return PipelineResult(
            output_dir=output_dir,
            final_video_path=final_video_path,
            completed_steps=list(state.completed),
        )

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
