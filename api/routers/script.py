from api.schemas import APIResponse
from fastapi import APIRouter
from pydantic import BaseModel


class ScriptPayload(BaseModel):
    status: str


router = APIRouter(prefix="/script", tags=["script"])


@router.post("/generate", response_model=APIResponse[ScriptPayload])
def generate_script() -> APIResponse[ScriptPayload]:
    return APIResponse(success=True, data=ScriptPayload(status="placeholder-ready"))
