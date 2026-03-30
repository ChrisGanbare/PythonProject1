# PythonProject1 v2.3 - 从零开始学习指南

> 📖 本指南带你从零开始，系统学习整个项目
> 
> **预计时间**: 2-3 小时 | **难度**: 中级 | **前置知识**: Python 基础、Web 开发基础

---

## 🎯 学习目标

完成本指南后，你将能够：

1. ✅ 理解项目的整体架构和设计思想
2. ✅ 掌握核心功能的使用和配置
3. ✅ 了解关键代码的实现逻辑
4. ✅ 具备二次开发和扩展的能力

---

## 📚 学习路线图

```
第 1 章：项目概览 (15 分钟)
    ├── 1.1 项目是什么？
    ├── 1.2 技术栈总览
    └── 1.3 项目结构
    
第 2 章：快速体验 (30 分钟)
    ├── 2.1 环境搭建
    ├── 2.2 第一个视频
    └── 2.3 功能探索
    
第 3 章：架构解析 (45 分钟)
    ├── 3.1 整体架构
    ├── 3.2 核心模块
    └── 3.3 数据流转
    
第 4 章：核心功能详解 (60 分钟)
    ├── 4.1 数据输入与校验
    ├── 4.2 模板系统
    ├── 4.3 渲染引擎
    └── 4.4 品牌系统
    
第 5 章：代码实战 (60 分钟)
    ├── 5.1 添加新模板
    ├── 5.2 自定义校验规则
    └── 5.3 扩展 API
    
附录：常见问题与调试技巧
```

---

## 第 1 章：项目概览

### 1.1 项目是什么？

**一句话定义**：
> PythonProject1 是一个**数据可视化视频生成系统**，可以将数据自动转换为动画视频。

**类比理解**：
- 像 **Flourish**（数据可视化工具）+ **Canva**（设计工具）的结合
- 但更专注于**视频生成**和**动画效果**

**核心流程**：
```
数据输入 → 选择模板 → 配置样式 → 生成视频
   ↓           ↓           ↓          ↓
 CSV/手动   柱状图/折线  品牌主题   MP4 文件
```

### 1.2 技术栈总览

#### 前端技术
| 技术 | 用途 | 版本 |
|------|------|------|
| **Vue.js 3** | 前端框架 | 3.x |
| **Bootstrap 5** | UI 框架 | 5.3.3 |
| **Plotly** | 图表库 | 5.18+ |

#### 后端技术
| 技术 | 用途 | 版本 |
|------|------|------|
| **Python** | 主语言 | 3.9+ |
| **FastAPI** | Web 框架 | latest |
| **Plotly** | 数据可视化 | 5.18+ |
| **Manim** | 动画引擎 | 0.18+ |
| **MoviePy** | 视频处理 | 2.0+ |
| **FFmpeg** | 视频编码 | 5.0+ |

#### 部署技术
| 技术 | 用途 |
|------|------|
| **Docker** | 容器化部署 |
| **GitHub Actions** | CI/CD |

### 1.3 项目结构

```
D:\PythonProject1/
├── 📄 main.py                    # 主入口（启动脚本）
├── 📄 README.md                  # 项目文档
│
├── 📁 api/                       # 后端 API
│   ├── main.py                   # API 服务入口
│   └── v2_routes.py              # v2 视频生成接口 ⭐
│
├── 📁 core/                      # 核心逻辑 ⭐
│   ├── v2_renderer.py            # 渲染器
│   ├── templates/                # 模板定义
│   │   ├── bar_chart.py          # 柱状图模板
│   │   ├── line_chart.py         # 折线图模板
│   │   └── base.py               # 基础模板类
│   ├── data/                     # 数据处理
│   │   └── sources.py            # 数据源
│   ├── brand/                    # 品牌系统
│   │   └── themes.py             # 主题配置
│   └── render/                   # 渲染后端
│       └── plotly_renderer.py    # Plotly 渲染器
│
├── 📁 static/                    # 前端静态文件 ⭐
│   ├── index.html                # 首页（4 步向导）
│   ├── settings-modal.html       # 全局设置
│   ├── projects.html             # 项目管理
│   ├── ai_compile.html           # AI 编译
│   └── code_studio.html          # 代码工坊
│
├── 📁 scripts/                   # 工具脚本
│   ├── dashboard.py              # Dashboard 服务
│   └── scheduler.py              # 调度器
│
├── 📁 poc/                       # 概念验证
│   ├── demo_stages.py            # 演示脚本
│   └── src/                      # POC 源码
│
├── 📁 projects/                  # 子项目
│   └── my_tutor/                 # 示例子项目
│
├── 📁 tests/                     # 测试文件
│   └── validation_test.py        # 验证测试
│
└── 📁 docs/                      # 补充文档
    ├── DEPLOY.md                 # 部署指南
    └── ROADMAP.md                # 开发路线
```

