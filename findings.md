# Findings

## Repository State

- The working directory is now a git repository and tracks `origin/main`.
- The repository contains a runnable Phase 1 scaffold:
  - source tree under `src/`
  - FastAPI app under `api/`
  - config files under `config/`
  - tests under `tests/`
- There is still no `.omx/` runtime state in the repository.

## Design Constraints Pulled Forward

- Architecture target: CLI + FastAPI pipeline.
- Pipeline phases: script -> character reference -> video -> voice/lip sync -> composition.
- Resume support via `state.json`.
- Use pure Python inference modules for Phase 1, with real model integration deferred behind interfaces.

## Environment

- Python `3.13.3`
- `fastapi 0.135.1`
- `pydantic 2.12.5`
- `pydantic_settings 2.13.1`
- `PyYAML 6.0.3`
- `pytest 9.0.2`
- `uvicorn 0.41.0`

## Implementation Direction

- Build a runnable scaffold with placeholder engines that serialize deterministic artifacts.
- Make the pipeline resume-aware from day one.
- Keep interfaces shaped so real model integrations can replace placeholders later without breaking API or CLI.

## Delivered Scaffold

- Config files: `config/models.yaml`, `config/characters.yaml`, `config/pipeline.yaml`
- Runtime entrypoints:
  - CLI: `python3 -m src.pipeline.engine --input ... --output ...`
  - API: `api.app`
- Placeholder modules for script generation, reference generation, video generation, TTS, lip sync, subtitle generation, and composition
- Tests covering registry loading, pipeline run, pipeline resume, and API status/run

## Delivered Stage APIs

- `POST /api/v1/script/generate` now generates and optionally persists `script.json`
- `POST /api/v1/character/reference` now creates reference artifacts from a supplied script
- `POST /api/v1/character/train` now creates placeholder LoRA weight files
- `POST /api/v1/video/generate` now creates clip artifacts with shot routing
- `POST /api/v1/voice/synthesize` now creates audio and lip-synced clip artifacts
- `POST /api/v1/compose/final` now creates subtitle, BGM, and final composition artifacts

## Delivered Script LLM Path

- `src/scriptwriter/engine.py` now supports an injected or environment-backed LLM client.
- `src/scriptwriter/llm_client.py` implements a no-SDK OpenAI-compatible `/chat/completions` client.
- If `LLM_API_BASE`, `LLM_API_KEY`, or `LLM_API_MODEL` are missing, or if the live request/parse fails, the engine falls back to the deterministic placeholder script.

## Delivered CI Prerequisite

- Added `environment.yml` so the existing GitHub Actions conda workflow has an environment file to consume.

## Delivered Pipeline Observability

- `src/pipeline/engine.py` now exposes `inspect(output_dir)` for filesystem-backed run inspection.
- Each pipeline run now writes `manifest.json` alongside `state.json`.
- `GET /api/v1/pipeline/status` now accepts `output_dir` and returns run metadata:
  - `current_step`
  - `completed_steps`
  - `progress_percent`
  - `script_path`
  - `final_video_path`
  - `manifest_path`
  - `artifact_counts`

## Delivered Run Lifecycle Tracking

- `src/pipeline/state.py` now stores:
  - `status`
  - `started_at`
  - `updated_at`
  - `completed_at`
  - `failed_at`
  - `last_error`
  - `theme`
- The pipeline marks each step as `running` before work starts.
- On exceptions, the pipeline now persists failed state and rewrites `manifest.json` before raising the error.

## Delivered Binary Resolution And Preflight

- Added `src/utils/binaries.py` with the intended resolution chain:
  - explicit settings path
  - environment variable
  - `PATH` lookup via `shutil.which()`
- Added `AISD_FFMPEG_PATH` and `AISD_FFPROBE_PATH` support through `src/config.py`.
- `src/compose/ffmpeg_composer.py` now uses the shared binary resolver and records resolved paths in placeholder output.
- Added `src/pipeline/preflight.py` and `GET /api/v1/pipeline/preflight` to report:
  - `pipeline_config`
  - `models_config`
  - `characters_config`
  - `ffmpeg`
  - `ffprobe`
  - `placeholder_mode`

