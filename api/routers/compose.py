from api.schemas import APIResponse
from fastapi import APIRouter
from pydantic import BaseModel


class ComposePayload(BaseModel):
    status: str


router = APIRouter(prefix="/compose", tags=["compose"])


@router.post("/final", response_model=APIResponse[ComposePayload])
def compose_final() -> APIResponse[ComposePayload]:
    return APIResponse(success=True, data=ComposePayload(status="placeholder-ready"))
