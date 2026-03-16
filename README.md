# video_project

根目录作为总调度层，统一管理多个子项目（当前包含 `loan_comparison`）。

## 文档入口

- 根目录仅保留本 `README.md` 作为唯一入口文档。

## 目标架构

- `shared/`：公共库，所有子项目均可导入（配置、平台规格、工具函数等）
- `projects/`：各作品子项目，互相独立
- `assets/`：共享静态资源（字体、音乐、模板）
- 扩展方式：新增子项目时，在 `projects/` 下添加目录并创建 `project_manifest.py`

## 当前目录

```text
video_project/
├─ shared/                        # 公共库
│  ├─ config/settings.py          # 全局配置
│  ├─ platform/presets.py         # 平台规格（B站/抖音/小红书）
│  ├─ core/                       # 异常、任务管理
│  ├─ media/                      # FFmpeg 封装
│  └─ utils/                      # 工具函数
├─ assets/                        # 共享静态资源
├─ projects/
│  └─ loan_comparison/            # 贷款对比可视化子项目
│     ├─ project_manifest.py      # 子项目任务清单
│     ├─ entrypoints.py           # 暴露给调度器的入口
│     ├─ api/main.py              # FastAPI 服务
│     ├─ renderer/                # 动画渲染
│     ├─ models/                  # 数据模型
│     └─ tests/                   # 项目级测试
├─ orchestrator/                  # 根调度核心（发现 + 执行）
├─ scheduler.py                   # 根调度 CLI 入口
├─ tests/                         # 根级测试
├─ .env
└─ .env.example
```

## 调度器用法

先在项目根目录执行：

```bash
python scheduler.py list
```

查看到子项目后：

```bash
python scheduler.py run --project loan_comparison --task smoke_check
python scheduler.py run --project loan_comparison --task api
python scheduler.py run --project loan_comparison --task loan_animation
python scheduler.py run --project loan_comparison --task loan_animation --param output_file="runtime/outputs/custom.mp4" --param width=1080 --param height=1920 --param duration=30 --param fps=30
python scheduler.py run --project loan_comparison --task api --param host="127.0.0.1" --param port=8000
python scheduler.py run-all
```

`loan_animation` 任务支持参数：
- `output_file` 输出文件路径
- `width` 宽度像素
- `height` 高度像素
- `duration` 视频时长（秒）
- `fps` 帧率
- `loan_amount` 贷款金额（可选）
- `annual_rate` 年利率（可选）
- `loan_years` 贷款年限（可选）

## 新增子项目（未来扩展）

1. 在 `projects/YourProject/` 创建子项目目录。
2. 增加 `project_manifest.py`，格式参考 `projects/loan_comparison/project_manifest.py`。
3. 增加 `entrypoints.py`，把可执行任务封装成函数。
4. 运行 `python scheduler.py list` 验证是否被自动发现。

## 配置说明

路径已改为项目相对路径（默认写入 `runtime/`）：

- `VIDEO__OUTPUT_DIR=runtime/outputs`
- `API__PEXELS_CACHE_DIR=runtime/pexels_cache`
- `LOG__LOG_DIR=runtime/logs`
- `CACHE_DIR=runtime/cache`
- `TEMP_DIR=runtime/temp`

## 测试

```bash
pytest                                  # 全部测试
pytest projects/loan_comparison/tests/  # 仅 loan_comparison 项目
pytest tests/                           # 仅根级测试
```
