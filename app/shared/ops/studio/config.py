"""Studio 控制面配置：数据库与其它跨切面设置。"""

from __future__ import annotations

import os
from pathlib import Path


def _repo_root() -> Path:
    # app/shared/ops/studio/config.py → parents[4] = workspace root
    return Path(__file__).resolve().parents[4]


def get_database_url() -> str:
    """默认 SQLite 文件库；生产可设为 PostgreSQL 等（SQLAlchemy URL）。

    环境变量（任选一）::
        STUDIO__DATABASE_URL
        STUDIO_DATABASE_URL
    """
    env = (os.environ.get("STUDIO__DATABASE_URL") or os.environ.get("STUDIO_DATABASE_URL") or "").strip()
    if env:
        return env
    db_path = _repo_root() / "runtime" / "studio.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # SQLAlchemy sqlite 需要正斜杠路径
    return f"sqlite:///{db_path.as_posix()}"


def is_sqlite(url: str) -> bool:
    return url.strip().lower().startswith("sqlite:")
