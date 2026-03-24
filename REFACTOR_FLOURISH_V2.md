# Flourish 对标重构方案

**版本**: v2.0.0  
**日期**: 2026-03-24  
**目标**: 打造数据可视化视频创作平台

---

## 🎯 Flourish 核心能力分析

### Flourish 的竞争优势

| 能力维度 | Flourish 做法 | 我们的差距 | 重构方向 |
|----------|--------------|-----------|----------|
| **模板系统** | 100+ 预建模板，零代码创建 | 项目各自为战 | 统一模板引擎 |
| **数据绑定** | Excel/Google Sheets/API | 硬编码数据 | 数据源抽象层 |
| **可视化库** | 25+ 图表类型 | 仅 4 种基础图表 | 扩展图表工厂 |
| **交互叙事** | Scrollytelling、时间线 | 线性视频 | 交互式叙事 |
| **品牌定制** | 颜色、字体、Logo | 有限主题 | 品牌系统 |
| **发布渠道** | Embed、社交媒体 | 本地文件 | 多渠道发布 |
| **协作** | 团队、权限管理 | 单用户 | 多用户协作 |

---

## 🏗️ 重构架构（v2.0）

### 新架构分层

```
┌─────────────────────────────────────────────────┐
│           用户界面层 (UI Layer)                  │
│  Web 控制台 / CLI / API / 未来 GUI               │
├─────────────────────────────────────────────────┤
│           业务能力层 (Business Layer)            │
│  模板引擎 | 数据源 | 图表工厂 | 叙事编排         │
├─────────────────────────────────────────────────┤
│           渲染引擎层 (Render Layer)              │
│  Plotly | Manim | Matplotlib | FFmpeg           │
├─────────────────────────────────────────────────┤
│           基础设施层 (Infrastructure)            │
│  缓存 | 存储 | 队列 | 数据库                     │
└─────────────────────────────────────────────────┘
```

---

## 📦 核心业务模块重构

### 1. 模板引擎 (Template Engine)

**目标**: 实现 Flourish 风格的模板系统

```python
# 新增：core/templates/
class VideoTemplate:
    """视频模板基类"""
    
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category  # bar_chart, line_chart, scatter, etc.
        self.config = TemplateConfig()
        self.data_schema = DataSchema()
    
    def render(self, data: DataSource, style: BrandStyle) -> VideoManifest:
        """渲染模板为视频清单"""
        pass

# 预定义模板库
TEMPLATES = {
    "bar_chart_race": BarChartRaceTemplate(),
    "line_chart_animated": LineChartAnimatedTemplate(),
    "scatter_plot_dynamic": ScatterPlotTemplate(),
    "pie_chart_comparison": PieChartTemplate(),
    "area_chart_stacked": StackedAreaTemplate(),
    "map_choropleth": ChoroplethMapTemplate(),
    "timeline_story": TimelineStoryTemplate(),
}
```

### 2. 数据源抽象 (Data Source Abstraction)

**目标**: 支持多种数据输入方式

```python
# 新增：core/data/sources.py
class DataSource(Protocol):
    """数据源协议"""
    
    def load(self) -> pd.DataFrame:
        """加载数据"""
        pass
    
    def validate(self, schema: DataSchema) -> bool:
        """验证数据格式"""
        pass

# 实现类
class CSVSource(DataSource):
    def __init__(self, path: str):
        self.path = path

class ExcelSource(DataSource):
    def __init__(self, path: str, sheet: str = None):
        self.path = path
        self.sheet = sheet

class GoogleSheetsSource(DataSource):
    def __init__(self, url: str, credentials: dict):
        self.url = url
        self.credentials = credentials

class APIDataSource(DataSource):
    def __init__(self, endpoint: str, params: dict):
        self.endpoint = endpoint
        self.params = params

class InlineDataSource(DataSource):
    """内联数据（JSON/Dict）"""
    def __init__(self, data: dict | list):
        self.data = data
```

### 3. 图表工厂 (Chart Factory)

**目标**: 统一图表创建接口

```python
# 重构：core/viz/chart_factory.py
class ChartFactory:
    """图表工厂"""
    
    @staticmethod
    def create(
        chart_type: str,
        data: pd.DataFrame,
        config: ChartConfig,
        backend: str = "plotly"
    ) -> Chart:
        """创建图表"""
        
        chart_classes = {
            "bar": BarChart,
            "line": LineChart,
            "scatter": ScatterChart,
            "area": AreaChart,
            "pie": PieChart,
            "heatmap": HeatmapChart,
            "bubble": BubbleChart,
            "radar": RadarChart,
        }
        
        ChartClass = chart_classes.get(chart_type)
        if not ChartClass:
            raise ValueError(f"Unknown chart type: {chart_type}")
        
        return ChartClass(data, config, backend)
```

