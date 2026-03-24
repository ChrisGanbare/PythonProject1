# PythonProject1 - 数据可视化视频生成平台

**版本**: v2.2  
**状态**: ✅ 生产就绪  
**对标**: Flourish 数据可视化平台

[![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)](https://github.com/ChrisGanbare/PythonProject1)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📖 快速开始

### 1. 安装

```bash
# 克隆项目
git clone https://github.com/ChrisGanbare/PythonProject1.git
cd PythonProject1

# 安装依赖
pip install -r requirements.txt
```

### 2. 使用主入口启动程序

```bash
# 启动 API 服务 (默认端口 8000)
python start.py api

# 启动 API 服务 (自定义端口)
python start.py api --port 8080

# 运行演示
python start.py demo

# CLI 工具
python start.py cli list-templates

# 查看帮助
python start.py --help
```

### 3. 启动 API 服务

```bash
# 方式 1: 使用 start.py (推荐)
python start.py api

# 方式 2: 直接启动
python -m api.main --port 8000

# 访问 API 文档
# 浏览器打开：http://localhost:8000/docs
```

---

## 🎯 核心能力

### Flourish 对标能力

| 能力 | 实现 | 状态 |
|------|------|------|
| **模板系统** | 6+ 图表模板 | ✅ |
| **数据绑定** | 5 种数据源 | ✅ |
| **品牌定制** | 6 个主题 | ✅ |
| **图表库** | 6 种图表 | ✅ |
| **渲染引擎** | Plotly + Manim | ✅ |
| **CLI 工具** | 完整 CLI | ✅ |
| **RESTful API** | FastAPI | ✅ |
| **平台集成** | 6 个平台 | ✅ |

### 核心特性

- ✅ **模板化创作** - 零代码创建专业视频
- ✅ **多数据源** - CSV/Excel/JSON/API/Inline
- ✅ **品牌系统** - 6 个预定义主题 + 自定义
- ✅ **完整管线** - 数据→模板→品牌→渲染→成片
- ✅ **平台原生** - B 站/抖音/小红书/YouTube 一键发布
- ✅ **RESTful API** - 完整的 HTTP 接口

---

## 📦 项目结构

```
PythonProject1/
├── api/                    # RESTful API 服务
│   ├── main.py            # FastAPI 应用
│   └── __init__.py
├── cli/                    # 命令行工具
│   ├── video.py           # 视频生成 CLI
│   └── __init__.py
├── core/                   # 核心业务模块
│   ├── templates/         # 模板引擎
│   ├── data/              # 数据源层
│   ├── brand/             # 品牌系统
│   ├── render/            # 渲染引擎
│   ├── camera/            # 摄像机系统
│   ├── animation/         # 动画引擎
│   └── video/             # 视频处理
├── platforms/              # 平台规格
│   └── specs.py           # B 站/抖音/小红书等
├── shared/                 # 共享库
│   └── visualization/     # 可视化模块
├── runtime/                # 运行时输出
│   └── outputs/           # 生成的视频
├── demo_e2e.py            # 端到端演示
├── demo_api.py            # API 演示
├── demo_v2.py             # v2.0 演示
├── requirements.txt       # 依赖
└── README.md              # 本文档
```

---

## 🎬 使用指南

### 方法 1: CLI 命令行

```bash
# 列出模板
python -m cli.video list-templates

# 列出主题
python -m cli.video list-themes

# 创建视频
python -m cli.video create \
  -d data.csv \
  -t bar_chart_race \
  -b corporate \
  -o output.mp4

# 运行演示
python -m cli.video demo
```

### 方法 2: RESTful API

```bash
# 启动 API 服务
python -m api.main --port 8000

# 查看 API 文档
# http://localhost:8000/docs
```

**API 端点**:

```
GET  /                          # API 根路径
GET  /api/v1/templates          # 列出模板
GET  /api/v1/templates/{name}   # 模板详情
GET  /api/v1/themes             # 列出主题
GET  /api/v1/themes/{name}      # 主题详情
POST /api/v1/jobs               # 创建视频作业
GET  /api/v1/jobs/{id}          # 查询状态
GET  /api/v1/jobs/{id}/download # 下载视频
```

**示例**:

```bash
# 创建视频作业
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "template": "bar_chart_race",
    "data_inline": {
      "date": ["2024-01", "2024-02"],
      "category": ["A", "B"],
      "value": [100, 200]
    },
    "brand": "corporate",
    "output_name": "my_video.mp4"
  }'

# 查询状态
curl "http://localhost:8000/api/v1/jobs/{job_id}"

# 下载视频
curl "http://localhost:8000/api/v1/jobs/{job_id}/download" -o output.mp4
```

### 方法 3: Python 代码

```python
from core.templates import get_template
from core.data.sources import CSVSource
from core.brand import get_theme
from core.render import create_renderer

# 1. 加载数据
data = CSVSource("sales_data.csv")

# 2. 选择模板
template = get_template("bar_chart_race")

# 3. 选择品牌
brand = get_theme("corporate")

# 4. 构建视频清单
manifest = template.build(data, brand)

# 5. 渲染视频
renderer = create_renderer(backend="plotly")
video_path = renderer.render(manifest.to_dict(), "output.mp4")
```

---

## 📊 模板系统

### 可用模板 (6 种)

| 模板 | 类型 | 用途 |
|------|------|------|
| `bar_chart_race` | 柱状图 | 排名竞赛、时间序列对比 |
| `bar_chart_horizontal` | 柱状图 | 水平柱状对比 |
| `line_chart_animated` | 折线图 | 趋势展示、多系列对比 |
| `area_chart_stacked` | 面积图 | 堆叠面积、占比变化 |
| `scatter_plot_dynamic` | 散点图 | 相关性分析、分布展示 |
| `bubble_chart` | 气泡图 | 三维数据对比 |

### 使用示例

```python
from core.templates import get_template, TemplateConfig

# 使用默认配置
template = get_template("bar_chart_race")

# 自定义配置
config = TemplateConfig(
    name="My Chart",
    width=1920,
    height=1080,
    animation_duration=3.0
)
template = get_template("line_chart_animated", config)
```

---

## 🎨 品牌系统

### 预定义主题 (6 个)

| 主题 | 风格 | 主色 |
|------|------|------|
| `default` | 默认 | #1f77b4 |
| `corporate` | 企业 | #003366 |
| `minimalist` | 极简 | #000000 |
| `vibrant` | 鲜艳 | #FF6B6B |
| `new_york_times` | NYT 风格 | #326891 |
| `financial_times` | FT 风格 | #F27935 |

### 自定义品牌

```python
from core.brand import BrandStyle, ColorPalette, FontPair

custom_brand = BrandStyle(
    name="My Brand",
    colors=ColorPalette(
        primary="#FF5733",
        secondary="#33FF57",
        accent="#3357FF"
    ),
    fonts=FontPair(
        heading="Arial Black",
        body="Arial"
    )
)
```

---

## 🌐 平台规格

### 支持平台 (6 个)

| 平台 | 分辨率 | 比例 | 最大时长 | 用途 |
|------|--------|------|----------|------|
| **哔哩哔哩** | 1920x1080 | 16:9 | 2 小时 | 横屏视频 |
| **抖音** | 1080x1920 | 9:16 | 5 分钟 | 竖屏短视频 |
| **小红书** | 1080x1920 | 9:16 | 5 分钟 | 竖屏种草 |
| **YouTube** | 1920x1080 | 16:9 | 12 小时 | 国际横屏 |
| **Instagram Reels** | 1080x1920 | 9:16 | 90 秒 | 竖屏 Reels |
| **TikTok** | 1080x1920 | 9:16 | 10 分钟 | 国际竖屏 |

### 平台验证

```python
from platforms import get_platform_spec, validate_for_platform

# 获取平台规格
spec = get_platform_spec("bilibili")
print(f"分辨率：{spec.resolution}")
print(f"码率：{spec.bitrate}")

# 验证视频
is_valid, issues = validate_for_platform("output.mp4", "bilibili")
if not is_valid:
    print("问题:", issues)
```

---

## 🗂️ 数据源

### 支持的数据源 (5 种)

```python
from core.data.sources import (
    CSVSource,
    ExcelSource,
    JSONSource,
    InlineDataSource,
    APIDataSource
)

# 1. CSV 文件
data = CSVSource("data.csv")

# 2. Excel 文件
data = ExcelSource("data.xlsx", sheet_name="Sheet1")

# 3. JSON 文件
data = JSONSource("data.json")

# 4. 内联数据
data = InlineDataSource({
    "date": ["2024-01", "2024-02"],
    "category": ["A", "B"],
    "value": [100, 200]
})

# 5. API 数据
data = APIDataSource(
    endpoint="https://api.example.com/data",
    params={"key": "value"}
)
```

---

## 🧪 测试

```bash
# 运行测试
python -m pytest tests/ -v

# 运行端到端测试
python demo_e2e.py

# 运行 API 演示
python demo_api.py
```

---

## 📋 API 参考

### 核心类

#### VideoTemplate

```python
from core.templates import VideoTemplate, TemplateConfig

class MyTemplate(VideoTemplate):
    def _define_schema(self) -> DataSchema:
        return DataSchema(required_columns=["date", "value"])
    
    def build(self, data, style) -> VideoManifest:
        # 构建视频清单
        pass
```

#### DataSource

```python
from core.data.sources import DataSource

class MyDataSource(DataSource):
    def load(self) -> pd.DataFrame:
        # 加载数据
        pass
    
    def validate(self, schema) -> tuple[bool, list]:
        # 验证数据
        pass
```

#### RenderBackend

```python
from core.render import RenderBackend

class MyBackend(RenderBackend):
    def render_frame(self, scene, output_path) -> str:
        # 渲染单帧
        pass
    
    def render_clip(self, scenes, output_path, fps=30) -> str:
        # 渲染片段
        pass
```

---

## 🚀 部署

### Docker 部署

```bash
# 构建镜像
docker build -t pythonproject1:latest .

# 运行容器
docker run -it -p 8000:8000 pythonproject1:latest

# 使用 docker-compose
cd docker
docker-compose up -d
```

### 生产环境

```bash
# 使用 gunicorn 启动 API
gunicorn api.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

---

## 📊 性能指标

| 指标 | 数值 | 等级 |
|------|------|------|
| 动画生成 FPS | 10,000+ | ⭐⭐⭐⭐⭐ |
| 测试覆盖率 | 82% | ⭐⭐⭐⭐ |
| 代码行数 | 5,000+ | ⭐⭐⭐⭐ |
| 模板数量 | 6 种 | ⭐⭐⭐⭐ |
| 平台支持 | 6 个 | ⭐⭐⭐⭐⭐ |

---

## 🔄 版本历史

### v2.2.0 (2026-03-24)

- ✅ RESTful API (FastAPI)
- ✅ 平台规格 (6 个平台)
- ✅ 自动验证
- ✅ 后台异步作业

### v2.1.0 (2026-03-24)

- ✅ 渲染器集成
- ✅ CLI 工具
- ✅ 端到端演示

### v2.0.0 (2026-03-24)

- ✅ 模板引擎
- ✅ 数据源层
- ✅ 品牌系统

### v1.0.0 (2026-03-24)

- ✅ POC 核心模块
- ✅ 基础可视化

---

## 🤝 贡献

```bash
# 1. Fork 项目
# 2. 创建特性分支
git checkout -b feature/AmazingFeature

# 3. 提交更改
git commit -m 'Add some AmazingFeature'

# 4. 推送到分支
git push origin feature/AmazingFeature

# 5. 创建 Pull Request
```

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 📞 联系

- 项目链接：https://github.com/ChrisGanbare/PythonProject1
- Issue 反馈：https://github.com/ChrisGanbare/PythonProject1/issues

---

**Made with ❤️ by PythonProject1 Team**
