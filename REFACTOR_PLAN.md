# 🚀 数据可视化视频平台 2.0 — 重构计划

**对标产品**: Flourish + 数据新闻头部作品 (NYT, Financial Times, The Guardian)  
**目标用户**: 个人创作者 + 企业内容团队  
**产品定位**: 生成有深度见解、有权威性的参考价值视频

---

## 一、战略定位升级

### 1.1 与 Flourish 的差异化

| 维度 | Flourish | 本项目 2.0 |
|------|----------|-----------|
| **输出形式** | 交互式网页嵌入 | **视频成片 + 交互网页双输出** |
| **核心场景** | 通用数据展示 | **财经/科普/深度分析垂直领域** |
| **叙事能力** | 基础 scrollytelling | **AI 驱动的深度叙事 + 数据洞察** |
| **权威性** | 数据由用户提供 | **数据验证 + 来源追溯 + 可复现审计** |
| **平台适配** | 网页响应式 | **多视频平台规格原生适配** |

### 1.2 产品护城河

```
真值层 (Truth Layer)
    ↓
数据验证引擎 → 来源追溯 → 可复现审计
    ↓
深度洞察生成 → AI 分析趋势/异常/对比
    ↓
权威叙事模板 → 财经/科普/政策分析垂直领域
    ↓
多平台成片 → B 站/抖音/YouTube/企业内部分享
```

---

## 二、架构重构蓝图

### 2.1 新目录结构

```
video_project/
├── core/                          # 【新增】核心引擎层
│   ├── data/                      # 数据引擎
│   │   ├── loader.py              # 多源数据加载 (CSV/Excel/API/SQL)
│   │   ├── validator.py           # 数据验证与异常检测
│   │   ├── transformer.py         # 数据转换与聚合
│   │   └── source_tracker.py      # 数据来源追溯
│   │
│   ├── insight/                   # 【新增】洞察生成引擎
│   │   ├── trend_detector.py      # 趋势识别 (增长/下降/拐点)
│   │   ├── anomaly_detector.py    # 异常值检测
│   │   ├── comparison_engine.py   # 对比分析引擎
│   │   ├── correlation_finder.py  # 相关性发现
│   │   └── insight_generator.py   # 自然语言洞察生成
│   │
│   ├── narrative/                 # 叙事引擎
│   │   ├── story_architect.py     # 故事结构设计
│   │   ├── hook_generator.py      # 开场钩子生成
│   │   ├── pacing_engine.py       # 节奏控制
│   │   └── authority_scorer.py    # 权威性评分
│   │
│   └── viz/                       # 可视化引擎 (重构)
│       ├── components/            # 【新增】通用图表组件库
│       │   ├── base.py            # 图表基类
│       │   ├── bar_chart.py       # 柱状图 (支持堆叠/分组)
│       │   ├── line_chart.py      # 折线图 (多轴/面积)
│       │   ├── pie_chart.py       # 饼图/环形图
│       │   ├── scatter_plot.py    # 散点图 + 回归线
│       │   ├── heatmap.py         # 热力图
│       │   ├── radar_chart.py     # 雷达图
│       │   ├── sankey.py          # 桑基图
│       │   └── chart_factory.py   # 工厂模式创建
│       │
│       ├── camera/                # 【新增】摄像机系统
│       │   ├── transform.py       # 缩放/平移/旋转
│       │   ├── keyframe.py        # 关键帧管理
│       │   └── motion_path.py     # 运动路径
│       │
│       ├── effects/               # 【新增】特效层
│       │   ├── blur.py            # 高斯模糊
│       │   ├── glow.py            # 发光效果
│       │   ├── particles.py       # 粒子系统
│       │   └── transitions.py     # 转场特效
│       │
│       └── backends/              # 后端 (保留并扩展)
│           ├── matplotlib_backend.py
│           ├── manim_backend.py
│           └── plotly_backend.py  # 【新增】
│
├── templates/                     # 【新增】模板系统
│   ├── verticals/                 # 垂直领域模板
│   │   ├── finance/               # 财经
│   │   │   ├── earnings_report.py # 财报分析
│   │   │   ├── market_trend.py    # 市场趋势
│   │   │   └── comparison.py      # 产品对比
│   │   ├── science/               # 科普
│   │   │   ├── research_summary.py
│   │   │   └── data_explainer.py
│   │   └── policy/                # 政策分析
│   │       ├── policy_impact.py
│   │       └── regional_comparison.py
│   │
│   ├── styles/                    # 视觉风格模板
│   │   ├── minimal.py
│   │   ├── tech.py
│   │   ├── news.py
│   │   └── corporate.py           # 【新增】企业风格
│   │
│   └── marketplace/               # 【新增】模板市场
│       ├── registry.py
│       └── sharing.py
│
├── projects/                      # 子项目 (保留，改为模板实例)
│   └── ...                        # 现有项目迁移为模板示例
│
├── platform/                      # 平台适配 (保留并扩展)
│   ├── presets.py                 # 平台规格
│   ├── audio/                     # 【新增】音频处理
│   │   ├── bpm_detector.py        # BPM 检测
│   │   ├── waveform_viz.py        # 波形可视化
│   │   └── beat_sync.py           # 节拍对齐
│   │
│   └── export/                    # 导出
│       ├── video.py               # 视频导出
│       └── interactive.py         # 【新增】交互式网页导出
│
├── studio/                        # 控制面 (保留并升级)
│   ├── api/                       # API v2
│   ├── db/                        # 数据库
│   └── ui/                        # 【新增】前端重构
│
├── shared/                        # 共享工具 (逐步迁移至 core/)
├── tests/                         # 测试
└── runtime/                       # 运行时
```