**关键标识**：
- ⭐ = 核心文件（重点学习）

---

## 第 2 章：快速体验

### 2.1 环境搭建

#### 步骤 1：检查环境
```bash
# 检查 Python 版本（需要 3.9+）
python --version

# 检查 pip
pip --version
```

#### 步骤 2：安装依赖
```bash
cd D:\PythonProject1
pip install -r poc/requirements.txt
```

#### 步骤 3：启动服务
```bash
# 启动 Dashboard
python main.py dashboard
```

#### 步骤 4：访问页面
打开浏览器访问：http://localhost:8090

### 2.2 第一个视频

**跟着做**：

1. **选择模板**
   - 点击"柱状图竞赛"
   
2. **输入数据**
   ```
   日期/类别：2024-01, 2024-02, 2024-03, 2024-04
   数值：100, 150, 200, 180
   系列名称：销售额
   ```

3. **选择品牌**
   - 点击"默认"品牌

4. **生成视频**
   - 点击"开始生成"
   - 等待进度条完成

**预期结果**：
- ✅ 看到视频生成成功的提示
- ✅ 视频保存在 `runtime/outputs/v2/` 目录

### 2.3 功能探索

**尝试以下功能**：

1. **全局设置**（右上角齿轮图标）
   - 配置 API Key（用于 AI 功能）
   - 修改视频分辨率
   - 调整帧率

2. **文件上传**
   - 点击"下载模板"下载 CSV 模板
   - 填写数据后上传

3. **数据校验**
   - 尝试输入错误格式（如连续逗号）
   - 观察错误提示

---

## 第 3 章：架构解析

### 3.1 整体架构

```
┌─────────────────────────────────────────────────┐
│              前端层 (Vue.js 3)                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ index   │ │projects │ │  AI     │           │
│  │ 首页     │ │ 项目管理 │ │ 编译    │  等...    │
│  └────┬────┘ └────┬────┘ └────┬────┘           │
└───────┼──────────┼───────────┼─────────────────┘
        │          │           │
        │ HTTP     │ HTTP      │ HTTP
        │          │           │
┌───────┼──────────┼───────────┼─────────────────┐
│       ▼          ▼           ▼                  │
│              API 层 (FastAPI)                    │
│  ┌─────────────────────────────────────┐       │
│  │  /api/v2/create  - 创建视频          │       │
│  │  /api/v2/status  - 查询状态          │       │
│  │  /api/settings   - 全局设置          │       │
│  └─────────────────────────────────────┘       │
└────────────────────┬───────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│              核心层 (Core)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Templates│  │  Data    │  │  Brand   │     │
│  │  模板系统 │  │  数据源  │  │  品牌系统 │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │             │             │            │
│       └─────────────┼─────────────┘            │
│                     ▼                          │
│            ┌────────────────┐                  │
│            │  v2_renderer   │                  │
│            │   渲染器       │                  │
│            └───────┬────────┘                  │
└────────────────────┼────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│              渲染层 (Renderer)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Plotly  │  │  Manim   │  │ MoviePy  │     │
│  │  图表渲染 │  │  动画引擎 │  │  视频合成 │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────┘
```

### 3.2 核心模块

#### 模块 1：前端 (static/)

**职责**：用户界面和交互

**关键文件**：
- `index.html` - 4 步向导式视频创建
- `settings-modal.html` - 全局设置模态框

