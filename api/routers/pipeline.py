from pathlib import Path

from api.schemas import (
    APIResponse,
    PipelinePreflightPayload,
    PipelineResultPayload,
    PipelineRunStatusPayload,
    PipelineResumeRequest,
    PipelineRunRequest,
    PipelineStatusPayload,
    PreflightCheckPayload,
)
from fastapi import APIRouter

from src.pipeline.engine import PIPELINE_STEPS, PipelineEngine, PipelineRequest
from src.pipeline.preflight import PreflightChecker
from src.config import get_settings


router = APIRouter(prefix="/pipeline", tags=["pipeline"])
engine = PipelineEngine()
preflight_checker = PreflightChecker(get_settings())


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


@router.get("/preflight", response_model=APIResponse[PipelinePreflightPayload])
def preflight() -> APIResponse[PipelinePreflightPayload]:
    report = preflight_checker.run()
    return APIResponse(
        success=True,
        data=PipelinePreflightPayload(
            placeholder_mode=report.placeholder_mode,
            checks={
                name: PreflightCheckPayload(
                    status=check.status,
                    detail=check.detail,
                    path=check.path,
                    source=check.source,
                )
                for name, check in report.checks.items()
            },
        ),
    )
