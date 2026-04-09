from api.schemas import (
    APIResponse,
    PipelineResultPayload,
    PipelineResumeRequest,
    PipelineRunRequest,
    PipelineStatusPayload,
)
from fastapi import APIRouter

from src.pipeline.engine import PIPELINE_STEPS, PipelineEngine, PipelineRequest


router = APIRouter(prefix="/pipeline", tags=["pipeline"])
engine = PipelineEngine()


@router.get("/status", response_model=APIResponse[PipelineStatusPayload])
def status() -> APIResponse[PipelineStatusPayload]:
    return APIResponse(
        success=True,
        data=PipelineStatusPayload(
            service="ai-short-drama",
            status="ready",
            steps=PIPELINE_STEPS,
        ),
    )


@router.post("/run", response_model=APIResponse[PipelineResultPayload])
def run_pipeline(payload: PipelineRunRequest) -> APIResponse[PipelineResultPayload]:
    result = engine.run(
        PipelineRequest(
            theme=payload.theme,
            output_dir=payload.output_dir,
        )
    )
    return APIResponse(
        success=True,
        data=PipelineResultPayload(
            output_dir=result.output_dir,
            final_video_path=result.final_video_path,
            completed_steps=result.completed_steps,
        ),
    )


@router.post("/resume", response_model=APIResponse[PipelineResultPayload])
def resume_pipeline(payload: PipelineResumeRequest) -> APIResponse[PipelineResultPayload]:
    result = engine.resume(payload.output_dir)
    return APIResponse(
        success=True,
        data=PipelineResultPayload(
            output_dir=result.output_dir,
            final_video_path=result.final_video_path,
            completed_steps=result.completed_steps,
        ),
    )