## Delivered Wan Adapter Layer

- `src/video/wan_engine.py` now accepts an optional `ModelSpec`.
- If `wan21` is configured with `backend.type=command`, the engine will:
  - render command argv from template fields
  - inject shot context via environment variables
  - execute the external backend via `subprocess.run`
  - require the backend to create the expected output file
- If command execution fails and `fallback_to_placeholder=true`, the engine writes a deterministic fallback artifact with command diagnostics.
- `src/pipeline/engine.py` and `api/routers/video.py` now construct `WanVideoEngine` from the `wan21` registry spec.
- `config/models.yaml` now makes the placeholder backend explicit for `wan21`.

## Delivered Flux Adapter Layer

- `src/character/flux_generator.py` now accepts an optional `ModelSpec`.
- If `flux` is configured with `backend.type=command`, the generator will:
  - render command argv from template fields
  - inject shot context via environment variables
  - execute the external backend via `subprocess.run`
  - require the backend to create the expected output file
- If command execution fails and `fallback_to_placeholder=true`, the generator writes a deterministic fallback reference artifact with command diagnostics.
- `src/pipeline/engine.py` and `api/routers/character.py` now construct `FluxReferenceGenerator` from the `flux` registry spec.
- `config/models.yaml` now makes the placeholder backend explicit for `flux`.

## Delivered Repo-Local Backend Wrappers

- Added [scripts/run_flux_backend.py](/Users/chengzheng/workspace/chuangxin/ai-short-drama/scripts/run_flux_backend.py) as a deterministic placeholder external backend for Flux.
- Added [scripts/run_wan_backend.py](/Users/chengzheng/workspace/chuangxin/ai-short-drama/scripts/run_wan_backend.py) as a deterministic placeholder external backend for Wan.
- Default `flux` and `wan21` registry entries now use `backend.type=command` with template-based argv:
  - `{python_executable}`
  - `{project_root}`
  - `{output_path}`
  - `{character}` for Flux
  - `{mode}` for Wan
- This means the default pipeline path now exercises the command-adapter execution model end to end while remaining local and deterministic.

## Delivered Wrapper Delegation Layer

- Added [scripts/backend_wrapper_common.py](/Users/chengzheng/workspace/chuangxin/ai-short-drama/scripts/backend_wrapper_common.py) to share wrapper-side template field rendering and delegate command execution.
- `scripts/run_flux_backend.py` now checks `AISD_FLUX_DELEGATE_CMD` before writing its deterministic placeholder output.
- `scripts/run_wan_backend.py` now checks `AISD_WAN_DELEGATE_CMD` before writing its deterministic placeholder output.
- Delegate commands are rendered with stable fields:
  - `{output_path}`
  - `{python_executable}`
  - `{project_root}`
  - Flux: `{character}`
  - Wan: `{mode}`
- The wrapper now enforces the contract that a successful delegate command must create the expected artifact path.

## Delivered Voice Adapter And Wrapper Layers

- `src/voice/cosyvoice_engine.py` now accepts an optional `ModelSpec` and supports `backend.type=command` for TTS execution.
- `src/voice/musetalk_engine.py` now accepts an optional `ModelSpec` and supports `backend.type=command` for lip-sync execution.
- Both engines now:
  - render argv from template fields
  - inject stage context through environment variables
  - require successful commands to create the expected output path
  - fall back to deterministic placeholder artifacts when configured to do so
- Added [scripts/run_cosyvoice_backend.py](/Users/chengzheng/workspace/chuangxin/ai-short-drama/scripts/run_cosyvoice_backend.py) as the default repo-local wrapper for TTS.
- Added [scripts/run_musetalk_backend.py](/Users/chengzheng/workspace/chuangxin/ai-short-drama/scripts/run_musetalk_backend.py) as the default repo-local wrapper for lip sync.
- `config/models.yaml` now routes default `cosyvoice` and `musetalk` entries through those wrapper scripts.
- `src/pipeline/engine.py` and [api/routers/voice.py](/Users/chengzheng/workspace/chuangxin/ai-short-drama/api/routers/voice.py) now construct both voice engines from the model registry, so the default pipeline path exercises the command-adapter model end to end.