**核心逻辑**：
```javascript
// 1. 用户输入数据
manualData: {
    labels: '2024-01, 2024-02, 2024-03',
    values: '100, 150, 200',
    seriesName: '销售额'
}

// 2. 校验数据
validateInput('labels')  // 检查格式

// 3. 提交到后端
fetch('/api/v2/create', {
    method: 'POST',
    body: JSON.stringify(requestData)
})
```

#### 模块 2：API 层 (api/)

**职责**：接收请求、参数校验、任务调度

**关键文件**：
- `v2_routes.py` - v2 视频生成接口

**核心流程**：
```python
# 1. 接收请求
@router.post("/create")
async def create_video(request: VideoCreateRequest):
    
    # 2. 解析数据
    labels = request.data.labels.split(",")
    values = [float(v) for v in request.data.values.split(",")]
    
    # 3. 构建图表数据
    chart_data = {
        "date": labels,
        "category": [series_name] * len(labels),
        "value": values
    }
    
    # 4. 调用渲染器
    video_path = render_v2_template(
        template_name=template_id,
        data=chart_data,
        brand=brand_id
    )
    
    # 5. 返回结果
    return {"job_id": job_id, "video_path": video_path}
```

#### 模块 3：核心层 (core/)

**职责**：业务逻辑、模板系统、数据处理

**关键组件**：

**a) 模板系统 (core/templates/)**
```python
class BarChartTemplate(BaseTemplate):
    def build(self, data, style):
        # 1. 按日期分组
        dates = sorted(data["date"].unique())
        
        # 2. 为每个日期构建场景
        scenes = []
        for date in dates:
            scene = {
                "id": f"scene_{date}",
                "type": "bar_chart",
                "data": get_top_10(date),
                "config": {...}
            }
            scenes.append(scene)
        
        # 3. 返回视频清单
        return VideoManifest(scenes=scenes, ...)
```

**b) 数据源 (core/data/sources.py)**
```python
class InlineDataSource(DataSource):
    def load(self):
        # 将 dict 转换为 DataFrame
        return pd.DataFrame(self.data)
```

**c) 品牌系统 (core/brand/themes.py)**
```python
def get_theme(brand_name):
    themes = {
        "default": {
            "primary_color": "#1f77b4",
            "secondary_color": "#ff7f0e",
            ...
        },
        "corporate": {...},
        ...
    }
    return themes.get(brand_name)
```

#### 模块 4：渲染层 (core/render/)

**职责**：将视频清单渲染为实际视频文件

**核心流程**：
```python
class PlotlyRenderer:
    def render(self, manifest, output_path):
        # 1. 解析视频清单
        scenes = manifest["scenes"]
        
        # 2. 为每个场景生成图表
        frames = []
        for scene in scenes:
            fig = create_plotly_chart(scene)
            frame = fig.to_image()
            frames.append(frame)
        
        # 3. 合成视频
        video = mp.ImageSequenceClip(frames, fps=30)
        video.write_videofile(output_path)
        
        return output_path
```

### 3.3 数据流转

**完整流程**：

```
用户输入
   ↓
[前端校验] → 错误提示
   ↓ 正确
[HTTP POST /api/v2/create]
   ↓
[API 层解析] → labels, values, series_name
   ↓
[构建 chart_data] → {date, category, value}
   ↓
[调用 render_v2_template]
   ↓
[模板系统.build()] → VideoManifest
   ↓
[渲染器.render()] → MP4 文件
   ↓
[返回 video_path]
   ↓
前端轮询状态
   ↓
显示完成
```

---

## 第 4 章：核心功能详解

### 4.1 数据输入与校验

#### 前端校验 (static/index.html)

**校验规则**：

```javascript
validateInput(field) {
    const value = this.manualData[field]
    
    // 1. 空值检查
    if (!value || value.trim() === '') {
        return { valid: false, error: '此项不能为空' }
    }
    
    // 2. 连续逗号检查
    if (value.includes(',,') || value.includes(',,') || ...) {
        return { valid: false, error: '检测到连续的逗号' }
    }
    
    // 3. 无分隔符检查
    if (!hasSeparator && value.length > 6) {
        return { valid: false, error: '未检测到分隔符' }
    }
    
    // 4. 数值有效性检查
    if (field === 'values') {
        for (const v of values) {
            if (isNaN(parseFloat(v))) {
                return { valid: false, error: `"${v}" 不是有效的数字` }
            }
        }
    }
    
    return { valid: true, error: '' }
}
```

