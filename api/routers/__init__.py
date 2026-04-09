from api.routers.character import router as character_router
from api.routers.compose import router as compose_router
from api.routers.pipeline import router as pipeline_router
from api.routers.script import router as script_router
from api.routers.video import router as video_router
from api.routers.voice import router as voice_router

__all__ = [
    "character_router",
    "compose_router",
    "pipeline_router",
    "script_router",
    "video_router",
    "voice_router",
]