### 2.2 核心模块依赖关系

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (Applications)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  CLI 调度器   │  │  Web 控制台  │  │  HTTP API   │      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
└─────────┼────────────────┼────────────────┼─────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼─────────────┐
│                   编排层 (Orchestration)                  │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Pipeline Orchestrator              │    │
│  │  数据加载 → 验证 → 洞察生成 → 叙事构建 → 渲染 → 导出  │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼─────────────┐
│                    引擎层 (Engines)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  数据引擎     │  │  洞察引擎      │  │  叙事引擎      │   │
│  │  - 加载       │  │  - 趋势检测    │  │  - 故事结构    │   │
│  │  - 验证       │  │  - 异常检测    │  │  - 钩子生成    │   │
│  │  - 转换       │  │  - 对比分析    │  │  - 节奏控制    │   │
│  │  - 追溯       │  │  - 洞察生成    │  │  - 权威性评分  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼─────────────┐
│                  渲染层 (Rendering)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  图表组件库    │  │  摄像机系统   │  │  特效层       │   │
│  │  - 10+ 图表    │  │  - 缩放平移   │  │  - 转场       │   │
│  │  - 主题系统    │  │  - 关键帧     │  │  - 粒子       │   │
│  │  - 自适应布局  │  │  - 运动路径   │  │  - 模糊发光    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼─────────────┐
│                   导出层 (Export)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  视频导出     │  │  交互网页     │  │  多平台适配    │   │
│  │  - FFmpeg    │  │  - HTML/JS   │  │  - B 站/抖音   │   │
│  │  - 字幕/BGM   │  │  - 可嵌入     │  │  - YouTube    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 三、核心能力升级详解

### 3.1 数据引擎升级

#### 现状
```python
# 硬编码数据
LOAN_AMOUNT = 1000000
ANNUAL_RATE = 0.045
```

#### 2.0 版本
```python
# core/data/loader.py
from typing import Protocol
import pandas as pd

class DataSource(Protocol):
    def load(self) -> pd.DataFrame: ...
    def validate(self) -> list[str]: ...
    def get_metadata(self) -> dict: ...

class CSVSource:
    def __init__(self, path: str, encoding: str = "utf-8"):
        self.path = path
    
    def load(self) -> pd.DataFrame:
        return pd.read_csv(self.path, encoding=self.encoding)
    
    def get_metadata(self) -> dict:
        return {
            "source_type": "csv",
            "path": self.path,
            "loaded_at": datetime.utcnow().isoformat()
        }

class APISource:
    def __init__(self, url: str, headers: dict = None):
        self.url = url
        self.headers = headers
    
    def load(self) -> pd.DataFrame:
        response = requests.get(self.url, headers=self.headers)
        return pd.DataFrame(response.json())

class SQLSource:
    def __init__(self, connection_string: str, query: str):
        self.connection_string = connection_string
        self.query = query
    
    def load(self) -> pd.DataFrame:
        return pd.read_sql(self.query, self.connection_string)

# 使用示例
from core.data import DataSourceRegistry

registry = DataSourceRegistry()
registry.register("csv", CSVSource)
registry.register("api", APISource)
registry.register("sql", SQLSource)

# 通过配置选择数据源
config = {
    "source_type": "api",
    "source_config": {
        "url": "https://api.example.com/market-data",
        "headers": {"Authorization": "Bearer xxx"}
    }
}

df = registry.create(config["source_type"], **config["source_config"]).load()
```

