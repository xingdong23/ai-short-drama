from api.schemas import APIResponse, VoiceSynthesizePayload, VoiceSynthesizeRequest
from fastapi import APIRouter

from src.config import get_settings
from src.models.registry import ModelRegistry
from src.voice.cosyvoice_engine import CosyVoiceEngine
from src.voice.musetalk_engine import MuseTalkEngine


router = APIRouter(prefix="/voice", tags=["voice"])
settings = get_settings()
registry = ModelRegistry.from_yaml(settings.config_dir / "models.yaml")
tts_engine = CosyVoiceEngine(registry.get("cosyvoice"))
lip_sync_engine = MuseTalkEngine(registry.get("musetalk"))


@router.post("/synthesize", response_model=APIResponse[VoiceSynthesizePayload])
def synthesize_voice(payload: VoiceSynthesizeRequest) -> APIResponse[VoiceSynthesizePayload]:
    audio_dir = payload.output_dir / "audio"
    synced_dir = payload.output_dir / "synced"

    audio_paths = {}
    synced_paths = {}
    script = payload.script.to_domain()

    for scene in script.scenes:
        clip_path = payload.clips_dir / f"{scene.id}.mp4"
        audio_path = None
        if scene.dialogue:
            audio_path = tts_engine.synthesize(scene, audio_dir)
            audio_paths[scene.id] = audio_path

        synced_paths[scene.id] = lip_sync_engine.lip_sync(
            shot=scene,
            clip_path=clip_path,
            output_dir=synced_dir,
            audio_path=audio_path,
        )

    return APIResponse(
        success=True,
        data=VoiceSynthesizePayload(
            audio_paths=audio_paths,
            synced_paths=synced_paths,
        ),
    )