#### 后端兜底 (api/v2_routes.py)

**兼容处理**：

```python
# 支持字符串和数组两种格式
if isinstance(labels_raw, str):
    labels = [l.strip() for l in labels_raw.replace(",", ",").split(",") if l.strip()]
elif isinstance(labels_raw, list):
    labels = [str(l).strip() for l in labels_raw if str(l).strip()]

# 数值转换
values = [float(v.strip()) for v in values_normalized.split(",") if v.strip()]

# 数量校验
if len(labels) != len(values):
    raise ValueError(f"标签和数值数量不匹配")
```

### 4.2 模板系统

#### 模板基类 (core/templates/base.py)

```python
class BaseTemplate:
    def build(self, data: DataSource, style: BrandStyle) -> VideoManifest:
        """
        构建视频清单
        
        Args:
            data: 数据源
            style: 品牌样式
            
        Returns:
            VideoManifest: 视频清单（包含场景、转场、配置等）
        """
        raise NotImplementedError
```

#### 柱状图模板 (core/templates/bar_chart.py)

```python
class BarChartRaceTemplate(BaseTemplate):
    def _build_scenes(self):
        scenes = []
        
        # 按日期分组
        dates = sorted(self.data["date"].unique())
        
        for i, date in enumerate(dates):
            # 获取前 N 名
            top_n = date_data.nlargest(10, "value")
            
            scene = {
                "id": f"scene_{i}",
                "title": str(date),
                "type": "bar_chart",
                "data": {
                    "categories": top_n["category"].tolist(),
                    "values": top_n["value"].tolist()
                },
                "config": {
                    "orientation": "h",
                    "show_labels": True,
                    "sort_by": "value",
                    "sort_order": "desc"
                }
            }
            
            scenes.append(scene)
        
        return scenes
```

### 4.3 渲染引擎

#### Plotly 渲染器 (core/render/plotly_renderer.py)

```python
class PlotlyRenderer:
    def render(self, manifest_dict, output_path):
        manifest = VideoManifest.from_dict(manifest_dict)
        
        # 1. 生成所有帧
        frames = []
        for scene in manifest.scenes:
            fig = self._create_chart(scene)
            img_bytes = fig.to_image(format="png")
            img = Image.open(io.BytesIO(img_bytes))
            frames.append(np.array(img))
        
        # 2. 添加转场
        if manifest.transitions:
            frames = self._add_transitions(frames, manifest.transitions)
        
        # 3. 合成视频
        clip = ImageSequenceClip(frames, fps=manifest.config.fps)
        clip.write_videofile(output_path, codec="libx264")
        
        return output_path
```

### 4.4 品牌系统

#### 主题定义 (core/brand/themes.py)

```python
THEMES = {
    "default": {
        "name": "默认",
        "primary_color": "#1f77b4",
        "secondary_color": "#ff7f0e",
        "accent_color": "#2ca02c",
        "font_family": "Arial",
        "background_color": "#ffffff"
    },
    "corporate": {
        "name": "企业",
        "primary_color": "#003366",
        "secondary_color": "#0066cc",
        "accent_color": "#0099ff",
        ...
    },
    ...
}
```

---

## 第 5 章：代码实战

### 5.1 添加新模板

**任务**：添加一个"饼图动画"模板

**步骤**：

1. **创建模板文件** (`core/templates/pie_chart.py`)
```python
from .base import BaseTemplate, VideoManifest

class PieChartTemplate(BaseTemplate):
    def build(self, data, style):
        scenes = self._build_scenes()
        
        return VideoManifest(
            scenes=scenes,
            transitions=[],
            config={
                "fps": 30,
                "width": 1920,
                "height": 1080
            }
        )
    
    def _build_scenes(self):
        # 实现饼图场景构建逻辑
        pass
```

2. **注册模板** (`core/templates/__init__.py`)
```python
from .pie_chart import PieChartTemplate

TEMPLATES = {
    "bar_chart_race": BarChartRaceTemplate,
    "pie_chart": PieChartTemplate,  # 新增
    ...
}
```

