from api.schemas import (
    APIResponse,
    CharacterReferencePayload,
    CharacterReferenceRequest,
    CharacterTrainPayload,
    CharacterTrainRequest,
)
from fastapi import APIRouter

from src.character.flux_generator import FluxReferenceGenerator
from src.character.lora_trainer import LoRATrainer


router = APIRouter(prefix="/character", tags=["character"])
reference_generator = FluxReferenceGenerator()
lora_trainer = LoRATrainer()


@router.post("/reference", response_model=APIResponse[CharacterReferencePayload])
def generate_reference(
    payload: CharacterReferenceRequest,
) -> APIResponse[CharacterReferencePayload]:
    references = reference_generator.generate_references(
        payload.script.to_domain(),
        payload.output_dir,
    )
    return APIResponse(
        success=True,
        data=CharacterReferencePayload(reference_paths=references),
    )


@router.post("/train", response_model=APIResponse[CharacterTrainPayload])
def train_lora(payload: CharacterTrainRequest) -> APIResponse[CharacterTrainPayload]:
    weights_path = lora_trainer.train(payload.character_name, payload.output_dir)
    return APIResponse(
        success=True,
        data=CharacterTrainPayload(weights_path=weights_path),
    )