### 3.2 洞察生成引擎 (新增)

```python
# core/insight/insight_generator.py
from dataclasses import dataclass
from enum import Enum

class InsightType(str, Enum):
    TREND = "trend"           # 趋势类
    ANOMALY = "anomaly"       # 异常类
    COMPARISON = "comparison" # 对比类
    CORRELATION = "correlation" # 相关类
    FORECAST = "forecast"     # 预测类

@dataclass
class Insight:
    type: InsightType
    confidence: float         # 置信度 0-1
    description: str          # 自然语言描述
    data_evidence: dict       # 支撑数据
    visual_suggestion: str    # 可视化建议
    authority_score: float    # 权威性评分 0-10

class InsightEngine:
    def __init__(self):
        self.trend_detector = TrendDetector()
        self.anomaly_detector = AnomalyDetector()
        self.comparison_engine = ComparisonEngine()
    
    def analyze(self, df: pd.DataFrame, context: dict = None) -> list[Insight]:
        insights = []
        
        # 趋势检测
        trend_insights = self.trend_detector.detect(df)
        insights.extend(trend_insights)
        
        # 异常检测
        anomaly_insights = self.anomaly_detector.detect(df)
        insights.extend(anomaly_insights)
        
        # 对比分析
        if context and "baseline" in context:
            comparison_insights = self.comparison_engine.compare(
                df, 
                baseline=context["baseline"]
            )
            insights.extend(comparison_insights)
        
        # 按置信度和权威性排序
        insights.sort(key=lambda x: (x.confidence * x.authority_score), reverse=True)
        
        return insights[:10]  # 返回 top 10 洞察

# 使用示例
engine = InsightEngine()
insights = engine.analyze(df, context={"baseline": historical_data})

for insight in insights:
    print(f"[{insight.type.upper()}] {insight.description}")
    print(f"  置信度：{insight.confidence:.2f}, 权威性：{insight.authority_score:.1f}/10")
    print(f"  建议可视化：{insight.visual_suggestion}")
```

### 3.3 通用图表组件库 (新增)

```python
# core/viz/components/chart_factory.py
from typing import Type
from .base import ChartBase

class ChartFactory:
    _registry: dict[str, Type[ChartBase]] = {}
    
    @classmethod
    def register(cls, chart_type: str, chart_class: Type[ChartBase]):
        cls._registry[chart_type] = chart_class
    
    @classmethod
    def create(cls, chart_type: str, **kwargs) -> ChartBase:
        if chart_type not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(f"Unknown chart type: {chart_type}. Available: {available}")
        return cls._registry[chart_type](**kwargs)
    
    @classmethod
    def list_types(cls) -> list[str]:
        return list(cls._registry.keys())

# 注册图表类型
ChartFactory.register("bar", BarChart)
ChartFactory.register("bar_stacked", StackedBarChart)
ChartFactory.register("line", LineChart)
ChartFactory.register("area", AreaChart)
ChartFactory.register("pie", PieChart)
ChartFactory.register("donut", DonutChart)
ChartFactory.register("scatter", ScatterPlot)
ChartFactory.register("heatmap", Heatmap)
ChartFactory.register("radar", RadarChart)
ChartFactory.register("sankey", SankeyDiagram)

# 使用示例
from core.viz.components import ChartFactory

# 创建堆叠柱状图
chart = ChartFactory.create(
    "bar_stacked",
    data=df,
    x_column="category",
    y_columns=["value_a", "value_b", "value_c"],
    theme="tech_blue",
    animation="grow_vertical"
)

# 渲染单帧
frame = chart.render_frame(frame_index=42, total_frames=300)

# 或生成完整动画
chart.animate(
    output_path="output.mp4",
    fps=30,
    duration=10
)
```

### 3.4 摄像机系统 (新增)

