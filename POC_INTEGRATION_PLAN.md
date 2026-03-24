# POC 代码整合计划

**日期**: 2026-03-24  
**目标**: 将 POC 验证代码整合到 D:\PythonProject1 主项目

---

## 📋 整合策略

### 现有项目结构

```
D:\PythonProject1/
├── shared/          # 公共库
├── projects/        # 子项目
├── core/            # 核心模块
├── orchestrator/    # 编排层
├── runtime/         # 运行时
├── tools/           # 工具集
└── docs/            # 文档
```

### POC 代码映射

| POC 模块 | 目标位置 | 说明 |
|----------|----------|------|
| `src/visualizer/` | `shared/visualization/` | 可视化模块提升为共享库 |
| `src/camera/` | `core/camera/` | 摄像机系统作为核心模块 |
| `src/animation/` | `core/animation/` | 动画引擎作为核心模块 |
| `src/video/` | `core/video/` | 视频处理作为核心模块 |
| `deploy.py` | `tools/deploy.py` | 部署工具 |
| `docker/` | `docker/` | Docker 配置合并 |
| `docs/` | `docs/POC/` | POC 文档归档 |

---

## 🚀 整合步骤

### 步骤 1: 创建共享可视化模块

```bash
# 目标：shared/visualization/
- __init__.py
- plotly_viz.py       # 从 POC 迁移
- chart_presets.py    # 新增：预设图表模板
```

### 步骤 2: 创建核心摄像机模块

```bash
# 目标：core/camera/
- __init__.py
- controller.py       # 基础摄像机控制器
- manim_adapter.py    # Manim 适配器
- paths.py            # 新增：摄像机路径系统
```

### 步骤 3: 创建核心动画引擎

```bash
# 目标：core/animation/
- __init__.py
- timeline.py         # 时间轴系统
- easing.py           # 缓动函数库 (分离)
- tracks.py           # 轨道系统 (分离)
- presets.py          # 新增：动画预设
```

### 步骤 4: 增强视频处理模块

```bash
# 目标：core/video/
- __init__.py
- composer.py         # 视频合成器
- ffmpeg_wrapper.py   # FFmpeg 封装
- batch_processor.py  # 批量处理
```

### 步骤 5: 更新依赖

```bash
# 更新 requirements.txt
# 合并 POC 依赖到主项目
```

### 步骤 6: 集成测试

```bash
# 创建 tests/test_poc_integration.py
# 验证 POC 功能在主项目中正常工作
```

---

## 📦 依赖整合

### 新增依赖

```txt
# 可视化
plotly>=5.18.0
kaleido>=0.2.1

# 动画
manim>=0.18.0

# 视频处理
moviepy>=2.0.0
imageio-ffmpeg>=0.4.8
```

### 现有依赖检查

确保与以下依赖兼容：
- numpy
- pandas
- Pillow
- pytest

---

## 🧪 测试策略

### 单元测试

- 迁移 POC 测试到 `tests/`
- 保持 100% 通过率
- 新增集成测试

### 集成测试

- 测试 POC 模块与现有代码的集成
- 测试完整工作流

### 性能测试

- 验证性能指标 (10,000+ FPS)
- 基准测试

---

## 📝 文档更新

### 新增文档

- `docs/POC/README.md` - POC 文档归档
- `docs/VISUALIZATION.md` - 可视化模块文档
- `docs/ANIMATION.md` - 动画引擎文档
- `docs/VIDEO_PROCESSING.md` - 视频处理文档

### 更新文档

- `README.md` - 添加新模块说明
- `docs/DATA_VIZ_VIDEO_ARCHITECTURE.md` - 更新架构

---

## ⏱️ 时间表

| 步骤 | 预计时间 | 状态 |
|------|----------|------|
| 1. 可视化模块 | 30 分钟 | ⏳ |
| 2. 摄像机模块 | 30 分钟 | ⏳ |
| 3. 动画引擎 | 45 分钟 | ⏳ |
| 4. 视频处理 | 30 分钟 | ⏳ |
| 5. 依赖整合 | 15 分钟 | ⏳ |
| 6. 集成测试 | 45 分钟 | ⏳ |
| **总计** | **3 小时 15 分** | |

---

## ✅ 验收标准

- [ ] 所有 POC 功能正常工作
- [ ] 测试通过率 100%
- [ ] 性能指标达标
- [ ] 文档完整
- [ ] 依赖无冲突
- [ ] Docker 构建成功

---

*整合计划 v1.0*
