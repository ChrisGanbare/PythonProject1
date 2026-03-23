# video_project

数据可视化视频创作工作区，根目录作为总调度层，统一管理多个子项目。

## 文档入口（请先读）

| 文档 | 用途 |
|------|------|
| **本 README** | **唯一用户入口**：安装、调度器、子项目任务与 HTTP API、Web 控制台、脚手架、配置与测试 |
| [`docs/PRODUCT_STRATEGY.md`](docs/PRODUCT_STRATEGY.md) | 产品战略：与通用「视频大模型」的差异、护城河、设计原则（**方案与优先级以本文为准**） |
| [`docs/DATA_VIZ_VIDEO_ARCHITECTURE.md`](docs/DATA_VIZ_VIDEO_ARCHITECTURE.md) | 工程分层、数据可视化管线、分阶段落地与扩展点 |
| [`docs/AGENT.md`](docs/AGENT.md) | Agent 集成：自然语言 → 标准模板 → 渲染的 HTTP API 与 CLI 说明 |
| [`docs/STUDIO_ARCHITECTURE.md`](docs/STUDIO_ARCHITECTURE.md) | 控制面数据库（SQLite/PostgreSQL）、作业持久化与 API 版本策略 |
| [`docs/CORE_VIDEO_PIPELINE.md`](docs/CORE_VIDEO_PIPELINE.md) | 从剧本到成片全流程白话说明（非技术角色推荐） |
| [`docs/UAT_BROWSER_AND_AGENT.md`](docs/UAT_BROWSER_AND_AGENT.md) | 真实 Agent 编译接口与浏览器 UAT 命令速查 |
| [`CLAUDE.md`](CLAUDE.md) | 面向 AI/IDE 助手的工作区约定（非必读） |

## 架构概览

- `shared/`：公共库，所有子项目均可导入（配置、平台规格、工具函数等）
- `projects/`：各作品子项目，互相独立，可相互借鉴
- `assets/`：共享静态资源（字体、音乐、模板）
- 扩展方式：新增子项目时，在 `projects/` 下添加目录并创建 `project_manifest.py`
- **子项目角色**：仓库里已有的子项目（如 `loan_comparison`、`fund_fee_erosion`、`video_platform_introduction`）是**随代码附带的参考实现**，用来演示端到端链路；**新建项目与此地位相同**，都走同一套约定，**不存在**「只有示例项目才适用某条规则、其他项目走另一套」的并行特例。
- 数据可视化主航道与分阶段说明：见 [`docs/DATA_VIZ_VIDEO_ARCHITECTURE.md`](docs/DATA_VIZ_VIDEO_ARCHITECTURE.md)
- 产品与护城河：见 [`docs/PRODUCT_STRATEGY.md`](docs/PRODUCT_STRATEGY.md)

### 统一业务流程（所有子项目共用）

下列环节对**任意** `projects/<name>/` 一致适用；实现深浅（是否接 AI 剧本、图表复杂度）可以不同，**发现方式、调度入口、控制台契约**相同。

| 环节 | 约定 |
|------|------|
| **注册与发现** | 子项目根目录放置 `project_manifest.py`，导出 `PROJECT_MANIFEST`（至少含 `name`、`tasks`、`default_task`）。根调度器通过 `orchestrator` 扫描 `projects/*/project_manifest.py` 自动发现。 |
| **能力与开关** | 可选 `capabilities`（如 `screenplay_workflow`、`viz_backends`）声明本项目**已实现**的能力；`/api/registry` 与控制台读取这些字段，**不**按项目名写死分支。 |
| **任务入口** | 在 `entrypoints.py` 暴露可调用函数，供 `scheduler.py run` 与 `POST /api/run/{project}/{task}` 使用；参数由函数签名与 Docstring 驱动表单（见下文「控制台参数表单约定」）。 |
| **HTTP 服务（可选）** | 子项目可有独立 `api/main.py`。若需控制台「AI 剧本 / 预览 / 编辑」代理，须在 manifest 声明 `screenplay_workflow: true` 并在子项目 API 中实现与 [`dashboard.py`](dashboard.py) 约定一致的 screenplay 端点（见 `/api/screenplay/{project}/...`）。未声明则控制台不展示该剧能力——这是**能力声明**差异，不是业务流程分叉。 |
| **成片与产物** | 默认输出落在 `runtime/outputs/<project>/`（各项目可在 entrypoint 内细化子路径）；共享配置、平台规格、素材库见 `shared/`、`assets/`。 |

## 目录结构

