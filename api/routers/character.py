from api.schemas import APIResponse
from fastapi import APIRouter
from pydantic import BaseModel


class CharacterReferencePayload(BaseModel):
    status: str


router = APIRouter(prefix="/character", tags=["character"])


@router.post("/reference", response_model=APIResponse[CharacterReferencePayload])
def generate_reference() -> APIResponse[CharacterReferencePayload]:
    return APIResponse(success=True, data=CharacterReferencePayload(status="placeholder-ready"))


@router.post("/train", response_model=APIResponse[CharacterReferencePayload])
def train_lora() -> APIResponse[CharacterReferencePayload]:
    return APIResponse(success=True, data=CharacterReferencePayload(status="placeholder-ready"))