## Delivered Voice Wrapper Delegation Layer

- `scripts/run_cosyvoice_backend.py` now checks `AISD_COSYVOICE_DELEGATE_CMD` before writing deterministic placeholder output.
- `scripts/run_musetalk_backend.py` now checks `AISD_MUSETALK_DELEGATE_CMD` before writing deterministic placeholder output.
- `scripts/backend_wrapper_common.py` now exposes stable voice-oriented template fields in addition to the visual ones:
  - `{shot_id}`
  - `{dialogue}`
  - `{character}`
  - `{source_clip_path}`
  - `{audio_path}`
- This keeps the wrapper contract uniform across `Flux`, `Wan`, `CosyVoice`, and `MuseTalk`.

## Verification Evidence

- `pytest -q` -> `5 passed`
- `python3 -m ruff check .` -> `All checks passed!`
- `python3 -m mypy src api scripts tests` -> `Success: no issues found in 43 source files`
- `python3 -m compileall src api scripts tests` -> success
- `python3 -m src.pipeline.engine --input 'test story' --output ./output/test-run-4` -> `output/test-run-4/final.mp4`
- FastAPI smoke:
  - `POST /api/v1/pipeline/run` -> `200`
  - `GET /api/v1/pipeline/status` -> `200`

## Additional Verification Evidence

- `pytest -q tests/test_stage_api.py` -> `6 passed`
- `pytest -q` -> `11 passed`
- `python3 -m mypy src api scripts tests` -> `Success: no issues found in 44 source files`

## Latest Verification Evidence

- `pytest -q tests/test_scriptwriter.py` -> `3 passed`
- `pytest -q` -> `14 passed`
- `python3 -m ruff check .` -> `All checks passed!`
- `python3 -m mypy src api scripts tests` -> `Success: no issues found in 46 source files`
- `python3 -m src.pipeline.engine --input 'llm fallback smoke' --output ./output/llm-fallback-run` -> `output/llm-fallback-run/final.mp4`
- `python3` YAML parse check for `environment.yml` -> loaded successfully with `flake8` present

## Observability Verification Evidence

- `pytest -q tests/test_pipeline.py tests/test_api.py` -> `5 passed`
- `pytest -q` -> `15 passed`
- `python3 -m ruff check .` -> `All checks passed!`
- `python3 -m mypy src api scripts tests` -> `Success: no issues found in 46 source files`
- `python3 -m src.pipeline.engine --input 'status manifest smoke' --output ./output/status-manifest-run` -> `output/status-manifest-run/final.mp4`
- FastAPI TestClient smoke for `/api/v1/pipeline/status?output_dir=...` -> `200`, `manifest_path` exists, `progress_percent` is `100`

## Lifecycle Verification Evidence

- `pytest -q tests/test_pipeline.py tests/test_api.py` -> `6 passed`
- `pytest -q` -> `16 passed`
- `python3 -m ruff check .` -> `All checks passed!`
- `python3 -m mypy src api scripts tests` -> `Success: no issues found in 46 source files`
- `python3 -m src.pipeline.engine --input 'failure-state smoke' --output ./output/failure-state-run` -> `output/failure-state-run/final.mp4`
- FastAPI TestClient smoke for `/api/v1/pipeline/status?output_dir=...` -> `200`, `status=completed`, timestamps present, `manifest_path` exists

## Preflight Verification Evidence

- `pytest -q tests/test_binaries.py tests/test_api.py::test_pipeline_preflight_endpoint_returns_check_summary` -> `5 passed`
- `pytest -q` -> `21 passed`
- `python3 -m ruff check .` -> `All checks passed!`
- `python3 -m mypy src api scripts tests` -> `Success: no issues found in 50 source files`
- `python3 -m src.pipeline.engine --input 'preflight smoke' --output ./output/preflight-run` -> `output/preflight-run/final.mp4`
- FastAPI TestClient smoke for `/api/v1/pipeline/preflight` -> `200`, `placeholder_mode=True`, expected check keys present

