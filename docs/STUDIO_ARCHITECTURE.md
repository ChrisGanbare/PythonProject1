# Studio 控制面架构（产品与技术说明）

本仓库除「各子项目渲染管线」外，增加一层 **Studio 控制面**：承载 **自然语言意图迭代**、**标准任务模板**、**异步渲染作业** 的持久化与 API。目标是可单机交付、也可横向扩展。

---

## 1. 边界划分

| 层级 | 职责 | 典型实现 |
|------|------|----------|
| **子项目** | 具体视频算法、Manim/matplotlib、成片落盘 | `projects/<name>/` + `entrypoints` |
| **编排** | 发现 manifest、解析参数、同步调用入口 | `orchestrator/` |
| **控制面（Studio）** | 作业与意图会话的持久化、Agent 契约、HTTP/CLI | `shared/studio/`、`shared/agent/` |
| **控制台 UI** | 人机操作、轮询作业 | `static/` + `dashboard.py` |

渲染计算仍在 **子进程/后台线程** 中执行；控制面只负责 **记录状态** 与 **触发** `run_project_task`。

---

## 2. 数据存储

### 2.1 默认：SQLite

- 默认路径：`runtime/studio.db`（目录随 `get_database_url()` 创建）。
- ORM：**SQLAlchemy 2.x**，启动时 `Base.metadata.create_all()`（开发友好）。
- **作业重启可恢复历史**：任务状态、日志、结果 JSON 均在库中，不再使用进程内字典。

### 2.2 生产：PostgreSQL（推荐）

设置环境变量 **`STUDIO__DATABASE_URL`**（或 `STUDIO_DATABASE_URL`），例如：

```text
postgresql+psycopg://user:pass@host:5432/videostudio
```

需安装对应驱动（如 `psycopg[binary]`）。表结构与 SQLite 一致；**建议**引入 **Alembic** 管理迁移（当前仓库以 `create_all` 为起点，迁移脚本可按团队流程补全）。

### 2.3 为何不默认上 Redis / Celery？

- **单机创作者场景**：SQLite + FastAPI `BackgroundTasks` 足够，部署简单。
- **多机队列**：可将「执行」从 BackgroundTasks 换成 **Celery + Redis/RabbitMQ**，**不改** `RenderJob` 表语义：Worker 只消费 `job_id` 并调用同一套 `run_render_job_task`。
- 产品演进顺序：**先持久化与 API 契约 → 再按需加队列**。

---

## 3. 核心表（概念）

- **`render_jobs`**：异步渲染任务（状态、kwargs、结果、日志、`intent_summary`、可选 `template_snapshot_json`、可选 `session_id`）。
- **`intent_sessions` / `intent_turns`**：自然语言多轮与编译结果链（与 Agent `compile` 的 `session_id` + `persist_turns` 联动）。

---

## 4. API 版本

- **规范路径**：`/api/v1/*`（健康检查、作业列表、意图会话、Agent 编译/校验）。
- **兼容路径**：现有 `/api/jobs/*`、`/api/run/*`、`/api/agent/*` 仍保留，与控制台前端及旧脚本兼容。

详见 [AGENT.md](AGENT.md) 中的 HTTP 说明。

---

## 5. 安全与多租户（后续）

当前默认 **本机单用户**（127.0.0.1）。若暴露公网，需补充：

- API Key 或 OAuth2；
- 按租户隔离 `session` / `job`；
- 对象存储（结果视频）与数据库分离。

---

## 6. 与「仅修修补补」的区别

- **持久化是第一性原理**：作业与意图链可审计、可恢复，而不是内存字典。
- **版本化 API**：`/api/v1` 明确演进边界。
- **存储可替换**：通过 `STUDIO__DATABASE_URL` 切换 PostgreSQL，无需改业务代码路径。
