from api.schemas import APIResponse, ScriptGeneratePayload, ScriptGenerateRequest, ScriptPayload
from fastapi import APIRouter

from src.pipeline.engine import PipelineEngine


router = APIRouter(prefix="/script", tags=["script"])
engine = PipelineEngine()


@router.post("/generate", response_model=APIResponse[ScriptGeneratePayload])
def generate_script(payload: ScriptGenerateRequest) -> APIResponse[ScriptGeneratePayload]:
    workspace, script = engine.generate_script_task(payload.task_id, payload.theme)
    script_payload = ScriptPayload.from_domain(script)

    return APIResponse(
        success=True,
        data=ScriptGeneratePayload(
            task_id=workspace.task_id,
            script=script_payload,
            script_path=workspace.script_path,
        ),
    )