## Wan Adapter Verification Evidence

- `pytest -q tests/test_video_engine.py` -> `3 passed`
- `pytest -q` -> `24 passed`
- `python3 -m ruff check .` -> `All checks passed!`
- `python3 -m mypy src api scripts tests` -> `Success: no issues found in 51 source files`
- `python3 -m src.pipeline.engine --input 'wan adapter smoke' --output ./output/wan-adapter-run` -> `output/wan-adapter-run/final.mp4`
- FastAPI TestClient smoke for `/api/v1/video/generate` -> `200`, generated clip contains `backend=placeholder` under default config

## Flux Adapter Verification Evidence

- `pytest -q tests/test_flux_generator.py` -> `3 passed`
- `pytest -q` -> `27 passed`
- `python3 -m ruff check .` -> `All checks passed!`
- `python3 -m mypy src api scripts tests` -> `Success: no issues found in 52 source files`
- `python3 -m src.pipeline.engine --input 'flux adapter smoke' --output ./output/flux-adapter-run` -> `output/flux-adapter-run/final.mp4`
- FastAPI TestClient smoke for `/api/v1/character/reference` -> `200`, generated reference contains `generator=flux-placeholder` under default config

## Default Wrapper Verification Evidence

- `pytest -q tests/test_backend_scripts.py tests/test_stage_api.py::test_character_reference_endpoint_generates_reference_files tests/test_stage_api.py::test_video_generate_endpoint_creates_clip_files tests/test_pipeline.py::test_pipeline_run_creates_expected_artifacts` -> `5 passed`
- `pytest -q` -> `29 passed`
- `python3 -m ruff check .` -> `All checks passed!`
- `python3 -m mypy src api scripts tests` -> `Success: no issues found in 55 source files`
- `python3 -m src.pipeline.engine --input 'wrapper default smoke' --output ./output/wrapper-default-run` -> `output/wrapper-default-run/final.mp4`
- FastAPI TestClient smoke:
  - `/api/v1/video/generate` -> `200`, clip contains `backend=wan-wrapper-placeholder`
  - `/api/v1/character/reference` -> `200`, reference contains `generator=flux-wrapper-placeholder`

## Wrapper Delegation Verification Evidence

- `pytest -q tests/test_backend_scripts.py` -> `4 passed`
- `pytest -q` -> `31 passed`
- `python3 -m ruff check .` -> `All checks passed!`
- `python3 -m mypy src api scripts tests` -> `Success: no issues found in 56 source files`
- `python3 -m compileall src api scripts tests` -> success
- `python3 -m src.pipeline.engine --input 'wrapper delegate smoke' --output ./output/wrapper-delegate-run` -> `output/wrapper-delegate-run/final.mp4`

## Voice Adapter Verification Evidence

- `pytest -q tests/test_voice_engines.py tests/test_backend_scripts.py tests/test_stage_api.py::test_voice_synthesize_endpoint_creates_audio_and_synced_files` -> `11 passed`
- `pytest -q` -> `37 passed`
- `python3 -m ruff check .` -> `All checks passed!`
- `python3 -m mypy src api scripts tests` -> `Success: no issues found in 59 source files`
- `python3 -m compileall src api scripts tests` -> success
- `python3 -m src.pipeline.engine --input 'voice adapter smoke' --output ./output/voice-adapter-run` -> `output/voice-adapter-run/final.mp4`

## Voice Wrapper Delegation Verification Evidence

- `pytest -q tests/test_backend_scripts.py` -> `8 passed`
- `pytest -q` -> `39 passed`
- `python3 -m ruff check .` -> `All checks passed!`
- `python3 -m mypy src api scripts tests` -> `Success: no issues found in 59 source files`
- `python3 -m compileall src api scripts tests` -> success
- `python3 -m src.pipeline.engine --input 'voice wrapper delegate smoke' --output ./output/voice-wrapper-delegate-run` -> `output/voice-wrapper-delegate-run/final.mp4`
