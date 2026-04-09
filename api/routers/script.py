import json

from api.schemas import APIResponse, ScriptGeneratePayload, ScriptGenerateRequest, ScriptPayload
from fastapi import APIRouter

from src.scriptwriter.engine import ScriptwriterEngine


router = APIRouter(prefix="/script", tags=["script"])
engine = ScriptwriterEngine()


@router.post("/generate", response_model=APIResponse[ScriptGeneratePayload])
def generate_script(payload: ScriptGenerateRequest) -> APIResponse[ScriptGeneratePayload]:
    script = engine.generate(payload.theme)
    script_payload = ScriptPayload.from_domain(script)
    script_path = None

    if payload.output_dir is not None:
        payload.output_dir.mkdir(parents=True, exist_ok=True)
        script_path = payload.output_dir / "script.json"
        script_path.write_text(
            json.dumps(script.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return APIResponse(
        success=True,
        data=ScriptGeneratePayload(
            script=script_payload,
            script_path=script_path,
        ),
    )
