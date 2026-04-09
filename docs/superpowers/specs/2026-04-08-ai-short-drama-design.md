# AI Short Drama - Design Spec

## Context

Build a CLI + FastAPI pipeline system for generating AI short drama videos (continuous narrative, 30-60s per episode). The system uses Flux + LoRA for character consistency, Wan2.1 for video generation, CosyVoice for TTS, MuseTalk for lip sync, and FFmpeg for final composition. Target platform: cloud GPU. This is a new independent project under `/Users/chengzheng/workspace/chuangxin/ai-short-drama/`.

## Requirements

- **Video type**: Continuous short drama with fixed characters across episodes
- **Video model**: Wan2.1 (primary, img2vid mode)
- **GPU**: Cloud GPU (24-48GB VRAM)
- **Interface**: CLI pipeline + FastAPI service
- **Script source**: LLM-generated scripts with shot breakdown
- **Character consistency**: Flux + LoRA training for reference images
- **Phases**: Phase 1 (core pipeline, this week), Phase 2 (ComfyUI + VACE), Phase 3 (sound effects + consistency check)

## Architecture: Pure Python Inference Modules

Each pipeline step is an independent Python module with direct model inference (diffusers/transformers). ComfyUI integration deferred to Phase 2.

## Project Structure

```
ai-short-drama/
├── setup.sh                      # One-click environment setup
├── requirements.txt
├── .env.example
├── config/
│   ├── models.yaml               # Model registry (paths, params, VRAM)
│   ├── characters.yaml           # Character definitions (name, LoRA, voice)
│   └── pipeline.yaml             # Pipeline configuration
├── src/
│   ├── __init__.py
│   ├── config.py                 # Pydantic Settings (env vars + .env)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── registry.py           # Model registry
│   │   ├── vram_manager.py       # GPU memory management
│   │   └── base.py               # InferenceEngine protocol
│   ├── scriptwriter/
│   │   ├── __init__.py
│   │   ├── engine.py             # LLM script generation
│   │   └── storyboard.py         # Shot list parsing
│   ├── character/
│   │   ├── __init__.py
│   │   ├── flux_generator.py     # Flux + LoRA reference image generation
│   │   ├── lora_trainer.py       # LoRA training wrapper
│   │   └── consistency.py        # Character consistency check
│   ├── video/
│   │   ├── __init__.py
│   │   ├── skyreels_engine.py    # SkyReels-V2 video generation (I2V/T2V/FLF2V/V2V)
│   │   ├── wan_engine.py         # Wan2.1 video generation (img2vid, fallback)
│   │   └── shot_router.py        # Shot type routing (model selection per shot)
│   ├── voice/
│   │   ├── __init__.py
│   │   ├── cosyvoice_engine.py   # CosyVoice TTS
│   │   └── musetalk_engine.py    # MuseTalk lip sync
│   ├── compose/
│   │   ├── __init__.py
│   │   ├── ffmpeg_composer.py    # FFmpeg final composition
│   │   ├── subtitle.py           # Subtitle generation (Faster Whisper)
│   │   └── bgm.py                # BGM mixing
│   └── pipeline/
│       ├── __init__.py
│       ├── engine.py             # Main pipeline orchestrator
│       └── state.py              # Pipeline state (resume support)
├── api/
│   ├── __init__.py
│   ├── app.py                    # FastAPI entry point
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pipeline.py
│   │   ├── character.py
│   │   ├── video.py
│   │   └── voice.py
│   └── schemas.py                # Request/response models
├── scripts/
│   ├── download_models.py        # Download all required models
│   └── train_lora.py             # LoRA training CLI
├── assets/
│   ├── characters/               # Character reference images
│   ├── bgm/                      # Background music
│   ├── voices/                   # Voice samples
│   └── lora/                     # LoRA weights
├── output/                       # Generated outputs
└── tests/
    ├── __init__.py
    ├── test_pipeline.py
    ├── test_video.py
    └── test_models.py
```

## Core Interface Protocol

```python
# src/models/base.py
from typing import Protocol

class InferenceEngine(Protocol):
    def load_model(self) -> None: ...
    def unload_model(self) -> None: ...
    def infer(self, inputs: dict) -> Result: ...
    @property
    def vram_required_mb(self) -> int: ...
```

