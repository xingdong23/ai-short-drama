from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


PayloadT = TypeVar("PayloadT")


class APIResponse(BaseModel, Generic[PayloadT]):
    success: bool
    data: PayloadT | None = None
    error: str | None = None


class PipelineRunRequest(BaseModel):
    theme: str = Field(min_length=1)
    output_dir: Path


class PipelineResumeRequest(BaseModel):
    output_dir: Path


class PipelineResultPayload(BaseModel):
    output_dir: Path
    final_video_path: Path
    completed_steps: list[str]


class PipelineStatusPayload(BaseModel):
    service: str
    status: str
    steps: list[str]