```text
video_project/
├─ CLAUDE.md                      # AI 助手指令与工作区约定
├─ Dockerfile
├─ pyproject.toml
├─ requirements.txt
├─ scheduler.py                   # 根调度 CLI 入口
├─ dashboard.py                   # Web 控制台 FastAPI（默认 127.0.0.1:8090）
├─ run_dashboard.bat              # Windows 启动控制台
├─ run_dashboard.sh               # macOS / Linux 启动控制台（需 chmod +x）
├─ static/                        # 控制台前端（index.html 等）
│  └─ vendor/                     # 内置 Vue / Bootstrap JS，避免依赖外网 CDN 刷新失败
├─ .env.example                   # 环境变量模板（复制为 .env 后生效）
├─ .gitignore
│
├─ shared/                        # 公共库（所有子项目可导入）
│  ├─ config/settings.py          # 全局配置（VideoConfig / APIConfig / LogConfig）
│  ├─ platform/                   # 平台规格（B站横/竖屏·抖音·小红书）与视频请求结构
│  ├─ core/                       # 公共异常层级 + 任务生命周期管理
│  ├─ agent/                      # 自然语言编译、Catalog 构建、StandardVideoJobRequest
│  ├─ code_studio/                # 代码补丁编译（LLM → patch）与会话持久化
│  ├─ content/                    # 剧本·内容规划·字幕·主题·排版·安全区令牌
│  ├─ studio/                     # 渲染作业数据库（SQLite/PostgreSQL）与意图会话服务层
│  ├─ media/video_editor.py       # FFmpeg 封装：成片合成、SRT/ASS 字幕烧录、封面生成
│  ├─ visualization/              # 可视化后端协议、PNG 帧缓存（断点续帧）、后端注册表
│  ├─ library/                    # 资产注册表（字体 / 音乐 / 模板）
│  └─ utils/                      # decorators（retry）/ logger / validators
│
├─ assets/                        # 共享静态资源（字体、音乐、模板）
│
├─ projects/
│  ├─ loan_comparison/            # 参考实现：贷款对比可视化（matplotlib）
│  │  ├─ project_manifest.py
│  │  ├─ entrypoints.py
│  │  ├─ models/                  # loan.py · schemas.py · validators.py
│  │  ├─ renderer/                # animation.py · impl.py · viz_bridge.py · viz_presets.py
│  │  ├─ api/main.py              # FastAPI 服务（默认端口 8000）
│  │  └─ tests/
│  │
│  ├─ fund_fee_erosion/           # 参考实现：基金手续费复利侵蚀可视化（matplotlib）
│  │  ├─ project_manifest.py
│  │  ├─ entrypoints.py
│  │  ├─ models/                  # calculator.py · schemas.py
│  │  ├─ renderer/                # animation.py · impl.py
│  │  ├─ api/main.py              # FastAPI 服务（默认端口 8001）
│  │  └─ tests/
│  │
│  └─ video_platform_introduction/ # 参考实现：平台介绍展示视频（Manim + screenplay_workflow）
│     ├─ project_manifest.py
│     ├─ entrypoints.py
│     ├─ renderer/                # Manim 渲染实现
│     └─ tests/
│
├─ orchestrator/                  # 项目发现与任务执行核心
│  ├─ registry.py                 # 扫描 projects/*/project_manifest.py 自动发现
│  ├─ runner.py                   # 任务执行器（同步/异步自适应，参数类型强制）
│  ├─ inspector.py                # 任务函数参数反射（驱动控制台动态表单）
│  ├─ scaffold.py                 # 交互式脚手架：生成新项目骨架
│  └─ agent_cli.py                # 自然语言 → 标准任务 CLI 链路（`video-agent` 命令）
│
├─ tests/                         # 根级测试（`pytest` 收集）
└─ runtime/                       # 运行时输出，gitignore
   ├─ outputs/
   ├─ logs/
   ├─ cache/
   └─ temp/
```

## 快速开始

```bash
# 1. （推荐）创建并激活虚拟环境，再安装依赖
python -m venv .venv
# Windows CMD:  .venv\Scripts\activate.bat
# Windows PS:  .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
# 或以可编辑模式安装（支持直接 import shared / loan_comparison / fund_fee_erosion + video-scheduler / video-dashboard）
pip install -e .

# 若仅需控制台与调度（缩短安装时间），可改用：
# pip install -r requirements-console.txt && pip install -e .

# 2. 配置环境变量（可选，默认值已可用）
cp .env.example .env

# 3. 验证安装
python scheduler.py run --project loan_comparison --task smoke_check
python scheduler.py run --project fund_fee_erosion --task smoke_check
```

**重要**：出现 `ModuleNotFoundError: No module named 'uvicorn'` / `pydantic` 等，说明**当前解释器未安装依赖**——请在**已激活的虚拟环境**里执行上面的 `pip install -r requirements.txt`（不要只创建 `.venv` 而不装包）。

若 `pip install` 报 **`WinError 32` 文件被占用**：关闭其他占用该环境的终端、Python 进程或 IDE 中对 `.venv` 的索引/调试，重试；仍失败可删除 `.venv` 后重新 `python -m venv .venv` 再安装。

### 系统要求

| 项目 | 说明 |
|------|------|
| Python | **3.10+** 推荐（与 `pyproject.toml` 一致，最低 3.9） |
| FFmpeg | **必须**（`loan_animation` / `fund_animation` 成片与编码）。未安装时请先安装并确保命令行可执行 `ffmpeg -version` |
| 可选 | OpenAI 兼容 Key（仅在使用 AI 剧本、控制台校验 API 时需要，见 `.env.example`） |

### 开箱即用（推荐路径）

