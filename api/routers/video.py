from api.schemas import APIResponse
from fastapi import APIRouter
from pydantic import BaseModel


class VideoPayload(BaseModel):
    status: str


router = APIRouter(prefix="/video", tags=["video"])


@router.post("/generate", response_model=APIResponse[VideoPayload])
def generate_video() -> APIResponse[VideoPayload]:
    return APIResponse(success=True, data=VideoPayload(status="placeholder-ready"))