3. **前端添加选项** (`static/index.html`)
```javascript
templates: [
    { id: 'bar_chart_race', name: '柱状图竞赛', ... },
    { id: 'pie_chart', name: '饼图动画', ... },  // 新增
]
```

### 5.2 自定义校验规则

**任务**：添加"日期格式必须为 YYYY-MM"的校验

**步骤**：

1. **前端校验** (`static/index.html`)
```javascript
validateInput(field) {
    if (field === 'labels') {
        const items = value.split(/[,，\s]+/)
        const datePattern = /^\d{4}-\d{2}$/
        
        for (const item of items) {
            if (!datePattern.test(item.trim())) {
                return { 
                    valid: false, 
                    error: '日期格式必须为 YYYY-MM（如：2024-01）' 
                }
            }
        }
    }
    // ...
}
```

2. **后端校验** (`api/v2_routes.py`)
```python
import re

DATE_PATTERN = re.compile(r'^\d{4}-\d{2}$')

for label in labels:
    if not DATE_PATTERN.match(label.strip()):
        raise ValueError(f"日期格式错误：{label}，应为 YYYY-MM 格式")
```

### 5.3 扩展 API

**任务**：添加批量生成接口

**步骤**：

1. **定义请求模型** (`api/v2_routes.py`)
```python
class BatchVideoRequest(BaseModel):
    videos: List[VideoCreateRequest]
    output_dir: str = "runtime/outputs/batch"
```

2. **实现接口**
```python
@router.post("/batch/create")
async def create_batch_videos(request: BatchVideoRequest):
    results = []
    
    for video_req in request.videos:
        try:
            video_path = render_v2_template(...)
            results.append({
                "success": True,
                "video_path": str(video_path)
            })
        except Exception as e:
            results.append({
                "success": False,
                "error": str(e)
            })
    
    return {"results": results}
```

---

## 附录：常见问题与调试技巧

### Q1: 视频生成失败，提示"没有可渲染的场景"

**原因**：
- 数据点太少（至少需要 2 个）
- 数据格式错误

**解决**：
```python
# 检查日志
logger.info(f"chart_data: {chart_data}")
logger.info(f"DataFrame shape: {df.shape}")

# 确保数据格式正确
chart_data = {
    "date": ["2024-01", "2024-02", "2024-03"],  # 至少 2 个
    "category": ["销售额", "销售额", "销售额"],
    "value": [100, 150, 200]
}
```

### Q2: 前端校验不生效

**原因**：
- 浏览器缓存了旧版本

**解决**：
- 强制刷新：`Ctrl + Shift + R`
- 清除浏览器缓存

### Q3: 中文逗号导致解析失败

**解决**：
```python
# 后端已自动处理
values_normalized = values_raw.replace(",", ",").strip()
values = [float(v.strip()) for v in values_normalized.split(",")]
```

### 调试技巧

1. **查看后端日志**
```bash
# 启动时查看详细日志
python main.py dashboard --log-level debug
```

2. **前端控制台**
- 按 `F12` 打开开发者工具
- 查看 Console 和 Network 标签

3. **API 测试**
```bash
# 使用 curl 测试 API
curl -X POST http://localhost:8090/api/v2/create \
  -H "Content-Type: application/json" \
  -d '{"template": {...}, "data": {...}}'
```

---

## 🎓 学习检查清单

完成学习后，检查以下能力：

- [ ] 能独立启动项目并访问 Web 界面
- [ ] 能成功生成第一个视频
- [ ] 理解整体架构（前端→API→核心→渲染）
- [ ] 了解数据流转过程
- [ ] 能解释模板系统的工作原理
- [ ] 能添加简单的校验规则
- [ ] 知道如何调试常见问题

---

## 📖 下一步学习

完成本指南后，可以深入学习：

1. **Manim 动画引擎** - 学习高级动画效果
2. **FFmpeg 视频处理** - 学习视频编码和优化
3. **Docker 部署** - 学习生产环境部署
4. **子项目开发** - 学习创建自定义子项目

---

**祝你学习愉快！** 🎉

有任何问题，随时查阅文档或提出疑问。
