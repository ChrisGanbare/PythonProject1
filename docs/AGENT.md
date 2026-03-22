# Agent 集成指南（自然语言 → 标准模板 → 渲染）

本仓库为 **Claude Code、Cursor Agent、自建 LLM** 等提供一层**稳定契约**，把自然语言需求编译为 `StandardVideoJobRequest` JSON，再交给现有调度器（`orchestrator.runner.run_project_task`）执行。

**控制面整体说明（数据库、作业持久化、演进路线）见 [STUDIO_ARCHITECTURE.md](STUDIO_ARCHITECTURE.md)。**

## 核心概念

| 概念 | 说明 |
|------|------|
| **Catalog** | 当前仓库内所有子项目、任务、manifest 参数提示的机器可读目录 |
| **StandardVideoJobRequest** | 版本化统一模板（`schema_version: "1.0"`），字段：`project`、`task`、`kwargs`、可选 `intent_summary` / `revision_notes` |
| **Compile** | 使用已配置的 **OpenAI 兼容 API** 将自然语言（及可选「上一版模板」）编译为标准模板 |
| **Validate** | 不调用模型，仅校验 `project`/`task` 是否存在、`kwargs` 是否可执行 |
| **Intent Session** | 多轮自然语言与编译结果写入数据库（`session_id` + `persist_turns`），便于追溯与修改需求 |

## 环境变量

### 编译（OpenAI 兼容）

- `API__OPENAI_COMPATIBLE_API_KEY`
- `API__OPENAI_COMPATIBLE_BASE_URL`（如 `https://api.openai.com/v1` 或其它兼容网关）
- `API__OPENAI_COMPATIBLE_MODEL`（可选，默认见 `shared/config/settings.py`）

未配置时，`compile` 会返回明确错误；仍可使用「手工 JSON → validate → run」。

### 控制面数据库

- 默认：`runtime/studio.db`（SQLite）
- 覆盖：设置 **`STUDIO__DATABASE_URL`**（或 `STUDIO_DATABASE_URL`），例如 PostgreSQL 连接串（生产推荐，见架构文档）

## HTTP — 规范路径 `/api/v1`（推荐）

假设控制台监听 `http://127.0.0.1:8090`：

| 方法 | 路径 | 作用 |
|------|------|------|
| GET | `/api/v1/health` | 控制面就绪 |
| GET | `/api/v1/jobs` | 分页列出历史作业（持久化） |
| GET | `/api/v1/jobs/{id}` | 作业状态与结果 |
| POST | `/api/v1/jobs` | Body: `{"template": StandardVideoJobRequest, "session_id": null}` 提交异步渲染 |
| GET | `/api/v1/sessions` | 意图会话列表 |
| POST | `/api/v1/sessions` | 创建会话，返回 `session_id` |
| GET | `/api/v1/sessions/{id}` | 会话详情（含 turns） |
| GET | `/api/v1/agent/catalog` | 同下 |
| GET | `/api/v1/agent/schema` | JSON Schema |
| POST | `/api/v1/agent/compile` | 自然语言编译；可选 `session_id`、`persist_turns` |
| POST | `/api/v1/agent/validate` | 校验标准模板 |

## HTTP — 兼容路径（与旧前端/脚本一致）

| 方法 | 路径 | 作用 |
|------|------|------|
| GET | `/api/agent/catalog` | 拉取目录（含 manifest `parameters`） |
| GET | `/api/agent/schema` | `StandardVideoJobRequest` 的 JSON Schema |
| POST | `/api/agent/compile` | Body 支持 `session_id`、`persist_turns` |
| POST | `/api/agent/validate` | 校验 |
| POST | `/api/agent/run` | 异步渲染，返回 `job_id` |
| GET | `/api/jobs/{id}` | 查询作业（**数据来自数据库**，非内存） |

**修改需求**：再次调用 `compile`，在 `previous` 中传入上一轮 `standard_request`，并在 `prompt` 中写修改说明；若使用会话，传入同一 `session_id` 以便库中形成 turn 链。

## CLI

```bash
pip install -e .
video-agent catalog > catalog.json
video-agent schema > standard_job.schema.json
video-agent compile 用贷款对比项目生成抖音竖屏30秒预览视频 -o job.json
video-agent validate job.json
video-agent run job.json
```

`compile` 需网络与 API Key；`run` 为**前台同步**执行，等同 `scheduler.py run`。

## 与「仅 Claude 写 JSON」的配合

1. `GET /api/v1/agent/catalog` + `GET /api/v1/agent/schema`；
2. 由模型直接产出符合 Schema 的 JSON；
3. `POST /api/v1/agent/validate` → `POST /api/v1/jobs`。

## 扩展子项目

新建或修改 `projects/<name>/project_manifest.py` 后，**catalog 与 registry 会自动发现**；Agent 提示词无需硬编码项目列表。
