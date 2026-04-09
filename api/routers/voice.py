from api.schemas import APIResponse
from fastapi import APIRouter
from pydantic import BaseModel


class VoicePayload(BaseModel):
    status: str


router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/synthesize", response_model=APIResponse[VoicePayload])
def synthesize_voice() -> APIResponse[VoicePayload]:
    return APIResponse(success=True, data=VoicePayload(status="placeholder-ready"))
