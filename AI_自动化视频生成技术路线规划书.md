# AI 自动化视频生成技术路线规划书 (V1.0)

> **文档目标**：为 AI 自动化流水线提供清晰的架构蓝图与核心技术参数指标，用于分析将项目从"脚本绘图"提升为"工业化视频生产线"的可参考技术解决方案。

---

## 一、核心架构设计 (The Pipeline)

整个流水线分为四个阶段，AI 需要在各阶段间传递结构化数据（JSON/XML）：

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   剧本层    │ →  │   代码层    │ →  │   渲染层    │ →  │   合成层    │
│  AI Agent   │    │  Code Gen   │    │ Rendering   │    │  FFmpeg     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

| 阶段 | 模块名称 | 核心职责 | 输出格式 |
|:---:|:---|:---|:---|
| **1** | 剧本层 (AI Agent) | 生成具备时间戳、视觉描述、核心数据的结构化剧本 | JSON/XML |
| **2** | 代码层 (Code Gen) | 根据选定框架，将剧本转化为可执行的绘图脚本或配置 | Python/TS |
| **3** | 渲染层 (Rendering Engine) | 执行代码，输出原始视频帧或视频流 | 视频帧/流 |
| **4** | 合成层 (FFmpeg/Post-process) | 音频对齐、特效叠加、最终转码 | MP4/MOV |

---

## 二、三大主流技术方案深度对比

| 维度 | 方案 A：学术逻辑流 (Manim) | 方案 B：Web 现代化流 (Remotion) | 方案 C：影视级 3D 流 (Blender) |
|:---|:---|:---|:---|
| **适用场景** | 数学推导、算法演示、逻辑架构 | 动态图表、SaaS 界面、商业报告 | 物理仿真、3D 工业、科幻视觉 |
| **开发语言** | Python | TypeScript (React) | Python (bpy) |
| **渲染驱动** | OpenGL / Cairo | WebGL / Chrome Headless | Cycles (光追) / Eevee |
| **先进生产力** | 自动对象平滑插值 (In-betweening) | 分布式云渲染 (几秒钟出片) | 真实的物理碰撞与材质系统 |

### 方案选型建议

| 如果你的需求是... | 推荐方案 | 理由 |
|:---|:---:|:---|
| 教学视频、数学公式动画 | **Manim** | 专为数学可视化设计，公式渲染精美 |
| 商业演示、数据看板 | **Remotion** | React 生态友好，组件化开发效率高 |
| 产品宣传片、3D 展示 | **Blender** | 电影级画质，物理引擎强大 |

---

## 三、必须明确的技术参数 (AI 统一处理指标)

为确保 AI 生成的代码能够稳定运行并达到商业标准，必须在提示词 (Prompt) 或配置文件中明确以下参数：

### 1. 渲染性能参数 (Performance Metrics)

| 参数 | 建议值 | 说明 |
|:---|:---|:---|
| **帧率 (FPS)** | 30fps (抖音/小红书) <br> 60fps (B站横屏/竖屏) | 平台硬性要求，见 `shared/platform/presets.py` |
| **分辨率** | 1920×1080 (B站横屏) <br> 1080×1920 (B站竖屏/抖音) <br> 1080×1350 (小红书) | 横屏 16:9 / 竖屏 9:16 / 小红书 4:5 |
| **单帧渲染时耗** | <1s/帧 (Matplotlib) <br> ~0.5s/帧 (Manim) | 监控代码执行效率，避免低效渲染 |

### 2. 视觉一致性参数 (Visual Identity)

| 参数 | 配置要求 | 说明 |
|:---|:---|:---|
| **色板 (Color Palette)** | 十六进制色值列表 | 确保 AI 生成的图表与剧本氛围统一 |
| **字体库 (Typography)** | 指定 TTF/OTF 路径 | 解决 Matplotlib 等库常见的中文乱码及美观问题 |
| **缓动函数 (Easing)** | ease-in-out-cubic (默认) <br> Linear / Bounce (特殊场景) | 视频“高级感”的核心，控制动画节奏 |

### 3. 物理/时间参数 (Temporal Logic)

| 参数 | 精度要求 | 说明 |
|:---|:---|:---|
| **持续时间 (Duration)** | 精确到毫秒 | 每一行代码对应的视觉元素在 Timeline 上的 Start/End 时间 |
| **同步位移 (Synchronization)** | 音频振幅 ↔ 视觉波动 | 如：根据音频强度触发图表跳动 |

### 4. 导出与兼容性 (Export Specs)

| 参数 | 推荐值 | 说明 |
|:---|:---|:---|
| **编码器 (Codec)** | H.264 (兼容性好) <br> H.265 (体积小) | 根据目标平台选择 |
| **像素格式 (Pixel Format)** | yuv420p (通用) <br> yuva420p (透明通道) | 需要透明背景时选后者 |
| **位速率 (Bitrate)** | 5Mbps - 20Mbps | 平衡清晰度与文件大小 |

---

## 四、自动化演进建议

### 📌 核心建议

| 建议 | 实施方案 | 收益 |
|:---|:---|:---|
| **数据协议化** | 让 AI 生成 Task JSON（包含数据点、时间轴、视觉样式），由固定底层模板脚本解析渲染 | 避免零散脚本，提高可维护性 |
| **反馈环 (Self-Correction)** | `shared/core/self_correction.py` — 渲染报错时自动分类错误、补丁参数、重试；`CorrectionReport` JSON 审计 | 实现自愈能力，减少人工干预 |
| **并行化预留** | 任务量大时，可按帧批次多进程渲染（>500 帧分批） | 充分利用多核 CPU |

### 🔄 演进路线图

```
Phase 1: 单脚本手动执行                         ✅ 已完成
    ↓
Phase 2: JSON 协议化 + 模板渲染                   ✅ 80% 完成（Screenplay/FrameRequest/RenderExpression）
    ↓
Phase 2.5: Self-Correction 反馈环 + Manim 后端  ✅ 已落地
    ↓
Phase 3: 本地多进程并行渲染                   ⭕ 待开始
    ↓
Phase 4: AI 辅助修正闭环（错误→AI分析→代码补丁）  ⭕ 待开始
```

---

## 附录：快速参考卡片

### 🎯 场景 → 方案速查

```
数学/算法演示  ──────────────────→ Manim
商业数据看板   ──────────────────→ Remotion
3D 产品宣传片  ──────────────────→ Blender
```

### ⚙️ 默认配置模板

```yaml
render:
  fps: 30  # 抖音/小红书； B站用 60
  resolution: 1080x1920  # 默认竖屏（抖音/B竖）
  codec: H.264
  bitrate: 10Mbps
  pixel_format: yuv420p

visual:
  easing: ease-in-out-cubic
  font: "Noto Sans SC"  # 或 Alibaba PuHuiTi
  color_palette: ["#1E90FF", "#32CD32", "#FF6347"]

self_correction:
  max_retries: 2
  backoff_base: 2.0
  auto_categories: [font_not_found, ffmpeg_error, out_of_memory, timeout, matplotlib_error]
```

---

> 📄 **版本**: V1.0  
> 📅 **最后更新**: 2026-03-23  
> 🍺 **BeerClaw** 整理排版
