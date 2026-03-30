"""
ASGI/CLI 入口：``python scheduler.py`` 或 ``from scheduler import build_parser, scaffold_project``。

实现位于 ``scripts.scheduler``；此处仅做路径准备与再导出（与 dashboard.py 同模式）。
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

from scripts.scheduler import (  # noqa: E402
    build_parser,
    generate_project_scaffold,
    main,
    print_backends,
    print_projects,
    run_all,
    run_single,
    scaffold_project,
)

__all__ = [
    "build_parser",
    "generate_project_scaffold",
    "main",
    "print_backends",
    "print_projects",
    "run_all",
    "run_single",
    "scaffold_project",
]

if __name__ == "__main__":
    raise SystemExit(main())
