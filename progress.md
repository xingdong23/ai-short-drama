# Progress Log

## 2026-04-09

- Inspected repository contents and confirmed it is still at the design-document stage.
- Read the applicable workflow skills for brainstorming, file-based planning, TDD, and verification.
- Captured current state, constraints, and success criteria in planning files.
- Wrote failing tests first for registry loading, pipeline run/resume, and API status/run behavior.
- Implemented the Phase 1 scaffold: config files, project structure, placeholder engines, stateful pipeline CLI, FastAPI routes, and helper scripts.
- Ran setup, fixed a package import warning for `python -m`, and resolved lint/type issues.
- Final verification passed across pytest, ruff, mypy, compileall, CLI smoke, and API smoke.
- Added a second TDD pass for stage-level APIs and wrote failing tests for script, character, video, voice, and compose endpoints.
- Replaced placeholder stage responses with concrete request/response schemas and deterministic artifact generation.
- Verified the expanded API surface with 11 passing tests plus fresh lint and type checks.
- Added a third TDD pass for `scriptwriter`, covering valid LLM JSON, fenced JSON, and failure fallback behavior.
- Implemented a no-SDK OpenAI-compatible chat-completions client and wired `ScriptwriterEngine` to use it opportunistically.
- Added `environment.yml` to satisfy the existing conda GitHub Actions workflow.
- Added a fourth TDD pass for pipeline observability, covering manifest writing, partial-run inspection, and status endpoint enrichment.
- Implemented `PipelineInspection`, `manifest.json` persistence, and runtime status lookup by `output_dir`.
- Verified the richer status flow with 15 passing tests plus fresh lint, typecheck, compile, CLI smoke, and API smoke.
- Added a fifth TDD pass for lifecycle tracking, covering successful timestamps and failed-run state persistence.
- Expanded `PipelineState` and inspection payloads with status, theme, timestamps, and last error fields.
- Wrapped pipeline execution so failed steps now write durable state before the exception propagates.
- Added a sixth TDD pass for binary resolution and environment preflight.
- Implemented shared `explicit > env > PATH` binary lookup, wired it into the FFmpeg composer, and exposed a pipeline preflight API.
- Verified the preflight path with 21 passing tests plus fresh lint, typecheck, compile, CLI smoke, and API smoke.
- Added a seventh TDD pass for the Wan adapter layer, covering command backend execution, fallback-on-failure, and hard failure without fallback.
- Upgraded `WanVideoEngine` from a pure placeholder writer into a config-driven subprocess adapter while preserving deterministic local fallback behavior.
- Rewired pipeline and video API construction so `wan21` behavior now comes from model registry config.