1. **安装可编辑包（推荐，便于使用全局命令）**  
   ```bash
   pip install -e .
   ```  
   之后可在任意目录使用：`video-scheduler`、`video-dashboard`（若未安装 `-e .`，请在仓库根目录用 `python scheduler.py` / `python dashboard.py`）。

2. **启动 Web 控制台（图形化选项目与任务）**  
   - **Windows**：双击或执行 `.\run_dashboard.bat`  
   - **macOS / Linux**：`chmod +x run_dashboard.sh && ./run_dashboard.sh`  
   - **或直接**：`video-dashboard` 或 `python dashboard.py`（均在仓库根目录时最稳妥）  
   浏览器打开 **http://127.0.0.1:8090**（可用环境变量 `DASHBOARD_HOST` / `DASHBOARD_PORT` 修改监听地址）。`run_dashboard.bat` / `run_dashboard.sh` 会设置 `DASHBOARD_OPEN_BROWSER=1`，在**控制台进程完成启动后再**打开浏览器，避免先开页后起服务的竞态。

3. **（可选）本地快速出一条预览成片**（依赖 FFmpeg，时长越短越快）：  
   ```bash
   python scheduler.py run --project loan_comparison --task loan_animation ^
     --param platform=douyin --param quality=preview --param duration=10 --param output_file=runtime/outputs/demo_loan.mp4
   ```  
   （PowerShell 下将 `^` 换为 `` ` `` 或写成一行。）成片默认在 `runtime/outputs/`。

4. **（可选）Docker 仅跑控制台**  
   ```bash
   docker build -t video-project .
   # 将宿主机的 runtime 挂进容器，便于落盘成片与缓存
   docker run --rm -p 8090:8090 -v "$(pwd)/runtime:/app/runtime" video-project
   ```  
   Windows（PowerShell）可将卷参数写成 `-v "${PWD}/runtime:/app/runtime"`。浏览器访问 `http://localhost:8090`。镜像内已含 FFmpeg。

### 常见问题

- **`ModuleNotFoundError: uvicorn` / `pydantic` 等**：在激活的 venv 中执行 `pip install -r requirements.txt`；或先装 [`requirements-console.txt`](requirements-console.txt) 再试 `python dashboard.py`。  
- **刷新页面后出现整页 `{{ }}`、任务名未翻译**：多为外网 CDN 加载 Vue 失败。仓库已在 `static/vendor/` 内置 Vue / Bootstrap JS，请更新代码后 **Ctrl+F5 硬刷新**；并确认用 `http://127.0.0.1:8090` 访问控制台而非直接打开本地 html 文件。  
- **`WinError 32` / 无法写入 `.venv\Lib\site-packages`**：多为文件被占用——关掉其他终端、Python、占用该环境的 IDE 任务后重试；必要时删掉 `.venv` 重建。  
- **`ffmpeg` 未找到**：安装 FFmpeg 并加入 PATH 后重开终端。  
- **端口已被占用 / `WinError 10048` / `EADDRINUSE`**：表示**当前已有进程**在监听该端口（默认 8090），不是「上次关机未释放」——**重启后**旧进程已消失，若仍报占用，多为本机**另一实例**（重复运行 `dashboard`）、Docker/其他软件占用，或开机自启程序占用了同端口。可结束占用进程，或设置环境变量 `DASHBOARD_PORT` 换端口后再启动。  
- **`ModuleNotFoundError: orchestrator` / 子项目**：请在**仓库根目录**执行命令，或先 `pip install -e .`。  
- **仅做数据与逻辑验证、不渲染视频**：继续使用 `smoke_check` 即可，无需 FFmpeg。

## Web 控制台（可选）

根目录提供轻量控制台（`dashboard.py` + `static/index.html`），便于非 CLI 用户浏览子项目、填参并触发调度任务。任务在后台执行，前端用返回的 **`job_id`** 轮询状态直至成功或失败。

**怎样算「从剧本到成片」跑通了？** 用大白话写在 [docs/CORE_VIDEO_PIPELINE.md](docs/CORE_VIDEO_PIPELINE.md)：先有一份结构化「剧本」，再点运行，最后磁盘上能打开**真正的 `.mp4`**。日常用**网页操作**即可；开发者若要自动跑「真出一段测试视频」，需本机已装 **FFmpeg**，并在 PowerShell 里设 `VIDEO_PIPELINE_E2E=1` 后再跑 `pytest tests/test_video_pipeline_e2e_render.py -m video_e2e`（约一两分钟，详见该文档）。

```powershell
# Windows：双击或终端执行
.\run_dashboard.bat
# 或：python dashboard.py
```

启动后默认访问 `http://127.0.0.1:8090`。

**交互闭环（Web UI）**：主界面顶部展示 **业务流程** 步骤（配置 → 执行 → 验收）；任务结束后在 **任务结果验收** 卡片中汇总可复制的**产出路径**（或纯数据 JSON），失败时展示错误与 Job 日志节选并支持 **使用当前参数重试**。长驻型 **「启动 API」** 任务在 Web 内**禁止**点击运行（避免阻塞后台线程），页面会给出 `scheduler.py` 终端命令以完成闭环。