All modules (Flux, Wan2.1, CosyVoice, MuseTalk) implement this protocol. The VRAM manager uses `vram_required_mb` to decide when to load/unload models.

## Data Flow

```
User input (story theme/outline)
    |
    v
[1] scriptwriter -- LLM generates script + shot list
    |  Output: Script { scenes: [Shot{prompt, character, duration, camera, type}] }
    |
    v
[2] character -- Flux + LoRA generates reference image per shot
    |  Output: { shot_id: reference_image_path }
    |
    v
[3] video -- shot_router selects model per shot type:
    |   establishing -> SkyReels/Wan2.1 T2V
    |   dialogue/action -> SkyReels/Wan2.1 I2V (with reference image)
    |   transition -> SkyReels FLF2V (first+last frame)
    |   extension -> SkyReels V2V (video continuation)
    |  Output: { shot_id: video_clip_path }
    |
    v
[4] voice -- CosyVoice TTS per dialogue -> MuseTalk lip sync
    |  Output: { shot_id: synced_video_path }
    |
    v
[5] compose -- FFmpeg concatenation + subtitles + BGM
    |  Output: final_video.mp4
```

## Shot List Format (Core Data Structure)

```yaml
script:
  title: "Episode 1: The Meeting"
  scenes:
    - id: shot_001
      type: establishing
      prompt: "City night scene, skyscraper lights flickering"
      character: null
      dialogue: null
      duration: 3
      camera: "slow_pan"
    - id: shot_002
      type: dialogue
      prompt: "Girl reading by cafe window, breeze in her hair"
      character: "xiaomei"
      dialogue: "The coffee is really good today"
      duration: 4
      camera: "close_up"
```

Shot types:
- `establishing`: No character, no dialogue. Pure scene generation.
- `dialogue`: Character present, has dialogue. Needs reference image + TTS + lip sync.
- `action`: Character present, no dialogue. Needs reference image, no TTS.
- `transition`: Scene transition, pure video generation.

## Pipeline State (Resume Support)

```
output/run_20260408_001/
├── state.json          # { "current_step": "video", "completed": ["script", "character"] }
├── script.json         # Generated script
├── references/         # Character reference images
├── clips/              # Video clips
├── audio/              # Voiceover files
├── synced/             # Lip-synced clips
└── final.mp4           # Final output
```

`state.json` updated after each step completes. On resume, skip completed steps.

## Model Configuration

### models.yaml

```yaml
models:
  flux:
    type: image_generation
    model_id: "black-forest-labs/FLUX.1-dev"
    vram_mb: 12000
    lora_support: true

  skyreels_13b:
    type: video_generation
    model_id: "Skywork/SkyReels-V2-I2V-1.3B-540P-Diffusers"
    vram_mb: 15000
    t2v_model: "Skywork/SkyReels-V2-T2V-1.3B-540P-Diffusers"
    df_model: "Skywork/SkyReels-V2-DF-1.3B-540P-Diffusers"
    flf2v: true                # supports first-last-frame-to-video
    video_extension: true      # supports autoregressive extension
    lora_support: true
    resolution: "540P"

  skyreels_14b:
    type: video_generation
    model_id: "Skywork/SkyReels-V2-I2V-14B-720P-Diffusers"
    vram_mb: 44000
    t2v_model: "Skywork/SkyReels-V2-T2V-14B-720P-Diffusers"
    df_model: "Skywork/SkyReels-V2-DF-14B-720P-Diffusers"
    flf2v: true
    video_extension: true
    lora_support: true
    resolution: "720P"

  wan21:
    type: video_generation
    model_id: "Wan-AI/Wan2.1-I2V-14B-480P"
    vram_mb: 20000
    t2v_model: "Wan-AI/Wan2.1-T2V-14B-480P"

  cosyvoice:
    type: tts
    model_id: "FunAudioLLM/CosyVoice2-0.5B"
    vram_mb: 2000

  musetalk:
    type: lip_sync
    model_id: "musetalk-v1.5"
    vram_mb: 4000

  whisper:
    type: transcription
    model_id: "large-v3"
    vram_mb: 3000

  llm:
    type: text_generation
    vram_mb: 0           # API call, no local VRAM
    api_base: "${LLM_API_BASE}"
    api_key: "${LLM_API_KEY}"
```

### VRAM Management Strategy

