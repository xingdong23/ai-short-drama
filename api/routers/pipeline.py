from pathlib import Path

from api.schemas import (
    APIResponse,
    PipelineResultPayload,
    PipelineRunStatusPayload,
    PipelineResumeRequest,
    PipelineRunRequest,
    PipelineStatusPayload,
)
from fastapi import APIRouter

from src.pipeline.engine import PIPELINE_STEPS, PipelineEngine, PipelineRequest


router = APIRouter(prefix="/pipeline", tags=["pipeline"])
engine = PipelineEngine()


@router.get("/status", response_model=APIResponse[PipelineStatusPayload])
def status(output_dir: Path | None = None) -> APIResponse[PipelineStatusPayload]:
    run = None
    if output_dir is not None:
        inspection = engine.inspect(output_dir)
        run = PipelineRunStatusPayload(
            output_dir=inspection.output_dir,
            status=inspection.status,
            current_step=inspection.current_step,
            completed_steps=inspection.completed_steps,
            progress_percent=inspection.progress_percent,
            theme=inspection.theme,
            started_at=inspection.started_at,
            updated_at=inspection.updated_at,
            completed_at=inspection.completed_at,
            failed_at=inspection.failed_at,
            last_error=inspection.last_error,
            script_path=inspection.script_path,
            final_video_path=inspection.final_video_path,
            manifest_path=inspection.manifest_path,
            artifact_counts=inspection.artifact_counts,
        )

    return APIResponse(
        success=True,
        data=PipelineStatusPayload(
            service="ai-short-drama",
            status="ready",
            steps=PIPELINE_STEPS,
            run=run,
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