**侧栏分区**：侧栏最上为 **全局设置**（与工作区绑定）；其下在 **「项目与任务」** 与 **「意图会话」** 之间切换（选择会写入 **localStorage**：`video_dashboard_sidebar_tab`）。**项目与任务** 内提供 **新建项目**（磁盘脚手架）、**刷新项目列表**（`GET /api/registry`）及任务分组；**意图会话** 内为 **新建会话** / 刷新会话列表（`/api/v1/sessions`）。**闭环流程与 FAQ** 在顶栏 **「使用说明」** 模态框。进入 **意图会话** 分区时才会拉取会话列表，避免默认停在「项目与任务」时误报会话接口错误。

**侧栏项目列表（项目多时）**：提供 **搜索**（匹配项目 ID、展示名、描述）、**排序**（项目 ID 正/倒序、按显示名、自建可删项目优先），并显示「共 N 个 / 显示 M 个」；列表区域 **单独纵向滚动**；排序方式会写入浏览器 **localStorage**（`video_dashboard_project_sort`）。筛选导致当前选中项目不可见时，会提示 **清空搜索**。

**意图会话与编译历史**：在侧栏 **「意图会话」** 分区内调用 **`GET/POST /api/v1/sessions`** 列出或新建会话；选中会话后展示 **`/api/v1/sessions/{id}`** 返回的 **turns**（用户语句与助手编译出的标准模板 JSON，可复制）。在 `POST /api/v1/agent/compile` 中携带 `session_id` 后，编译记录会出现在此时间线中。

**脚本交付（成片任务）**：选中 `loan_animation`、`fund_animation`、`generate_intro_video` 等成片任务后会出现 **「脚本交付（JSON）」**。**默认须**导入或粘贴合法 `Screenplay` JSON 并 **解析并加载** 后，「开始运行」才可用；若你**明确**只想用表单参数（如 platform、topic、style）走项目内置默认管线，请勾选 **「本次不使用 Screenplay JSON」**。示例：[static/sample_screenplay.json](static/sample_screenplay.json)；脚手架项目在 `content/sample_screenplay.json`。

### 控制台主要 HTTP API

**版本化控制面（推荐集成）**：前缀 **`/api/v1`** — 作业列表/详情、意图会话、Agent 编译等均在此（详见 [docs/STUDIO_ARCHITECTURE.md](docs/STUDIO_ARCHITECTURE.md)）。下列为控制台与兼容路径。

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/health` | 控制面就绪 |
| `GET` | `/api/v1/jobs` | 分页列出**持久化**渲染作业 |
| `POST` | `/api/v1/jobs` | 使用 `StandardVideoJobRequest` 提交异步任务 |
| `GET`/`POST` | `/api/v1/sessions` | 意图会话（自然语言多轮） |
| `GET` | `/api/registry` | 列出已发现子项目、任务与 `capabilities` |
| `GET` | `/api/inspect/{project}/{task}` | 反射任务函数参数与 Docstring，驱动动态表单 |
| `POST` | `/api/run/{project}/{task}` | 提交任务；请求体 `{"kwargs": {...}}`；响应含 `job_id` |
| `GET` | `/api/jobs/{job_id}` | 查询任务状态与结果（成功时 `result` 内可含 `scene_schedule` 等） |
| `GET` | `/api/jobs/{job_id}/scene-schedule` | 若结果含节拍表，可下载 JSON |
| `GET` / `PUT` | `/api/settings` | 读取/更新全局视频与 API 相关设置（密钥在界面中脱敏） |
| `POST` | `/api/settings/validate-openai` | 校验 OpenAI 兼容接口连通性 |
| `GET` / `POST` / `PATCH` | `/api/screenplay/{project}/...` | 对声明了剧本能力的子项目做代理（见各项目 `capabilities`） |
| `POST` | `/api/projects` | 创建新项目脚手架（与 `scheduler.py scaffold` 同源能力） |
| `DELETE` | `/api/projects/{name}` | 删除 `projects/<name>/` 目录；**内置参考项目**（见 API 返回的 `reference_project_names`）拒绝删除 |
| `POST` | `/api/projects/delete` | 请求体 `{"name": "<id>"}`，与上一行**等价**；控制台默认走此接口（与「新建」同为 POST，且避免旧进程未加载 DELETE 时出现 404） |
| `GET` | `/api/agent/catalog` | **Agent**：子项目/任务/manifest 参数提示（供自然语言编译） |
| `GET` | `/api/agent/schema` | **Agent**：`StandardVideoJobRequest` 的 JSON Schema（稳定契约） |
| `POST` | `/api/agent/compile` | **Agent**：自然语言（及可选 `previous` 模板）→ 标准任务 JSON；需配置 OpenAI 兼容 API |
| `POST` | `/api/agent/validate` | **Agent**：校验标准模板是否可被当前注册表执行 |
| `POST` | `/api/agent/run` | **Agent**：用标准模板异步触发任务，语义同 `POST /api/run/...`，返回 `job_id` |
| `GET` | `/api/viz/backends` | 列出当前注册的可视化渲染后端及其能力（matplotlib / manim 等） |
| `GET` | `/api/viz/self-correction/categories` | 列出 Self-Correction 反馈环支持的错误分类与是否支持自动修复 |

自然语言与 Claude Code 等对接说明见 **[docs/AGENT.md](docs/AGENT.md)**；控制面（数据库、作业持久化、API 版本）见 **[docs/STUDIO_ARCHITECTURE.md](docs/STUDIO_ARCHITECTURE.md)**。规范 REST 前缀为 **`/api/v1`**（兼容旧路径 `/api/jobs`、`/api/agent`）。命令行：`video-agent`（安装 `pip install -e .` 后可用）。

`GET /api/registry` 中每个子项目含 **`deletable`**：用户自建一般为 `true`，内置参考为 `false`。前端据此显示删除或锁定图标。

前端由 `static/index.html` + `static/css/dashboard.css` + `static/js/dashboard-app.js` 组成（见 [`static/README.md`](static/README.md)）；参数反射见 `orchestrator/inspector.py`。端到端干跑见 `tests/e2e/test_dashboard_e2e.py`。

### 控制台任务命名约定（便于 UI 分组）

新项目的 `entrypoints.py` 中任务函数名建议遵循下表，控制台可按关键字归类（无需改前端）：

| 任务名特征 | 后台分组 | 界面分组示例 |
|------------|----------|----------------|
| `smoke_check` | `prep` | 准备工作 / 环境自检 |
| `*_animation`、`*_video` | `core` | 视频生成 |
| `api` | `dev` | 后台服务 |
| 其他 | `other` | 其他任务 |

项目名、任务名建议使用清晰英文 `snake_case`；界面可将 `crypto_tracker` 格式化为「Crypto Tracker」。

### 控制台参数表单约定

表单控件类型与默认值来自 **Python 函数签名** 与 **Docstring 的 `Args:`**，例如：

```python
def my_new_task(
    input_file: str,
    mode: str = "fast",
    enable_gpu: bool = True,
    limit: int = 100,
) -> dict:
    """我的新任务。

    Args:
        input_file: 数据文件路径
        mode: 运行模式
    """
