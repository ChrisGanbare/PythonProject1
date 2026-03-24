# 修复 Dashboard 启动问题

## 问题现象

Dashboard 启动后，前端检查任务时报错：
```
ERROR:dashboard:Inspection failed: Could not import module 'panel_tutor.entrypoints': No module named 'panel_tutor'
```

## 原因分析

`inspect_callable` 函数在检查任务时，尝试导入 `panel_tutor.entrypoints`，但 Python 路径中没有包含 `projects/` 目录。

## 解决方案

### 方案 1: 修改 dashboard.py (已实施)

在 dashboard.py 启动时添加 `projects/` 到 Python 路径：

```python
# 在 dashboard.py 的开头添加
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = PROJECT_ROOT / "projects"
if str(PROJECTS_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECTS_DIR))
```

### 方案 2: 使用 start.py 启动 (推荐)

```bash
python start.py dashboard
```

start.py 会自动设置正确的 Python 路径。

## 验证

启动 Dashboard 后，检查日志应该没有错误：
```
INFO:dashboard:Discovering projects...
INFO:dashboard:Studio control plane database ready.
```

访问 http://localhost:8090 应该可以正常创建项目。