```python
# core/viz/camera/transform.py
from dataclasses import dataclass
from enum import Enum

class MotionType(str, Enum):
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    PAN_UP = "pan_up"
    PAN_DOWN = "pan_down"
    ROTATE = "rotate"
    CUSTOM = "custom"

@dataclass
class CameraState:
    x: float = 0.0        # 平移 X
    y: float = 0.0        # 平移 Y
    zoom: float = 1.0     # 缩放
    rotation: float = 0.0 # 旋转角度
    focus: tuple = None   # 焦点坐标

class Camera:
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
        self.state = CameraState()
        self.keyframes: list[tuple[int, CameraState]] = []
    
    def add_keyframe(self, frame: int, state: CameraState):
        self.keyframes.append((frame, state))
        self.keyframes.sort(key=lambda x: x[0])
    
    def get_state_at_frame(self, frame: int) -> CameraState:
        if not self.keyframes:
            return self.state
        
        # 找到前后关键帧
        before = None
        after = None
        for kf_frame, kf_state in self.keyframes:
            if kf_frame <= frame:
                before = (kf_frame, kf_state)
            if kf_frame > frame and after is None:
                after = (kf_frame, kf_state)
                break
        
        # 插值计算
        if before is None:
            return after[1]
        if after is None:
            return before[1]
        
        t = (frame - before[0]) / (after[0] - before[0])
        t = self._ease_in_out_cubic(t)
        
        return self._interpolate(before[1], after[1], t)
    
    def _ease_in_out_cubic(self, t: float) -> float:
        if t < 0.5:
            return 4 * t * t * t
        return 1 - pow(-2 * t + 2, 3) / 2
    
    def _interpolate(self, start: CameraState, end: CameraState, t: float) -> CameraState:
        return CameraState(
            x=start.x + (end.x - start.x) * t,
            y=start.y + (end.y - start.y) * t,
            zoom=start.zoom + (end.zoom - start.zoom) * t,
            rotation=start.rotation + (end.rotation - start.rotation) * t,
            focus=self._interpolate_tuple(start.focus, end.focus, t)
        )
    
    def _interpolate_tuple(self, start, end, t):
        if start is None or end is None:
            return end if end is not None else start
        return (start[0] + (end[0] - start[0]) * t, 
                start[1] + (end[1] - start[1]) * t)

# 使用示例
camera = Camera(width=1920, height=1080)

# 定义摄像机运动
camera.add_keyframe(0, CameraState(zoom=1.0, x=0, y=0))
camera.add_keyframe(30, CameraState(zoom=1.5, x=100, y=50))  # 30 帧后放大并平移
camera.add_keyframe(60, CameraState(zoom=1.0, x=0, y=0))     # 60 帧后恢复

# 在渲染循环中使用
for frame in range(90):
    state = camera.get_state_at_frame(frame)
    apply_camera_transform(state)
```

### 3.5 模板系统 (新增)

```python
# templates/verticals/finance/earnings_report.py
from core.pipeline import VideoPipeline
from core.insight import InsightEngine
from core.viz.components import ChartFactory

class EarningsReportTemplate:
    """财报分析视频模板"""
    
    NAME = "财报分析"
    DESCRIPTION = "自动生成公司财报对比分析视频"
    VERTICAL = "finance"
    
    def __init__(self, config: dict):
        self.config = config
        self.insight_engine = InsightEngine()
    
    def build_pipeline(self, data_source) -> VideoPipeline:
        pipeline = VideoPipeline()
        
        # 加载数据
        df = data_source.load()
        
        # 生成洞察
        insights = self.insight_engine.analyze(df)
        
        # 场景 1: 开场概览
        pipeline.add_scene(
            duration=5,
            elements=[
                ChartFactory.create(
                    "bar_stacked",
                    data=df[["revenue", "profit"]],
                    title="营收与利润概览"
                ),
                TextOverlay(
                    text=insights[0].description,
                    position="bottom"
                )
            ]
        )
        
        # 场景 2: 趋势分析
        pipeline.add_scene(
            duration=8,
            elements=[
                ChartFactory.create(
                    "line",
                    data=df[["quarter", "revenue"]],
                    title="营收趋势",
                    show_markers=True,
                    trend_line=True
                )
            ],
            camera_motion="pan_right"
        )
        
        # 场景 3: 对比分析
        if "competitor_data" in self.config:
            pipeline.add_scene(
                duration=6,
                elements=[
                    ChartFactory.create(
                        "radar",
                        data=self._build_comparison_data(df),
                        title="竞争力对比"
                    )
                ]
            )
        
        # 场景 4: 结论
        pipeline.add_scene(
            duration=4,
            elements=[
                ConclusionCard(
                    title="核心结论",
                    points=[i.description for i in insights[:3]],
                    authority_score=insights[0].authority_score
                )
            ]
        )
        
        return pipeline

# 使用示例
from templates.verticals.finance import EarningsReportTemplate

template = EarningsReportTemplate({
    "company": "AAPL",
    "quarters": 8,
    "competitors": ["MSFT", "GOOGL"]
})

pipeline = template.build_pipeline(
    APISource(url="https://api.example.com/earnings/AAPL")
)

video = pipeline.render(output="aapl_earnings.mp4")
```

---

## 四、迁移计划

### 4.1 阶段划分