```

遵循上述约定时，新项目可尽量 **零前端配置** 接入控制台。

## 调度器用法

```bash
# 列出所有已发现子项目及任务
python scheduler.py list

# 列出所有注册的可视化渲染后端
python scheduler.py backends

# ── loan_comparison ──────────────────────────────────────────
python scheduler.py run --project loan_comparison --task smoke_check
python scheduler.py run --project loan_comparison --task loan_animation
python scheduler.py run --project loan_comparison --task api

# 带参数运行
python scheduler.py run --project loan_comparison --task loan_animation \
  --param platform="douyin" \
  --param output_file="runtime/outputs/custom.mp4" \
  --param width=1080 --param height=1920 \
  --param duration=30 --param fps=30 \
  --param loan_amount=800000 --param annual_rate=0.039 --param loan_years=20

# ── fund_fee_erosion ─────────────────────────────────────────
python scheduler.py run --project fund_fee_erosion --task smoke_check
python scheduler.py run --project fund_fee_erosion --task fund_animation
python scheduler.py run --project fund_fee_erosion --task api

# 带参数运行
python scheduler.py run --project fund_fee_erosion --task fund_animation \
  --param platform="douyin" \
  --param output_file="runtime/outputs/custom_fund.mp4" \
  --param principal=2000000 --param gross_return=0.07 --param years=25
```

## 子项目任务说明

### loan_comparison — 等额本息 vs 等额本金

| 任务 | 说明 |
|------|------|
| `smoke_check` | 轻量验证，仅做贷款计算，无需 ffmpeg / OpenAI |
| `loan_animation` | 渲染贷款对比动画 MP4，需要 ffmpeg |
| `api` | 启动 FastAPI 服务（默认 `0.0.0.0:8000`） |

`loan_animation` 支持参数：`platform`、`quality`、`output_file`、`width`、`height`、`duration`、`fps`、`loan_amount`、`annual_rate`、`loan_years`

当提供 `platform` 时，`width` / `height` / `fps` 必须与平台预设一致；推荐直接只传 `platform` 与业务参数。

### fund_fee_erosion — 基金手续费复利侵蚀

| 任务 | 说明 |
|------|------|
| `smoke_check` | 轻量验证，输出4档费用方案收益对比，无需 ffmpeg |
| `fund_animation` | 渲染手续费侵蚀对比动画 MP4，需要 ffmpeg |
| `api` | 启动 FastAPI 服务（默认 `0.0.0.0:8001`） |

`fund_animation` 支持参数：`platform`、`quality`、`output_file`、`width`、`height`、`duration`、`fps`、`principal`、`gross_return`、`years`

当提供 `platform` 时，`width` / `height` / `fps` 必须与平台预设一致；推荐直接只传 `platform` 与业务参数。

### video_platform_introduction — 平台介绍展示视频

| 任务 | 说明 |
|------|------|
| `smoke_check` | 环境自检，验证 Manim 依赖与剧本加载，无需 ffmpeg |
| `generate_intro_video` | 使用 Manim 渲染平台介绍动画 MP4（需要 Manim + ffmpeg） |

本项目使用 **Manim** 渲染引擎（非 matplotlib），演示 `screenplay_workflow` 剧本驱动能力。manifest 中声明 `capabilities.viz_backends: ["manim"]`，控制台会据此显示剧本交付入口。

## API 服务

### loan_comparison（默认 :8000）

- **接口文档**：`http://localhost:8000/docs`
- **健康检查**：`GET http://localhost:8000/health`
- **贷款汇总**：`POST http://localhost:8000/api/loan/summary`
- **生成视频**：`POST http://localhost:8000/api/generate-video`
- **任务状态**：`GET http://localhost:8000/api/task/{task_id}`
- **任务结果**：`GET http://localhost:8000/api/task/{task_id}/result`
- **视频下载**：`GET http://localhost:8000/api/download/{task_id}`

