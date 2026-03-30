"""领域子项目 FastAPI 子应用挂载：单一注册表，供 Dashboard 组装与架构清单使用。"""

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

# (公开名称, importlib 模块路径，需导出 ``app``)
DOMAIN_APP_SPECS: tuple[tuple[str, str], ...] = (
    ("loan_comparison", "loan_comparison.api.main"),
    ("fund_fee_erosion", "fund_fee_erosion.api.main"),
    ("video_platform_introduction", "video_platform_introduction.api.main"),
)


def mount_domain_apps(app: FastAPI, *, logger: logging.Logger | None = None) -> None:
    """将各子项目既有 FastAPI 应用挂到 ``/api/domain/<name>``。"""
    log = logger or logging.getLogger(__name__)
    for name, mod_path in DOMAIN_APP_SPECS:
        try:
            mod = importlib.import_module(mod_path)
            sub = getattr(mod, "app", None)
            if sub is None:
                continue
            mount_path = f"/api/domain/{name}"
            app.mount(mount_path, sub)
            log.info("Domain API mounted at %s", mount_path)
        except Exception as exc:
            log.warning("Domain mount skipped %s: %s", name, exc)