### 4. 品牌系统 (Brand System)

**目标**: 支持企业品牌定制

```python
# 新增：core/brand/style.py
class BrandStyle:
    """品牌风格"""
    
    def __init__(
        self,
        name: str,
        colors: ColorPalette,
        fonts: FontPair,
        logo: Optional[str] = None,
        watermark: Optional[str] = None
    ):
        self.name = name
        self.colors = colors
        self.fonts = fonts
        self.logo = logo
        self.watermark = watermark

class ColorPalette:
    """颜色调色板"""
    
    def __init__(
        self,
        primary: str,
        secondary: str,
        accent: str,
        background: str = "#FFFFFF",
        text: str = "#000000",
        charts: List[str] = None
    ):
        self.primary = primary
        self.secondary = secondary
        self.accent = accent
        self.background = background
        self.text = text
        self.charts = charts or []

class FontPair:
    """字体配对"""
    
    def __init__(
        self,
        heading: str,
        body: str,
        mono: str = None
    ):
        self.heading = heading  # 标题字体
        self.body = body        # 正文字体
        self.mono = mono        # 等宽字体（代码/数据）

# 预定义品牌主题
BRAND_THEMES = {
    "default": BrandStyle(...),
    "corporate": BrandStyle(...),  # 企业风格
    "minimalist": BrandStyle(...),  # 极简风格
    "vibrant": BrandStyle(...),     # 鲜艳风格
    "new_york_times": BrandStyle(...),  # NYT 风格
    "financial_times": BrandStyle(...), # FT 风格
}
```

### 5. 叙事编排 (Story Orchestration)

**目标**: 实现交互式叙事能力

```python
# 新增：core/story/orchestrator.py
class StoryOrchestrator:
    """叙事编排器"""
    
    def __init__(self):
        self.scenes: List[Scene] = []
        self.transitions: List[Transition] = []
    
    def add_scene(self, scene: Scene) -> 'StoryOrchestrator':
        """添加场景"""
        self.scenes.append(scene)
        return self
    
    def add_transition(
        self,
        from_scene: str,
        to_scene: str,
        transition_type: str = "fade",
        duration: float = 1.0
    ) -> 'StoryOrchestrator':
        """添加转场"""
        self.transitions.append(Transition(
            from_scene=from_scene,
            to_scene=to_scene,
            transition_type=transition_type,
            duration=duration
        ))
        return self
    
    def build(self) -> StoryManifest:
        """构建故事清单"""
        return StoryManifest(
            scenes=self.scenes,
            transitions=self.transitions
        )

class Scene:
    """场景"""
    
    def __init__(
        self,
        id: str,
        title: str,
        chart: Chart,
        annotations: List[Annotation] = None,
        duration: float = 3.0,
        camera: CameraPath = None
    ):
        self.id = id
        self.title = title
        self.chart = chart
        self.annotations = annotations or []
        self.duration = duration
        self.camera = camera

class CameraPath:
    """摄像机路径"""
    
    def __init__(self):
        self.keyframes: List[CameraKeyframe] = []
    
    def add_keyframe(
        self,
        time: float,
        position: Tuple[float, float],
        zoom: float = 1.0,
        rotation: float = 0.0,
        easing: str = "ease_in_out"
    ):
        """添加摄像机关键帧"""
        self.keyframes.append(CameraKeyframe(
            time=time,
            position=position,
            zoom=zoom,
            rotation=rotation,
            easing=easing
        ))
```

---

## 🗂️ 新的项目结构