### fund_fee_erosion（默认 :8001）

- **接口文档**：`http://localhost:8001/docs`
- **健康检查**：`GET http://localhost:8001/health`
- **费用汇总**：`GET http://localhost:8001/api/fund/summary`
- **生成视频**：`POST http://localhost:8001/api/generate-video`
- **任务状态**：`GET http://localhost:8001/api/task/{task_id}`
- **任务结果**：`GET http://localhost:8001/api/task/{task_id}/result`
- **视频下载**：`GET http://localhost:8001/api/download/{task_id}`

`POST /api/generate-video` 现在要求请求体显式传入 `platform`，可选值为：

- `bilibili_landscape`
- `bilibili_vertical`
- `douyin`
- `xiaohongshu`

服务会根据平台自动锁定分辨率和标准帧率，并校验视频时长是否落在平台建议范围内。

同时支持统一质量档：

- `preview`：快速预览，适合验证画面与流程
- `draft`：默认草稿，适合内容审阅
- `final`：最终交付，使用更高 DPI 和更保守压缩参数

同时支持统一内容风格：

- `minimal`：极简说明
- `tech`：科技感 / 数据感更强
- `news`：新闻播报式表达
- `trendy`：更适合短视频口吻

同时支持内容结构版本：

- `short`：更适合 30~45 秒精华版
- `standard`：更适合 60~180 秒完整表达
- 留空时会按视频时长自动推断

成片后处理相关字段：

- `burn_subtitles`：是否将 `.srt` 字幕直接烧录进最终视频（默认开启）
- `background_music`：可选，本地 BGM 文件路径
- `bgm_volume`：BGM 音量
- `video_audio_volume`：原视频音量
- `bgm_loop`：BGM 不足时是否循环
- `ducking_enabled` / `ducking_strength`：原视频存在音轨时，对 BGM 做压低处理

当任务完成后，`GET /api/task/{task_id}/result` 会返回：

- 原始渲染视频路径
- 最终成片路径
- 视频下载地址
- 字幕文件路径（`.srt`）
- 样式化字幕文件路径（`.ass`，如果成功生成）
- 封面帧路径（`.png`）
- 平台、质量档、时长、分辨率等元数据
- 字幕是否已烧录、BGM 是否已应用
- 当前字幕交付模式（`subtitle_render_mode`）
- 内容风格、内容结构版本、结论卡片标题
- 当前使用的视觉主题名（`theme_name`）
- 当前画面主导表达焦点（`visual_focus`）

还可以在正式渲染前预览内容方案：

- 贷款项目：`POST /api/content/preview`
- 基金项目：`POST /api/content/preview`

内容预览返回：

- 开场钩子
- 四段式内容节拍（hook / setup / climax / conclusion）
- 可直接转换为字幕的文案切片
- 按节拍生成的字幕 cue（含 `style_token` / `beat_type`）
- 结论卡片模板信息（标题 / 正文 / 强调标签 / 主题）

内容方案还会进一步映射为渲染表达：

- 标题文案
- 开场冲击文案
- 总结文案
- 结论卡片标题 / 正文 / 强调标签
- 共享视觉主题资产（`shared/content/themes.py`）
- 主题强调色 / 次强调色 / 背景色 / 面板色 / CTA 色
- `short` / `standard` 对应的节奏提示
- 标题层级与字号资产（`typography`）
- 字体族 / 字重 / 行高等共享排版资产（`typography`）
- 卡片背景 / 边框 / 标题色 / 正文字色 / 徽标底色（`card`）
- Hook / 图表 / 结尾场景布局提示（`layout`）
- 场景级行为令牌（`scene_behavior`）
- 平台安全区令牌与安全内容边界（`safe_area`）
- 封面模板令牌与主题化封面文案（`cover`）
- 字幕布局建议、字幕样式令牌与字幕 cue（`subtitle_layout` / `subtitle_styles` / `subtitle_cues`）
- 将 `visual_hint` 归一化后的视觉 cue（`visual_cues`）
- 归纳后的画面焦点摘要（`visual_focus`）

不同平台与风格会使用不同的钩子模板；例如同样是 `tech` 风格，抖音会更强调快速冲击式开场，B 站则更偏解释型开场。

当前 `loan_comparison` 与 `fund_fee_erosion` 已接入这条链路，形成了：

`内容方案 -> 视觉主题资产 -> RenderExpression -> 项目渲染实现`

其中 `C-4` 已落地的内容包括：