| 阶段 | 时间 | 目标 | 风险 |
|------|------|------|------|
| **Phase 0** | 第 1 周 | 搭建新架构骨架，保留现有代码 | 低 |
| **Phase 1** | 第 2-3 周 | 数据引擎 + 洞察引擎 | 中 |
| **Phase 2** | 第 4-6 周 | 图表组件库 (5 种核心图表) | 中 |
| **Phase 3** | 第 7-8 周 | 摄像机系统 + 特效层 | 中 |
| **Phase 4** | 第 9-10 周 | 模板系统 (3 个垂直领域) | 高 |
| **Phase 5** | 第 11-12 周 | 控制台重构 + API v2 | 高 |
| **Phase 6** | 第 13 周 | 迁移现有项目，完整测试 | 中 |

### 4.2 向后兼容策略

```python
# 兼容层：旧项目可继续运行
class LegacyAdapter:
    """将旧项目适配到新架构"""
    
    def __init__(self, legacy_project_path: str):
        self.legacy_path = legacy_project_path
        self._load_legacy_manifest()
    
    def to_new_pipeline(self) -> VideoPipeline:
        """转换为新 Pipeline 格式"""
        pipeline = VideoPipeline()
        
        # 解析旧项目的 entrypoints.py
        # 映射到新的 Scene/Element 结构
        
        return pipeline
```

---

## 五、成功指标

### 5.1 技术指标

| 指标 | 当前 | 目标 | 测量方式 |
|------|------|------|----------|
| 图表类型数量 | 2 | 10+ | 组件库计数 |
| 单文件最大行数 | 1200+ | <300 | 代码分析 |
| 测试覆盖率 | 65% | 85% | pytest-cov |
| 渲染性能 (1080p/30s) | ~2 分钟 | <45 秒 | 基准测试 |
| 内存峰值 | ~2GB | <800MB | 性能分析 |

### 5.2 产品指标

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| 模板数量 | 15+ | 模板市场计数 |
| 垂直领域覆盖 | 3+ | 财经/科普/政策 |
| 从数据到成片时间 | <5 分钟 | 用户测试 |
| 权威性评分 | 8+/10 | 专家评审 |
| 用户满意度 | 4.5/5 | 用户调研 |

---

## 六、立即行动项

### 6.1 本周启动 (Phase 0)

```bash
# 1. 创建新目录结构
mkdir -p core/{data,insight,narrative,viz/{components,camera,effects}}
mkdir -p templates/{verticals/{finance,science,policy},styles,marketplace}

# 2. 初始化核心模块
touch core/__init__.py
touch core/data/{loader,validator,transformer,source_tracker}.py
touch core/insight/{trend_detector,anomaly_detector,comparison_engine,insight_generator}.py
touch core/viz/components/{base,bar_chart,line_chart,chart_factory}.py
touch core/viz/camera/{transform,keyframe,motion_path}.py

# 3. 创建基础测试
mkdir -p tests/core/{data,insight,viz}
```

### 6.2 首批代码文件

我将按以下顺序生成代码：

1. `core/data/loader.py` - 数据加载协议与实现
2. `core/insight/insight_generator.py` - 洞察生成引擎
3. `core/viz/components/base.py` - 图表基类
4. `core/viz/components/bar_chart.py` - 柱状图组件
5. `core/viz/camera/transform.py` - 摄像机系统
6. `templates/verticals/finance/earnings_report.py` - 首个垂直模板

---

## 七、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 重构期间现有功能回归 | 高 | 保留兼容层，双轨运行 4 周 |
| 新图表组件性能不达标 | 中 | 早期性能测试，设定基准 |
| 模板开发进度延迟 | 中 | 优先完成 3 个核心模板 |
| 学习曲线陡峭 | 低 | 详细文档 + 示例项目 |

---

## 八、附录：Flourish 核心能力对照表

| Flourish 能力 | 本项目 2.0 实现 | 优先级 |
|--------------|----------------|--------|
| 模板系统 | `templates/` + 模板市场 | P0 |
| Scrollytelling | `core/narrative/pacing_engine.py` | P1 |
| 交互式网页导出 | `platform/export/interactive.py` | P1 |
| SDK 自定义模板 | `core/viz/components/` 可扩展架构 | P0 |
| 多语言支持 | 待实现 (i18n 框架) | P2 |
| 移动端优化 | `platform/presets.py` 已支持 | P0 |
| 嵌入选项 | 交互式导出支持 | P1 |
| 数据叙事 | `core/insight/` + `core/narrative/` | P0 |

---

**下一步**: 请确认此重构计划是否符合您的预期，我将开始生成 Phase 0 的核心代码文件。