Sequential loading by pipeline phase. Shot router selects model based on shot type and available VRAM:

```
Phase 1: Load Flux (~12GB) -> Generate all references -> Unload
Phase 2: Load video model (SkyReels 1.3B ~15GB / 14B ~44GB / Wan2.1 ~20GB) -> Generate all clips -> Unload
Phase 3: Load CosyVoice (~2GB) + MuseTalk (~4GB) -> Voice + lip sync -> Unload
Phase 4: CPU only (FFmpeg) -> Final composition
```

For 24GB cards: SkyReels 1.3B fits natively, 14B requires offload or multi-GPU.
For 48GB+ cards (A6000/A100): SkyReels 14B runs natively.

### Shot Router Logic

```python
# shot_router.py selects model per shot:
# - establishing shots -> T2V pipeline (any model)
# - dialogue/action with character -> I2V pipeline (Flux reference + SkyReels I2V)
# - shot transitions -> FLF2V pipeline (SkyReels DF with first+last frame)
# - scene extensions -> Video extension pipeline (SkyReels V2V)
```

### LoRA Training Config

```yaml
training:
  method: "kohya_ss"
  base_model: "FLUX.1-dev"
  rank: 16
  alpha: 16
  steps: 1000
  learning_rate: 0.0001
  dataset:
    min_images: 10
    resolution: 1024
```

## FastAPI Endpoints

```python
POST /api/v1/pipeline/run          # Run full pipeline
POST /api/v1/pipeline/resume       # Resume from checkpoint
GET  /api/v1/pipeline/status       # Query progress

POST /api/v1/script/generate       # LLM script generation
POST /api/v1/character/reference   # Generate character reference image
POST /api/v1/character/train       # Trigger LoRA training

POST /api/v1/video/generate        # Generate video clip
POST /api/v1/voice/synthesize      # TTS synthesis
POST /api/v1/compose/final         # Final composition
```

### API Response Format

```python
class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
```

## CLI Interface

```bash
# Full pipeline
python -m src.pipeline.engine --input "story theme" --output ./output/ep01

# Resume
python -m src.pipeline.engine --resume ./output/ep01

# Individual steps
python -m src.scriptwriter.engine --theme "campus romance"
python -m src.character.flux_generator --character xiaomei --lora ./assets/lora/xiaomei
python -m src.video.wan_engine --reference ./references/shot_001.png --prompt "..."
python -m src.compose.ffmpeg_composer --clips ./clips/ --subtitle ./subs.srt
```

## Reusable Patterns from video-automation-studio

These proven patterns from the existing codebase should be adopted:

1. **Lazy initialization** (`@property` with `None` guard) for all engines
2. **Frozen dataclasses** for result objects (immutable)
3. **Pydantic BaseSettings** for configuration (env vars + .env)
4. **Binary resolution chain** for FFmpeg/ffprobe (explicit path -> env var -> shutil.which())
5. **Singleton with double-check locking** for shared resources
6. **Vendored dependencies** for CosyVoice, MuseTalk (with sys.path manipulation)

## Phase 1 Implementation Order

1. **Environment setup + directory structure** -- setup.sh, requirements.txt, config files
2. **Model download script** -- scripts/download_models.py
3. **Core infrastructure** -- config.py, base.py, registry.py, vram_manager.py
4. **LoRA training** -- lora_trainer.py
5. **Character reference generation** -- flux_generator.py (Flux + LoRA)
6. **Video generation** -- wan_engine.py, shot_router.py
7. **Voice + lip sync** -- cosyvoice_engine.py, musetalk_engine.py
8. **Composition** -- ffmpeg_composer.py, subtitle.py, bgm.py
9. **Pipeline orchestrator** -- engine.py, state.py
10. **FastAPI service** -- app.py, routers, schemas
11. **Tests** -- unit tests for each module

## Verification Plan

1. **Unit tests**: Each module tested independently with mock models
2. **Integration test**: Run full pipeline with a simple 3-shot script
3. **CLI smoke test**: `python -m src.pipeline.engine --input "test story" --output ./output/test`
4. **API smoke test**: `curl -X POST /api/v1/pipeline/run` with test payload
5. **VRAM monitoring**: `nvidia-smi` before/after each phase to verify load/unload
6. **Output validation**: Verify final.mp4 has correct duration, audio, subtitles