- `shared/content/themes.py`：沉淀 `minimal / tech / news / trendy` 四套共享视觉主题预设。
- `RenderExpression`：除文案外，还包含更完整的 `theme` / `typography` / `card` / `layout` / `visual_cues` / `visual_focus`。
- `fund_fee_erosion`：更深消费主题资产，驱动头部标题层级、冲击数字卡、图表说明、结论卡和页脚说明。
- `loan_comparison`：更深消费主题资产，驱动标题栏、参数卡、趋势图图例、结论卡和底部 CTA 表达。
- 两个项目的任务结果接口：都能返回 `theme_name` 与 `visual_focus`，方便追踪本次内容是如何映射到视觉表达的。

`C-5.1` 当前已继续下沉的内容包括：

- `shared/content/themes.py`：为四套主题补齐字体族、数字字体、字重、行高等共享排版基线。
- `shared/content/typography.py`：新增 Matplotlib 排版 helper，统一字体候选、字重归一化和字体应用逻辑。
- `RenderExpression.typography`：除字号外，现已包含 `font_family / font_fallbacks / numeric_font_family / *_weight / *_line_height` 等排版资产。
- `loan_comparison` 与 `fund_fee_erosion`：已切换为从共享排版令牌中读取字体栈、字重和行高，减少各自 renderer 的局部排版硬编码。

`C-5.2` 当前已继续下沉的内容包括：

- `shared/platform/presets.py`：平台预设除像素级安全区外，现已提供归一化安全区 helper。
- `RenderExpression.safe_area`：新增 `top/bottom/left/right` 的像素值、比例值、内容安全边界与 `subtitle_band_top`。
- `loan_comparison`：`GridSpec` 外边距开始由共享 `safe_area` 驱动，标题区与底部 CTA 不再完全依赖硬编码边距。
- `fund_fee_erosion`：figure 布局边距开始由共享 `safe_area` 驱动，标题、结论和页脚内容会整体避让平台安全区。
- 当前策略是“先保证关键文本和底部留白遵守平台安全区”；字幕样式本身仍留待 `C-5.3` 继续体系化。

`C-5.3` 当前已继续下沉的内容包括：

- `shared/content/schemas.py`：新增 `SubtitleCue`，`ContentPlan` 现可显式携带 `subtitle_cues`。
- `shared/content/planner.py`：已将 `hook / setup / climax / conclusion` 稳定映射为 `hook_emphasis / body_explainer / climax_emphasis / conclusion_summary|conclusion_cta`。
- `shared/platform/presets.py`：新增字幕布局 helper，导出平台相关的 `anchor / max_lines / max_width_ratio / bottom_px`。
- `RenderExpression`：现已包含 `subtitle_layout`、`subtitle_styles`、`subtitle_cues`，把内容节拍、平台安全区、主题排版收拢成共享字幕契约。
- `shared/media/video_editor.py`：`write_srt()` 保持向后兼容，只依赖 `start / end / text`，会忽略 `style_token` 等扩展键。
- 当前策略是“先把字幕元数据与布局建议体系化”，真正的字幕烧录样式增强仍可在后续阶段继续下沉。

`C-5.4` 当前已继续下沉的内容包括：

- `RenderExpression`：新增 `cover` 令牌，把眉题、主标题、强调语、摘要语和封面布局沉淀为共享封面契约。
- `shared/media/video_editor.py`：新增模板优先的封面生成入口，会优先生成主题化封面，失败时再回退到视频截帧。
- `loan_comparison` / `fund_fee_erosion`：后台任务的封面生成已从单纯 `extract_cover_frame()` 升级为统一 `generate_cover_image()`。
- 当前策略是“先做到主题感知封面模板 + 截帧兜底”；更复杂的封面设计系统仍可在后续阶段继续深化。

`C-5.5` 当前已继续下沉的内容包括：

- `shared/content/renderer_tokens.py`：新增共享 renderer helper，收敛主题/card fallback、排版角色字号换算、字重/行高解析、安全区到 figure bounds 的映射。
- `loan_comparison` / `fund_fee_erosion`：已改为优先消费共享 renderer token helper，而不是各自重复维护 bootstrap 逻辑。
- 当前策略是“共享 bootstrap 基础设施”，不是强行抽一个通用 renderer 基类；scene 绘制流程仍然保留项目自由度。

`C-5.6` 当前已继续下沉的内容包括：

- `RenderExpression`：新增 `scene_behavior`，把 `hero_number / full_context / cta_card` 等 cue 派生为 renderer 可直接消费的场景指令。
- `loan_comparison`：开场参数卡密度、分叉节奏、月供对比窗口长度、关键里程碑参考线和 CTA 结尾卡面积都会随 `scene_behavior` 变化。
- `fund_fee_erosion`：header 支撑文案密度、参考线密度、shock card 淡出节奏、结论卡 reveal 顺序会随 `scene_behavior` 变化。
- 当前策略是“让 cue 真正驱动场景结构”，不是只停留在文案替换或微调字号。

`C-6` 已完成，当前落地内容包括：

