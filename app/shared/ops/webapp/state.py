"""控制台与 Web 应用共享状态：仓库根路径、ProjectRegistry 单例。"""

from __future__ import annotations

from pathlib import Path

from orchestrator.registry import ProjectRegistry

REPO_ROOT = Path(__file__).resolve().parents[4]
registry = ProjectRegistry(REPO_ROOT / "app")
