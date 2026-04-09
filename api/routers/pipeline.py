from pathlib import Path

from api.schemas import (
    APIResponse,
    PipelinePreflightPayload,
    PipelineResultPayload,
    PipelineTaskCreatePayload,
    PipelineTaskCreateRequest,
    PipelineRunStatusPayload,
    PipelineResumeRequest,
    PipelineRunRequest,
    PipelineStatusPayload,
    PreflightCheckPayload,
)
from api.workspaces import workspace_to_payload
from fastapi import APIRouter

from src.pipeline.engine import PIPELINE_STEPS, PipelineEngine
from src.pipeline.preflight import PreflightChecker
from src.config import get_settings


router = APIRouter(prefix="/pipeline", tags=["pipeline"])
engine = PipelineEngine()
preflight_checker = PreflightChecker(get_settings())


@router.post("/tasks", response_model=APIResponse[PipelineTaskCreatePayload])
def create_task(payload: PipelineTaskCreateRequest) -> APIResponse[PipelineTaskCreatePayload]:
    workspace = engine.create_task(theme=payload.theme)
    return APIResponse(
        success=True,
        data=PipelineTaskCreatePayload(**workspace_to_payload(workspace).model_dump()),
    )


@router.get("/status", response_model=APIResponse[PipelineStatusPayload])
def status(
    task_id: str | None = None,
    output_dir: Path | None = None,
) -> APIResponse[PipelineStatusPayload]:
    run = None
    if task_id is not None:
        inspection = engine.inspect_task(task_id)
        run = PipelineRunStatusPayload(
            output_dir=inspection.output_dir,
            task_id=inspection.task_id,
            task_dir=inspection.output_dir,
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
            task_file_path=inspection.task_file_path,
            directories=inspection.directories,
            artifact_counts=inspection.artifact_counts,
        )
    elif output_dir is not None:
        inspection = engine.inspect(output_dir)
        run = PipelineRunStatusPayload(
            output_dir=inspection.output_dir,
            task_id=inspection.task_id,
            task_dir=inspection.output_dir,
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
            task_file_path=inspection.task_file_path,
            directories=inspection.directories,
            artifact_counts=inspection.artifact_counts,
        )

    return APIResponse(
        success=True,
        data=PipelineStatusPayload(
            service="ai-short-drama",
            status="ready",
            steps=PIPELINE_STEPS,
            task_root_dir=get_settings().output_dir,
            run=run,
        ),
    )


@router.post("/run", response_model=APIResponse[PipelineResultPayload])
def run_pipeline(payload: PipelineRunRequest) -> APIResponse[PipelineResultPayload]:
    result = engine.run_task(theme=payload.theme, task_id=payload.task_id)
    return APIResponse(
        success=True,
        data=PipelineResultPayload(
            task_id=result.task_id,
            task_dir=result.output_dir,
            task_file_path=result.task_file_path,
            output_dir=result.output_dir,
            final_video_path=result.final_video_path,
            completed_steps=result.completed_steps,
            directories=result.directories,
        ),
    )


@router.post("/resume", response_model=APIResponse[PipelineResultPayload])
def resume_pipeline(payload: PipelineResumeRequest) -> APIResponse[PipelineResultPayload]:
    result = engine.resume_task(payload.task_id)
    return APIResponse(
        success=True,
        data=PipelineResultPayload(
            task_id=result.task_id,
            task_dir=result.output_dir,
            task_file_path=result.task_file_path,
            output_dir=result.output_dir,
            final_video_path=result.final_video_path,
            completed_steps=result.completed_steps,
            directories=result.directories,
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
