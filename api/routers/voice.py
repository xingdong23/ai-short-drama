from api.schemas import APIResponse, VoiceSynthesizePayload, VoiceSynthesizeRequest
from fastapi import APIRouter

from src.pipeline.engine import PipelineEngine


router = APIRouter(prefix="/voice", tags=["voice"])
engine = PipelineEngine()


@router.post("/synthesize", response_model=APIResponse[VoiceSynthesizePayload])
def synthesize_voice(payload: VoiceSynthesizeRequest) -> APIResponse[VoiceSynthesizePayload]:
    workspace, audio_paths, synced_paths = engine.synthesize_voice_task(
        payload.task_id,
        payload.script.to_domain() if payload.script is not None else None,
    )

    return APIResponse(
        success=True,
        data=VoiceSynthesizePayload(
            task_id=workspace.task_id,
            audio_paths=audio_paths,
            synced_paths=synced_paths,
        ),
    )
