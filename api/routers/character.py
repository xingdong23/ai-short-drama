from api.schemas import (
    APIResponse,
    CharacterReferencePayload,
    CharacterReferenceRequest,
    CharacterTrainPayload,
    CharacterTrainRequest,
)
from fastapi import APIRouter

from src.config import get_settings
from src.character.flux_generator import FluxReferenceGenerator
from src.character.lora_trainer import LoRATrainer
from src.models.registry import ModelRegistry
from src.pipeline.engine import PipelineEngine


router = APIRouter(prefix="/character", tags=["character"])
settings = get_settings()
registry = ModelRegistry.from_yaml(settings.config_dir / "models.yaml")
reference_generator = FluxReferenceGenerator(registry.get("flux"))
lora_trainer = LoRATrainer()
pipeline_engine = PipelineEngine()


@router.post("/reference", response_model=APIResponse[CharacterReferencePayload])
def generate_reference(
    payload: CharacterReferenceRequest,
) -> APIResponse[CharacterReferencePayload]:
    workspace, references = pipeline_engine.generate_references_task(
        payload.task_id,
        payload.script.to_domain() if payload.script is not None else None,
    )
    return APIResponse(
        success=True,
        data=CharacterReferencePayload(
            task_id=workspace.task_id,
            reference_paths=references,
        ),
    )


@router.post("/train", response_model=APIResponse[CharacterTrainPayload])
def train_lora(payload: CharacterTrainRequest) -> APIResponse[CharacterTrainPayload]:
    weights_path = lora_trainer.train(payload.character_name, payload.output_dir)
    return APIResponse(
        success=True,
        data=CharacterTrainPayload(weights_path=weights_path),
    )