```
D:\PythonProject1/
├── core/                          # 核心业务逻辑
│   ├── templates/                 # 新增：模板引擎
│   │   ├── __init__.py
│   │   ├── base.py                # 模板基类
│   │   ├── bar_chart.py           # 柱状图模板
│   │   ├── line_chart.py          # 折线图模板
│   │   └── registry.py            # 模板注册表
│   │
│   ├── data/                      # 重构：数据层
│   │   ├── __init__.py
│   │   ├── sources.py             # 新增：数据源
│   │   ├── schema.py              # 数据模式
│   │   └── loader.py              # 数据加载器
│   │
│   ├── viz/                       # 重构：可视化
│   │   ├── __init__.py
│   │   ├── factory.py             # 图表工厂
│   │   ├── charts/                # 图表类型
│   │   │   ├── bar.py
│   │   │   ├── line.py
│   │   │   ├── scatter.py
│   │   │   └── ...
│   │   ├── backends/              # 渲染后端
│   │   │   ├── plotly_backend.py
│   │   │   ├── manim_backend.py
│   │   │   └── matplotlib_backend.py
│   │   └── components/            # 图表组件
│   │       ├── axes.py
│   │       ├── legend.py
│   │       └── annotations.py
│   │
│   ├── brand/                     # 新增：品牌系统
│   │   ├── __init__.py
│   │   ├── style.py               # 品牌风格
│   │   ├── themes.py              # 主题库
│   │   └── assets.py              # 品牌资产
│   │
│   ├── story/                     # 新增：叙事编排
│   │   ├── __init__.py
│   │   ├── orchestrator.py        # 编排器
│   │   ├── scene.py               # 场景
│   │   └── transition.py          # 转场
│   │
│   ├── camera/                    # 保留：摄像机
│   ├── animation/                 # 保留：动画
│   └── video/                     # 保留：视频处理
│
├── templates/                     # 新增：模板目录
│   ├── bar_chart_race/
│   ├── line_chart_animated/
│   └── scatter_plot_dynamic/
│
├── projects/                      # 精简：仅保留示例
│   ├── examples/                  # 示例项目
│   └── user_projects/             # 用户项目目录
│
├── platform/                      # 新增：平台规格
│   ├── __init__.py
│   ├── bilibili.py                # B 站规格
│   ├── douyin.py                  # 抖音规格
│   ├── xiaohongshu.py             # 小红书规格
│   └── youtube.py                 # YouTube 规格
│
├── api/                           # 重构：统一 API
│   ├── __init__.py
│   ├── routes/
│   │   ├── templates.py           # 模板 API
│   │   ├── data.py                # 数据 API
│   │   ├── render.py              # 渲染 API
│   │   └── publish.py             # 发布 API
│   └── middleware/
│
├── web/                           # 新增：Web 控制台
│   ├── dashboard.py               # 控制台后端
│   └── static/                    # 前端资源
│
├── cli/                           # 重构：命令行
│   ├── __init__.py
│   ├── commands/
│   │   ├── create.py              # 创建视频
│   │   ├── template.py            # 模板管理
│   │   ├── data.py                # 数据管理
│   │   └── publish.py             # 发布管理
│   └── main.py                    # CLI 入口
│
├── tests/                         # 测试
├── docs/                          # 文档
└── tools/                         # 工具
```

---

## 🚀 实施计划

### 阶段 1: 核心重构 (2 周)

- [ ] 创建模板引擎框架
- [ ] 实现数据源抽象层
- [ ] 重构图表工厂
- [ ] 建立品牌系统

### 阶段 2: 叙事能力 (1 周)

- [ ] 实现场景编排器
- [ ] 添加摄像机路径系统
- [ ] 创建转场效果库

### 阶段 3: API 与 CLI (1 周)

- [ ] 统一 RESTful API
- [ ] 重构命令行工具
- [ ] 添加批量处理能力

### 阶段 4: Web 控制台 (1 周)

- [ ] 现代化 Web UI
- [ ] 实时预览
- [ ] 拖拽式编辑器

### 阶段 5: 平台集成 (1 周)

- [ ] B 站/抖音/小红书规格
- [ ] 一键发布
- [ ] 数据分析

---

## 📊 关键指标

| 指标 | 当前 | 目标 | 提升 |
|------|------|------|------|
| 图表类型 | 4 种 | 15 种 | +275% |
| 数据源 | 1 种 | 5 种 | +400% |
| 模板数量 | 0 个 | 20 个 | +∞ |
| 品牌主题 | 1 个 | 10 个 | +900% |
| 发布渠道 | 本地 | 5 平台 | +400% |
| API 覆盖 | 30% | 90% | +200% |

---

## ✅ 验收标准

- [ ] 模板系统支持 20+ 图表类型
- [ ] 数据源支持 CSV/Excel/API/Google Sheets
- [ ] 品牌系统支持自定义颜色/字体/Logo
- [ ] 叙事编排支持多场景 + 转场
- [ ] API 覆盖所有核心功能
- [ ] CLI 支持完整工作流
- [ ] Web 控制台支持实时预览
- [ ] 一键发布到 5+ 平台

---

*重构方案 v2.0 - 对标 Flourish*
