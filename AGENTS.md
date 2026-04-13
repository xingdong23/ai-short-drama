# AI Short Drama Agent Guide

本文件作用域覆盖整个 `ai-short-drama/` 目录树。

## Mission

`ai-short-drama/` 是一个独立的 AI 短剧生成项目，不属于 `opentalker/`。
它看起来是一条以 Python 为中心的生成链路，覆盖：

- 角色资产与配置
- 剧本生成
- 配音与语音后端
- 视频生成/组合
- API 层与调试 UI

如果任务属于 `opentalker/` 或 `product-image-prototype/`，请回到工作区根目录重新路由。

## Repository Boundary

这个目录当前保留自己的独立 `.git`。
把它搬进工作区，只是为了统一目录组织，不代表它已经并入外层仓库。

理解方式：

- 工作区根目录负责多项目路由
- `ai-short-drama/` 仍然是自己的项目根

## Read Order

1. `AGENTS.md`
2. `requirements.txt` 或 `environment.yml`
3. `api/app.py`
4. `src/pipeline/engine.py`
5. 根据任务进入对应子模块

## Top-Level Modules

- `api/`
  - API 入口、路由、schema、workspace 管理、debug UI
- `src/`
  - 核心业务实现
  - `character/`
  - `scriptwriter/`
  - `voice/`
  - `video/`
  - `compose/`
  - `pipeline/`
- `scripts/`
  - 模型下载、后端 wrapper、训练与运行脚本
- `config/`
  - `characters.yaml`
  - `models.yaml`
  - `pipeline.yaml`
- `assets/`
  - 角色、BGM、LoRA、声音资产
- `tests/`
  - API、pipeline、voice、video、scriptwriter 等测试
- `docs/`
  - 设计与计划文档
- `output/`
  - 运行产物，不当作源码

## Routing Hints

- API 问题：
  - 先看 `api/app.py`、`api/routers/`、`api/schemas.py`
- 工作流编排问题：
  - 先看 `src/pipeline/engine.py`、`src/pipeline/tasks.py`、`src/pipeline/state.py`
- 角色/剧本/配音/视频能力问题：
  - 进入 `src/character`、`src/scriptwriter`、`src/voice`、`src/video`
- 外部后端包装或模型脚本：
  - 看 `scripts/run_*_backend.py` 与 `scripts/download_models.py`

## Local Development

当前可见的环境入口有两套：

- `requirements.txt`
- `environment.yml`

常见脚本入口：

```bash
cd ai-short-drama
python -m api.app
pytest
```

如果项目内部已有更具体的启动方式，以该目录后续补充的 README / scripts 为准。

## Testing

测试主要位于：

- `tests/test_api.py`
- `tests/test_pipeline.py`
- `tests/test_scriptwriter.py`
- `tests/test_voice_engines.py`
- `tests/test_video_engine.py`
- `tests/test_stage_api.py`

修改某个能力模块时，优先跑最近的测试，不要默认全量跑所有重型链路。

## Editing Notes

- `output/`、缓存目录、临时运行结果不要当作源码修改
- `assets/` 更偏运行资源与素材，不要随意把它们改成代码目录
- 这个项目和 `opentalker/` 是并列关系，不要在两边混用路径和部署假设
