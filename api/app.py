from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
debug_ui_dir = Path(__file__).resolve().parent / "debug_ui"

app.include_router(pipeline_router, prefix=settings.api_v1_prefix)
app.include_router(script_router, prefix=settings.api_v1_prefix)
app.include_router(character_router, prefix=settings.api_v1_prefix)
app.include_router(video_router, prefix=settings.api_v1_prefix)
app.include_router(voice_router, prefix=settings.api_v1_prefix)
app.include_router(compose_router, prefix=settings.api_v1_prefix)
app.mount("/debug/assets", StaticFiles(directory=debug_ui_dir / "assets"), name="debug_assets")


@app.get("/")
def root() -> dict[str, str]:
    return {"service": settings.project_name, "status": "ok"}


@app.get("/debug", include_in_schema=False)
def debug_console() -> FileResponse:
    return FileResponse(debug_ui_dir / "index.html")
