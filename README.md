# PythonProject1

数据驱动视频生成平台 — v2.3.0

---

## 这是什么

PythonProject1 是一套视频自动化生成系统，核心能力：

- **4 步向导式创建**：在 Web 控制台选模板 → 填数据 → 选品牌 → 生成视频
- **RESTful API**：支持外部系统集成调用
- **多领域子项目**：贷款对比、基金费率侵蚀、视频平台介绍等开箱即用场景
- **AI 辅助**（可选）：接入 OpenAI 兼容接口实现脚本生成与代码编译

**非开发者**：请先读 [docs/业务落地说明.md](docs/业务落地说明.md)，5 分钟了解如何上线和验收。

---

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 复制配置模板（按需修改）
cp .env.example .env          # Windows: copy .env.example .env

# 3. 环境自检
python main.py doctor

# 4. 启动 Web 控制台
python main.py dashboard
# 浏览器访问 http://127.0.0.1:8090
```

运行 `python main.py` 不带参数，会打印所有可用命令提示。

**外网/服务器监听**：`python main.py dashboard --host 0.0.0.0 --port 8090`

---

## Docker 启动

```bash
# 构建（构建期自动执行 doctor 自检，失败则 build 失败）
docker build -f docker/Dockerfile -t pythonproject1:latest .

# 运行（默认启动 Web 控制台，端口 8090）
docker run -p 8090:8090 pythonproject1:latest

# 或用 compose（推荐生产，含健康检查与持久化卷）
docker compose -f docker/docker-compose.yml up dashboard
```

---

## 前端页面

| 页面 | 地址 | 说明 |
|------|------|------|
| 首页 / 向导 | http://localhost:8090 | 4 步创建视频 |
| AI 编译 | http://localhost:8090/ai_compile.html | 聊天式生成 |
| 项目管理 | http://localhost:8090/projects.html | 项目列表与执行历史 |
| API 文档 | http://localhost:8090/docs | OpenAPI 交互文档 |

---

## API 简介

所有 HTTP 能力统一在同一应用（dashboard 或 api 模式），主要前缀：

| 前缀 | 说明 |
|------|------|
| `/api/studio/v1/*` | Studio 控制面（作业、会话、Agent） |
| `/api/video/v2/*` | 快速图表视频（创建/状态/下载） |
| `/api/domain/<project>/*` | 领域子项目挂载（如 `loan_comparison`） |
| `GET /api/meta/architecture` | 机器可读的前缀与挂载清单 |
| `GET /api/studio/v1/health` | 健康探针 |

```bash
# 示例：创建一个柱状图视频
curl -X POST "http://localhost:8090/api/video/v2/create" \
  -H "Content-Type: application/json" \
  -d '{"template":{"template_id":"bar_chart_race","template_name":"柱状图"},
       "data":{"labels":"2024-01,2024-02","values":"10,20"},
       "brand":{"brand_id":"default"},"platform":"bilibili"}'
```

---

## 项目结构

```
PythonProject1/
│
│  ── 入口 ──────────────────────────────────────────────────
├── main.py              # 统一 CLI（dashboard / api / doctor / demo / cli）
├── dashboard.py         # ASGI 再导出（uvicorn dashboard:app）
├── scheduler.py         # 子项目调度器再导出
├── pyproject.toml       # 包定义与工具配置（black / mypy / pytest）
├── requirements.txt     # 生产运行时依赖
├── requirements-dev.txt # 开发 / 测试依赖（pytest 等）
├── .env.example         # 环境变量模板
│
│  ── 业务逻辑 ───────────────────────────────────────────────
├── app/
│   ├── api/                # HTTP 路由（v2 快速图表视频）
│   ├── core/               # v2 渲染引擎（模板、品牌、视频合成）
│   ├── orchestrator/       # 子项目发现、调度、脚手架
│   ├── projects/           # 领域子项目（loan_comparison / fund_fee_erosion 等）
│   ├── scripts/            # 服务入口（dashboard.py / scheduler.py）
│   └── shared/             # 跨模块共享库
│       ├── ai/             # AI 智能层（agent、content 规划）
│       ├── render/         # 渲染引擎（visualization、media、core）
│       ├── output/         # 输出适配（platform、library）
│       └── ops/            # 运维基础（studio、webapp、config、utils）
│
│  ── 前端 ───────────────────────────────────────────────────
├── web/                    # Web 前端（HTML / JS / CSS）
│   ├── index.html          # 主页（4 步向导）
│   ├── ai_compile.html     # AI 意图编译
│   ├── projects.html       # 项目管理
│   ├── js/                 # Vue 3 应用逻辑
│   └── vendor/             # Bootstrap / Vue 离线包
│
│  ── 测试 ───────────────────────────────────────────────────
├── tests/
│   ├── unit/               # 单元测试（单一模块，纯函数）
│   ├── integration/        # 集成测试（多模块协作、DB、HTTP）
│   ├── e2e/                # 端到端 API 测试（真实 HTTP）
│   ├── browser/            # Playwright 浏览器 UI 测试
│   └── uat/                # 用户验收测试（需真实 LLM 密钥）
│
│  ── 运维 / 辅助 ────────────────────────────────────────────
├── docker/                 # Dockerfile + docker-compose.yml
├── docs/                   # 技术与运营文档
├── examples/               # 演示脚本与工具（demo_*.py / 辅助工具）
└── runtime/                # 运行时数据（输出视频 / SQLite / 日志，gitignore）
```

---

## 测试

```bash
# 安装开发依赖
pip install -r requirements.txt -r requirements-dev.txt

# 单元测试
python -m pytest tests/unit/ -q

# 集成测试
python -m pytest tests/integration/ -q

# API 端到端测试（CI 主链路）
python -m pytest tests/e2e/test_dashboard_e2e.py tests/integration/test_studio_db.py -q

# 全量测试（排除浏览器和 UAT）
python -m pytest tests/ --ignore=tests/browser --ignore=tests/uat -q

# 浏览器 UI 测试（需先安装 playwright）
pip install playwright
python -m playwright install chromium
python -m pytest tests/browser/test_dashboard_ui_walkthrough.py -m browser -q
```

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [docs/业务落地说明.md](docs/业务落地说明.md) | 非技术用户：如何上线、验收、常见问题 |
| [DEPLOY.md](DEPLOY.md) | 完整部署流程（生产/云平台） |
| [ROADMAP.md](ROADMAP.md) | 开发路线图与版本计划 |
| [docs/技术预研报告.md](docs/技术预研报告.md) | 技术选型分析（Flourish/Manim 等） |
| [docs/阶段2-4实现报告.md](docs/阶段2-4实现报告.md) | 核心功能实现细节 |

---

## 环境要求

| 依赖 | 版本 | 必需 |
|------|------|------|
| Python | 3.9+ | 必需 |
| FFmpeg | 5.0+ | 必需（成片） |
| Docker | 20.0+ | 可选 |
| OpenCV | 4.5+ | 可选（帧提取） |

---

## 许可证

MIT License — 详见 [LICENSE](LICENSE)