- `shared/media/video_editor.py`：新增 `write_ass()`，可基于 `subtitle_layout / subtitle_styles / subtitle_cues` 生成样式化 ASS 字幕。
- 最终成片链路：字幕烧录已改为优先使用 `.ass`，如果样式化字幕生成失败则自动回退到 `.srt`。
- `loan_comparison` / `fund_fee_erosion`：任务结果中现已返回 `styled_subtitle_path` 与 `subtitle_render_mode`，可观察本次是否走了样式化字幕主路径。
- 当前策略是“先完成共享样式化字幕引擎 + 两项目接入”；逐字高亮、卡拉 OK 特效等更复杂字幕特效不在本轮范围内。

## 可视化渲染后端

系统采用可插拔后端架构（`shared/visualization/`），当前支持：

| 后端 | 模块 | 适用场景 |
|------|------|----------|
| **matplotlib**（默认） | `shared/visualization/backends/matplotlib_backend.py` | 折线图、柱状图、散点图、Bar Chart Race 等统计图表类 |
| **manim** | `shared/visualization/backends/manim_backend.py` | 数学动画、公式推导、几何变换、算法可视化 |

后端在启动时自动注册；Manim 后端在 `manim` 包不可用时静默跳过。各子项目可在 `project_manifest.py` 的 `capabilities.viz_backends` 中声明使用的后端，控制台侧栏会显示对应标签。

```bash
# CLI 查看所有后端
python scheduler.py backends

# API 查看
curl http://127.0.0.1:8090/api/viz/backends
```

## Self-Correction 自动修复

渲染任务执行时自动启用 Self-Correction 反馈环（`shared/core/self_correction.py`）。当任务因以下可自愈原因失败时，系统最多自动重试 2 次：

| 错误分类 | 自动修复策略 |
|----------|------------|
| `font_not_found` | 回退到 Noto Sans SC |
| `ffmpeg_error` | 添加 `-pix_fmt yuv420p` |
| `out_of_memory` | 降级到 preview 质量 |
| `timeout` | 延长超时时间 |
| `matplotlib_error` | 降低 DPI |

不可自动修复的类别（`missing_dependency`、`file_not_found`、`invalid_parameter`、`unknown`）会直接报告诊断结果供用户处理。

**用户可感知方式**：
- **Web 控制台**：失败时显示「Self-Correction 诊断」（错误分类 + 建议 + 重试次数）；成功但经过重试时显示修复记录
- **CLI 日志**：任务执行中打印每次诊断与修复动作
- **API**：`GET /api/jobs/{job_id}` 的 `result` 字段含 `self_correction` 对象；`GET /api/viz/self-correction/categories` 列出全部分类

## 新增子项目

可以直接用脚手架命令生成最小项目骨架：

```powershell
python scheduler.py scaffold --name your_project --description "Your project description" --port 8010
```

生成后会自动包含：

- `project_manifest.py`
- `entrypoints.py`
- `content/planner.py`
- `api/main.py`
- `models/schemas.py`
- 基础包目录与 `tests/`

然后再运行：

```powershell
python scheduler.py list
```

确认子项目已经被根调度器发现。

## 配置说明

复制 `.env.example` 为 `.env` 并按需修改。主要配置项：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `VIDEO__WIDTH` | `1080` | 视频宽度（px） |
| `VIDEO__HEIGHT` | `1920` | 视频高度（px） |
| `VIDEO__FPS` | `30` | 帧率 |
| `VIDEO__OUTPUT_DIR` | `runtime/outputs` | 视频输出目录 |
| `LOG__LOG_DIR` | `runtime/logs` | 日志目录 |
| `CACHE_DIR` | `runtime/cache` | 缓存目录 |
| `VIDEO_RUNTIME_DIR` | —— | 一键覆盖整个 `runtime/` 根路径 |
| `API__OPENAI_API_KEY` | —— | OpenAI API Key（可选） |
| `API__PEXELS_API_KEY` | —— | Pexels API Key（可选） |

完整配置项见 `.env.example`。

## 测试

```bash
python -m pytest -q                         # 全仓库（根 `tests/` + 各 `projects/*/tests/`）
python -m pytest projects/loan_comparison/tests/ -q
python -m pytest projects/fund_fee_erosion/tests/ -q
python -m pytest tests/ -q
```

**注意事项：**

- `tests/test_api.py`、`tests/test_main.py`、`tests/test_video_pipeline.py` 依赖 `opencv-python`（`cv2`）。若未安装 cv2，这 3 个文件会在收集阶段报错但**不影响其余测试**。如需全量执行，先运行 `pip install opencv-python`。
- E2E 测试（`tests/e2e/`）需要控制台服务**在本地运行**（`python dashboard.py`），否则会失败或跳过。
- 浏览器 UAT（`tests/e2e_browser/`）需额外安装 Playwright：`pip install -e ".[uat]" && python -m playwright install chromium`，详见 [`docs/UAT_BROWSER_AND_AGENT.md`](docs/UAT_BROWSER_AND_AGENT.md)。
- 真实 Agent 编译测试（`tests/uat/`）需要本机 `.env` 中已配置 OpenAI 兼容密钥，且须设置环境变量 `UAT_AGENT_COMPILE=1`。
