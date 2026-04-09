from api.schemas import APIResponse, VideoGeneratePayload, VideoGenerateRequest
from fastapi import APIRouter

from src.pipeline.engine import PipelineEngine


router = APIRouter(prefix="/video", tags=["video"])
engine = PipelineEngine()


@router.post("/generate", response_model=APIResponse[VideoGeneratePayload])
def generate_video(payload: VideoGenerateRequest) -> APIResponse[VideoGeneratePayload]:
    workspace, clip_paths = engine.generate_video_task(
        payload.task_id,
        payload.script.to_domain() if payload.script is not None else None,
    )

    return APIResponse(
        success=True,
        data=VideoGeneratePayload(
            task_id=workspace.task_id,
            clip_paths=clip_paths,
        ),
    )
