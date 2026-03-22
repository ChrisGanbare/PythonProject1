# 数据可视化视频：定位与重构方向

> **使用与安装入口**：仓库根目录 [README.md](../README.md)。  
> **产品战略（与通用视频 AI 的差异、护城河、设计原则）见 [PRODUCT_STRATEGY.md](./PRODUCT_STRATEGY.md)。本文档侧重工程架构与落地阶段。**  
> **遇阻塞时的质量参照**：见 [PRODUCT_STRATEGY.md § 阻塞与对标](./PRODUCT_STRATEGY.md#阻塞与对标头部作品作参照系)（对标数据可视化头部作品的清晰度与节奏，而非替代创意工具）。

## 定位（North Star）

**以 Python 可视化栈为核心，把「数据 → 图表动画 → 平台成片」做成可复用流水线**，服务自媒体创作者更快产出结构清晰、数据可信的短视频；剧本 / AI / 素材库是增效层，不替代「图表与数据」这一主航道。

## 子项目在仓库中的角色

随仓库提供的 `projects/*` 目录是**参考实现**（题材、数据域、渲染实现深度可不同），**不**构成与「日后新建项目」相异的特例规则。统一约定见根目录 [README.md § 统一业务流程](../README.md#统一业务流程所有子项目共用)；下文中的「贷款 / 基金」等仅作**落地示例**，分层与契约适用于**任意**子项目。

## 现状与缺口

| 已有能力 | 缺口 |
|----------|------|
| 子项目 manifest + 调度器 | `shared/visualization/` 仅脚手架，未形成统一抽象 |
| 各项目 `renderer/impl.py`（如 matplotlib） | 缺少跨项目的 **Chart/Frame 契约** 与 **后端可插拔** |
| 平台预设、质量档、剧本库、素材注册表 | 剧本与 **图表规格** 未稳定绑定（如 scene → chart_id） |
| FFmpeg / VideoEditor 后处理 | 数据管线（清洗→聚合）与渲染参数分散 |

## 目标架构（四层）

```text
数据与规格层    DatasetSpec / ChartRecipe / 时间轴关键帧
      ↓
渲染后端层      MatplotlibBackend | PlotlyStatic | ManimScene（可选）
      ↓
合成与平台层    分辨率·安全区·字幕·BGM·成片 manifest
      ↓
创作者工作流层   剧本版本·定稿·任务·素材复用（已实现雏形）
```

**原则**：业务项目（`projects/*`）只声明「讲什么数据、用什么图、多长」；**具体绑 PIL/matplotlib 实现** 仍在各项目 `renderer`，但通过 **共享协议** 收敛接口，避免每个项目各写一套 env 传参。

## 分阶段重构（建议优先级）

### P0 — 契约与目录（1～2 次迭代）

- 在 `shared/visualization/` 定义最小协议（建议命名）：
  - `FrameRequest`：分辨率、fps、帧索引、主题 token
  - `ChartLayer` 或 `VizSceneSpec`：图表类型、数据引用方式（内存 / 路径 / 内嵌小表）
  - `RenderBackend` 协议：`render_frame` / `render_clip`（由项目实现）
- **Scaffold**：`python scheduler.py scaffold ...` 已生成 `renderer/viz_backend.py` + manifest `capabilities.viz_backends`。

### P1 — 数据管线显式化

- **各项目约定**：在 `projects/<name>/data/pipeline.py`（或等价模块）提供面向可视化的数据出口，并与 manifest / 任务参数对齐。**示例**：贷款参考实现中的 `loan_params_for_viz` / `loan_summary_for_charts`；基金参考实现中的 `fund_params_for_viz` 与 `compute_fund_reproducibility_fingerprint`（域不同则指纹逻辑不同，但**模式**一致）。
- 单元测试优先覆盖：**数值正确性**（利息、还款计划等）再谈像素。

### P2 — 剧本与图表对齐

- `Scene.action_directives` 约定键：`viz_scene_id`、`chart_type`、`reference_style`（见 `screenplay.py`）；成片侧车 `render_manifest` 的 `viz.scene_refs` + **`reproducibility_fingerprint`**（贷款参数 + 关键视频参数 + 各场景 viz 绑定）已落地，便于审计与缓存身份。
- **贷款对比主图**：`viz_scene_id=loan_compare_main` 时，`chart_type` 映射到 `render_expression.layout.chart_focus`（`dual_cumulative`→`balanced`，`trend_gap`→`trend-gap` 等），见 `loan_comparison/renderer/viz_presets.py` 与 `impl.py` 中 `CHART_FOCUS`。
- **待加强**：字幕主时钟与图表轴完全对齐；更多 chart_type 与像素层一一对应。

### P3 — 性能与规模化

- **渲染指纹**：`generate_loan_animation` 向子进程设置 `VIDEO_RENDER_FINGERPRINT`（与 manifest `reproducibility_fingerprint` 同源），`impl.py` 启动时打印短前缀便于对日志。
- **缓存目录与逐帧恢复**：`render_cache_dir(project, fingerprint_hex)` → `runtime/cache/renders/<project>/<fp[:32]>/`；子进程设置 **`VIDEO_FRAME_CACHE_DIR`**（与指纹一致）。`shared.visualization.png_frame_cache` 提供 **`PngCachingFFMpegWriter`**（缺帧则绘制并写入 `frame_%06d.png`，已缓存帧直接管道 RGBA）与 **全量命中** 时用 ffmpeg 从 PNG 序列封装、跳过 `anim.save`。可用 **`VIDEO_FRAME_CACHE_DISABLE=1`** 关闭缓存读写。
- 大批量：多进程按 batch 拆帧（CLAUDE 已约定 >500 帧分批）。

## 扩展性预留

- **后端注册表**：`shared/visualization/registry.py` 默认注册 **matplotlib**（帧级数据图表最高效、与现有 impl 一致）；可选注册 `plotly_static`（`PlotlyStaticVizBackend`，需 `plotly+kaleido`）。子项目 manifest 可用 `capabilities.viz_backends` 声明支持项。
- **非图表层**：片头片尾、大字报仍走现有 `VideoEditor` + 素材库，与图表层解耦。

## 与现有模块的关系

| 模块 | 角色 |
|------|------|
| `scheduler.py` + `orchestrator/` | 发现项目、执行任务，不变 |
| `shared/platform/` | 平台规格单一事实来源 |
| `shared/library/` + 素材注册表 | 创作者资产与成片溯源 |
| `shared/content/screenplay*` | 叙事与节拍；`action_directives` 与 manifest `viz` 块对齐（持续收紧） |
| 各项目 `renderer/impl.py` | 短期仍为主体实现，逐步迁入协议方法 |

## 成功标准（可度量）

- 新项目从 scaffold 到首条「带数据图表」成片的路径 **文档化且 <1 天**。
- 同一组数据 + 同一 ChartRecipe，换平台预设 **只改配置不改绘图逻辑**（或仅改 DPI/字号）。
- 成片旁 manifest 可回答：**哪版数据、哪版剧本、哪套渲染参数**。
- **基金 HTTP API**：成片成功时写入 `*.render_manifest.json`，任务结果返回 `render_manifest_path` 与 `render_fingerprint`（与 CLI 子进程指纹同源逻辑）。

---

*本文件为架构共识，实现可分批落地；具体 Issue/PR 以任务为单位切分。*
