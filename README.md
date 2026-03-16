# video_project

数据可视化视频创作工作区，根目录作为总调度层，统一管理多个子项目（当前包含 `loan_comparison`）。

## 架构概览

- `shared/`：公共库，所有子项目均可导入（配置、平台规格、工具函数等）
- `projects/`：各作品子项目，互相独立，可相互借鉴
- `assets/`：共享静态资源（字体、音乐、模板）
- 扩展方式：新增子项目时，在 `projects/` 下添加目录并创建 `project_manifest.py`

## 目录结构

```text
video_project/
├─ CLAUDE.md                      # AI 助手指令与工作区约定
├─ Dockerfile
├─ pyproject.toml
├─ requirements.txt
├─ scheduler.py                   # 根调度 CLI 入口
├─ .env.example                   # 环境变量模板（复制为 .env 后生效）
├─ .gitignore
├─ .github/
│  └─ workflows/python-ci.yml     # CI 配置
│
├─ shared/                        # 公共库
│  ├─ config/settings.py          # 全局配置（VideoConfig / APIConfig / LogConfig）
│  ├─ platform/presets.py         # 平台规格常量（B站/抖音/小红书）
│  ├─ core/
│  │  ├─ exceptions.py            # 公共异常类
│  │  └─ task_manager.py          # 任务生命周期管理 + TaskStatus
│  ├─ media/video_editor.py       # FFmpeg 封装（stub）
│  ├─ visualization/              # 预留：bar_chart_race 等
│  └─ utils/
│     ├─ decorators.py            # retry / log_execution
│     ├─ logger.py                # setup_logger
│     └─ validators.py            # 通用范围检查
│
├─ assets/                        # 共享静态资源（字体、音乐、模板）
│
├─ projects/
│  └─ loan_comparison/            # 贷款对比可视化子项目
│     ├─ project_manifest.py      # 任务清单（供调度器发现）
│     ├─ entrypoints.py           # 暴露给调度器的入口函数
│     ├─ api/main.py              # FastAPI 服务
│     ├─ renderer/
│     │  ├─ animation.py          # 调度层（generate_loan_animation + ContentEngine）
│     │  └─ impl.py               # matplotlib 渲染脚本（subprocess 执行）
│     ├─ models/
│     │  ├─ loan.py               # 贷款计算模型
│     │  ├─ schemas.py            # Pydantic 请求/响应模型
│     │  └─ validators.py         # 贷款参数验证
│     └─ tests/                   # 项目级测试（24 个）
│
├─ orchestrator/                  # 项目发现与任务执行核心
│  ├─ registry.py                 # 扫描 projects/ 目录
│  └─ runner.py                   # 任务执行器
│
├─ tests/                         # 根级测试（26 个）
└─ runtime/                       # 运行时输出，gitignore
   ├─ outputs/                    # 视频文件
   ├─ logs/
   ├─ cache/
   └─ temp/
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt
# 或以可编辑模式安装（支持直接 import shared / loan_comparison）
pip install -e .

# 2. 配置环境变量（可选，默认值已可用）
cp .env.example .env

# 3. 验证安装
python scheduler.py run --project loan_comparison --task smoke_check
```

## 调度器用法

```bash
# 列出所有已发现子项目及任务
python scheduler.py list

# 运行指定任务
python scheduler.py run --project loan_comparison --task smoke_check
python scheduler.py run --project loan_comparison --task loan_animation
python scheduler.py run --project loan_comparison --task api

# 带参数运行
python scheduler.py run --project loan_comparison --task loan_animation \
  --param output_file="runtime/outputs/custom.mp4" \
  --param width=1080 --param height=1920 \
  --param duration=30 --param fps=30 \
  --param loan_amount=800000 --param annual_rate=0.039 --param loan_years=20

python scheduler.py run --project loan_comparison --task api \
  --param host="127.0.0.1" --param port=8000

# 运行所有子项目默认任务
python scheduler.py run-all
```

### loan_comparison 任务说明

| 任务 | 说明 |
|------|------|
| `smoke_check` | 轻量验证，仅做贷款计算，无需 ffmpeg / OpenAI |
| `loan_animation` | 渲染贷款对比动画 MP4，需要 ffmpeg |
| `api` | 启动 FastAPI 服务（默认 `0.0.0.0:8000`） |

`loan_animation` 支持参数：`output_file`、`width`、`height`、`duration`、`fps`、`loan_amount`、`annual_rate`、`loan_years`

## API 服务

启动后访问：

- **接口文档**：`http://localhost:8000/docs`
- **健康检查**：`GET http://localhost:8000/health`
- **贷款汇总**：`POST http://localhost:8000/api/loan/summary`
- **生成视频**：`POST http://localhost:8000/api/generate-video`
- **任务状态**：`GET http://localhost:8000/api/task/{task_id}`

## 新增子项目

1. 在 `projects/YourProject/` 创建子项目目录，结构参考 `projects/loan_comparison/`。
2. 添加 `project_manifest.py`，声明任务名称和可调用路径。
3. 添加 `entrypoints.py`，将任务封装为普通函数。
4. 运行 `python scheduler.py list` 验证自动发现。

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
pytest                                  # 全部 50 个测试
pytest projects/loan_comparison/tests/  # 仅 loan_comparison（24 个）
pytest tests/                           # 仅根级（26 个）
```
