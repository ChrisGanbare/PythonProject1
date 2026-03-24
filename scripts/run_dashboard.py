#!/usr/bin/env python
"""
Dashboard 启动脚本

用于启动 Web 控制台，提供项目管理和任务调度功能。

使用方式:
    python scripts/run_dashboard.py
    
访问地址:
    http://localhost:8090
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    # 直接运行 dashboard 模块
    from scripts import dashboard
    dashboard.main()
