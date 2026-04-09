from api.schemas import APIResponse, VideoGeneratePayload, VideoGenerateRequest
from fastapi import APIRouter

from src.config import get_settings
from src.models.registry import ModelRegistry
from src.video.shot_router import ShotRouter
from src.video.skyreels_engine import SkyReelsVideoEngine
from src.video.wan_engine import WanVideoEngine


router = APIRouter(prefix="/video", tags=["video"])
settings = get_settings()
registry = ModelRegistry.from_yaml(settings.config_dir / "models.yaml")
router_engine = ShotRouter(registry)
wan_engine = WanVideoEngine()
skyreels_engine = SkyReelsVideoEngine()


@router.post("/generate", response_model=APIResponse[VideoGeneratePayload])
def generate_video(payload: VideoGenerateRequest) -> APIResponse[VideoGeneratePayload]:
    clip_paths = {}
    script = payload.script.to_domain()

    for scene in script.scenes:
        reference_path = None
        if payload.references_dir is not None:
            reference_candidate = payload.references_dir / f"{scene.id}.txt"
            reference_path = reference_candidate if reference_candidate.exists() else None

        decision = router_engine.route(scene)
        engine = skyreels_engine if decision.engine_name.startswith("skyreels") else wan_engine
        clip_paths[scene.id] = engine.generate(
            shot=scene,
            output_dir=payload.output_dir,
            mode=decision.mode,
            reference_path=reference_path,
        )

    return APIResponse(
        success=True,
        data=VideoGeneratePayload(clip_paths=clip_paths),
    )
