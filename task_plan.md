# Task Plan

## Goal

Turn the current design-only repository into a runnable Phase 1 scaffold for the AI short drama project:
- Python project layout
- minimal CLI pipeline
- FastAPI service
- config loading
- placeholder engines and state management
- tests proving the scaffold runs

## Phases

| Phase | Status | Notes |
| --- | --- | --- |
| Capture current state and constraints | complete | Confirmed the repository started with only a single design document |
| Define minimum runnable behavior with tests | complete | Added model registry, pipeline, resume, and API smoke coverage |
| Implement scaffold and placeholder engines | complete | Added Python project layout, config, CLI pipeline, FastAPI app, and placeholder engines |
| Verify with tests and smoke commands | complete | pytest, ruff, mypy, compileall, CLI run, and API smoke all passed |
| Upgrade stage APIs from placeholders to executable endpoints | complete | `script`, `character`, `video`, `voice`, and `compose` now generate deterministic artifacts and return real paths |
| Add optional LLM-backed script generation with safe fallback | complete | `scriptwriter` now accepts OpenAI-compatible chat completions and falls back to placeholder scripts on failure |
| Restore GitHub Actions conda workflow prerequisites | complete | Added `environment.yml` expected by `.github/workflows/python-package-conda.yml` |
| Add manifest persistence and real pipeline status inspection | complete | Pipeline now writes `manifest.json`, exposes `inspect()`, and returns run progress via `/api/v1/pipeline/status?output_dir=...` |
| Record timestamps and failure state for pipeline runs | complete | State and manifest now capture `running/completed/failed` lifecycle, timestamps, and last error text |
| Add binary resolution chain and pipeline preflight checks | complete | Added `explicit > env > PATH` binary resolution and `/api/v1/pipeline/preflight` environment checks |
| Upgrade Wan video engine into a configurable command adapter | complete | `WanVideoEngine` now supports command-based external backends, placeholder fallback, and config-driven injection from `wan21` model spec |

## Constraints

- Existing repository contains only design documentation.
- No real model weights or cloud GPU environment are available locally.
- No new dependencies beyond the minimal Python stack already implied by the design.
- Keep the scaffold reviewable and reversible.

## Success Criteria

- `python3 -m pytest` passes.
- `python3 -m src.pipeline.engine --input "test story" --output ./output/test-run` succeeds.
- FastAPI app imports successfully and exposes the documented route family.

## Errors Encountered

| Error | Attempt | Resolution |
| --- | --- | --- |
| Missing source tree caused import failures in pytest | 1 | Added scaffolded packages and modules to satisfy test targets |
| `python -m src.pipeline.engine` emitted `runpy` warning | 1 | Removed eager import from `src/pipeline/__init__.py` |
| `ruff` flagged redundant f-string and `mypy` flagged `Path | None` handling | 1 | Simplified string literal and made reference path narrowing explicit |
| New stage API tests failed because route payloads were still placeholders | 1 | Added concrete request/response schemas and wired routes to the existing placeholder engines |
| `mypy` rejected API schema conversions around `ShotPayload` | 1 | Tightened `ShotPayload.type` to `ShotType` and replaced `**dict` construction with explicit field mapping |
| `ScriptwriterEngine` could not accept an injected LLM client in tests | 1 | Added an injectable client protocol and fallback generation path |
| Pipeline status API had no runtime inspection payload | 1 | Added `PipelineInspection`, manifest writes, and optional `run` payload on the status endpoint |
| Pipeline runs had no durable failure metadata | 1 | Expanded `PipelineState` with lifecycle fields and wrapped execution to persist failed state before re-raising |
| No shared binary resolution logic existed for FFmpeg/ffprobe or environment preflight | 1 | Added reusable binary resolver, preflight checker, config fields, and API exposure |
| `WanVideoEngine` could not execute an external backend or honor model config | 1 | Added command backend parsing from model extras, subprocess invocation, fallback handling, and pipeline/API wiring |
