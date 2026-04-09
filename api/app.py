from fastapi import FastAPI

from api.routers import (
    character_router,
    compose_router,
    pipeline_router,
    script_router,
    video_router,
    voice_router,
)
from src.config import get_settings


settings = get_settings()
app = FastAPI(title=settings.project_name)
app.include_router(pipeline_router, prefix=settings.api_v1_prefix)
app.include_router(script_router, prefix=settings.api_v1_prefix)
app.include_router(character_router, prefix=settings.api_v1_prefix)
app.include_router(video_router, prefix=settings.api_v1_prefix)
app.include_router(voice_router, prefix=settings.api_v1_prefix)
app.include_router(compose_router, prefix=settings.api_v1_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": settings.project_name, "status": "ok"}
