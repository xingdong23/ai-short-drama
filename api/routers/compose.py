from api.schemas import APIResponse, ComposeFinalPayload, ComposeFinalRequest
from fastapi import APIRouter

from src.compose.bgm import BGMMixer
from src.compose.ffmpeg_composer import FFmpegComposer
from src.compose.subtitle import SubtitleGenerator


router = APIRouter(prefix="/compose", tags=["compose"])
subtitle_generator = SubtitleGenerator()
bgm_mixer = BGMMixer()
composer = FFmpegComposer()


@router.post("/final", response_model=APIResponse[ComposeFinalPayload])
def compose_final(payload: ComposeFinalRequest) -> APIResponse[ComposeFinalPayload]:
    script = payload.script.to_domain()
    compose_dir = payload.output_dir / "compose"
    subtitle_path = subtitle_generator.generate(script, compose_dir)
    bgm_path = bgm_mixer.select_track(compose_dir)
    clips = [payload.clips_dir / f"{scene.id}.mp4" for scene in script.scenes]
    final_video_path = composer.compose(
        clips=clips,
        subtitle_path=subtitle_path,
        bgm_path=bgm_path,
        output_path=payload.output_dir / "final.mp4",
    )

    return APIResponse(
        success=True,
        data=ComposeFinalPayload(
            final_video_path=final_video_path,
            subtitle_path=subtitle_path,
            bgm_path=bgm_path,
        ),
    )
