# video_project

根目录作为总调度层，统一管理多个子项目（当前包含 `PythonProject1`）。

## 文档入口

- 根目录仅保留本 `README.md` 作为唯一入口文档。

## 目标架构

- 根目录：调度/发现/执行子项目任务
- 子项目目录：业务代码、API、渲染逻辑
- 扩展方式：新增同级子项目时，仅需添加 `project_manifest.py`

## 当前目录

```text
video_project/
├─ orchestrator/                  # 根调度核心（发现 + 执行）
├─ scheduler.py                   # 根调度 CLI 入口
├─ src/
│  └─ PythonProject1/
│     ├─ project_manifest.py      # 子项目任务清单
│     ├─ entrypoints.py           # 子项目暴露给调度器的入口
│     ├─ main.py                  # FastAPI 服务
│     ├─ original_assets/         # 来自原仓库的原始代码副本
│     ├─ config/settings.py       # 配置（已改为项目相对路径）
│     ├─ models/
│     ├─ modules/
│     └─ utils/
├─ tests/
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
python scheduler.py run --project PythonProject1 --task smoke_check
python scheduler.py run --project PythonProject1 --task api
python scheduler.py run --project PythonProject1 --task loan_animation
python scheduler.py run --project PythonProject1 --task loan_animation --param output_file="runtime/outputs/custom.mp4" --param width=1080 --param height=1920 --param duration=30 --param fps=30
python scheduler.py run --project PythonProject1 --task api --param host="127.0.0.1" --param port=8000
python scheduler.py run-all
```

`loan_animation` 任务直接使用子项目本地的原始等价渲染实现（不桥接根目录脚本）。
支持参数：
- `output_file` 输出文件路径
- `width` 宽度像素
- `height` 高度像素
- `duration` 视频时长（秒）
- `fps` 帧率
- `loan_amount` 贷款金额（可选）
- `annual_rate` 年利率（可选）
- `loan_years` 贷款年限（可选）

## 执行方式（旧/新）

如果你习惯“直接运行子项目脚本”，用旧方式即可：

```bash
python src/PythonProject1/loan_animation_pro.py
```

如果你想走根目录统一调度（推荐后续多子项目扩展），用新方式：

```bash
python scheduler.py run --project PythonProject1 --task loan_animation
```

两种方式都会在 `runtime/outputs/` 生成 MP4 文件。

## 新增子项目（未来扩展）

1. 在 `src/YourProject/`（或 `projects/YourProject/`）创建子项目目录。
2. 增加 `project_manifest.py`，格式参考 `src/PythonProject1/project_manifest.py`。
3. 增加 `entrypoints.py`，把可执行任务封装成函数。
4. 运行 `python scheduler.py list` 验证是否被自动发现。

## 配置说明

路径已改为项目相对路径（默认写入 `runtime/`）：

- `VIDEO__OUTPUT_DIR=runtime/outputs`
- `API__PEXELS_CACHE_DIR=runtime/pexels_cache`
- `LOG__LOG_DIR=runtime/logs`
- `CACHE_DIR=runtime/cache`
- `TEMP_DIR=runtime/temp`

不再依赖 `D:/PythonProject1/...` 这种硬编码路径。

## 测试

```bash
pytest
```
