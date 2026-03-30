"""
ASGI 入口：``uvicorn dashboard:app``、``from dashboard import app, REPO_ROOT``。

实现位于 ``scripts.dashboard``；此处仅做路径准备与再导出。
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
_APP = REPO_ROOT / "app"
for _p in (_APP, _APP / "projects"):
    s = str(_p)
    if s not in sys.path:
        sys.path.insert(0, s)

from scripts.dashboard import app, run_dashboard

__all__ = ["app", "run_dashboard", "REPO_ROOT"]
