from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from src.scriptwriter.storyboard import Script, Shot, ShotType


PayloadT = TypeVar("PayloadT")


class APIResponse(BaseModel, Generic[PayloadT]):
    success: bool
    data: PayloadT | None = None
    error: str | None = None


class ShotPayload(BaseModel):
    id: str
    type: ShotType
    prompt: str
    character: str | None
    dialogue: str | None
    duration: int
    camera: str

    def to_domain(self) -> Shot:
        return Shot(
            id=self.id,
            type=self.type,
            prompt=self.prompt,
            character=self.character,
            dialogue=self.dialogue,
            duration=self.duration,
            camera=self.camera,
        )

    @classmethod
    def from_domain(cls, shot: Shot) -> "ShotPayload":
        return cls(
            id=shot.id,
            type=shot.type,
            prompt=shot.prompt,
            character=shot.character,
            dialogue=shot.dialogue,
            duration=shot.duration,
            camera=shot.camera,
        )


class ScriptPayload(BaseModel):
    title: str
    theme: str
    scenes: list[ShotPayload]

    def to_domain(self) -> Script:
        return Script(
            title=self.title,
            theme=self.theme,
            scenes=[scene.to_domain() for scene in self.scenes],
        )

    @classmethod
    def from_domain(cls, script: Script) -> "ScriptPayload":
        return cls(
            title=script.title,
            theme=script.theme,
            scenes=[ShotPayload.from_domain(scene) for scene in script.scenes],
        )


class PipelineRunRequest(BaseModel):
    theme: str = Field(min_length=1)
    output_dir: Path


class PipelineResumeRequest(BaseModel):
    output_dir: Path


class PipelineResultPayload(BaseModel):
    output_dir: Path
    final_video_path: Path
    completed_steps: list[str]


class PipelineRunStatusPayload(BaseModel):
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


class PipelineStatusPayload(BaseModel):
    service: str
    status: str
    steps: list[str]
    run: PipelineRunStatusPayload | None = None


class PreflightCheckPayload(BaseModel):
    status: str
    detail: str
    path: Path | None = None
    source: str | None = None


class PipelinePreflightPayload(BaseModel):
    placeholder_mode: bool
    checks: dict[str, PreflightCheckPayload]


class ScriptGenerateRequest(BaseModel):
    theme: str = Field(min_length=1)
    output_dir: Path | None = None


class ScriptGeneratePayload(BaseModel):
    script: ScriptPayload
    script_path: Path | None = None


class CharacterReferenceRequest(BaseModel):
    script: ScriptPayload
    output_dir: Path


class CharacterReferencePayload(BaseModel):
    reference_paths: dict[str, Path]


class CharacterTrainRequest(BaseModel):
    character_name: str = Field(min_length=1)
    output_dir: Path


class CharacterTrainPayload(BaseModel):
    weights_path: Path


class VideoGenerateRequest(BaseModel):
    script: ScriptPayload
    output_dir: Path
    references_dir: Path | None = None


class VideoGeneratePayload(BaseModel):
    clip_paths: dict[str, Path]


class VoiceSynthesizeRequest(BaseModel):
    script: ScriptPayload
    clips_dir: Path
    output_dir: Path


class VoiceSynthesizePayload(BaseModel):
    audio_paths: dict[str, Path]
    synced_paths: dict[str, Path]


class ComposeFinalRequest(BaseModel):
    script: ScriptPayload
    clips_dir: Path
    output_dir: Path


class ComposeFinalPayload(BaseModel):
    final_video_path: Path
    subtitle_path: Path
    bgm_path: Path
