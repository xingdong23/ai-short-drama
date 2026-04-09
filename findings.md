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
