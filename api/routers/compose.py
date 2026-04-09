from api.schemas import APIResponse, ComposeFinalPayload, ComposeFinalRequest
from fastapi import APIRouter

from src.pipeline.engine import PipelineEngine


router = APIRouter(prefix="/compose", tags=["compose"])
engine = PipelineEngine()


@router.post("/final", response_model=APIResponse[ComposeFinalPayload])
def compose_final(payload: ComposeFinalRequest) -> APIResponse[ComposeFinalPayload]:
    workspace, final_video_path, subtitle_path, bgm_path = engine.compose_task(
        payload.task_id,
        payload.script.to_domain() if payload.script is not None else None,
    )

    return APIResponse(
        success=True,
        data=ComposeFinalPayload(
            task_id=workspace.task_id,
            final_video_path=final_video_path,
            subtitle_path=subtitle_path,
            bgm_path=bgm_path,
        ),
    )
