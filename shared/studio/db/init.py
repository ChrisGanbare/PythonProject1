"""建表（开发默认）；生产建议使用 Alembic 迁移。"""

from __future__ import annotations

from sqlalchemy import inspect, text

from shared.studio.db import base  # noqa: F401 — register models
from shared.studio.db.base import Base, get_engine
from shared.studio.db import models  # noqa: F401


def _run_migrations(engine) -> None:
    """对已存在的表执行轻量级增量迁移（幂等）。"""
    inspector = inspect(engine)
    with engine.connect() as conn:
        # code_sessions.task_name（2026-03 新增）
        if "code_sessions" in inspector.get_table_names():
            cols = {c["name"] for c in inspector.get_columns("code_sessions")}
            if "task_name" not in cols:
                conn.execute(text(
                    "ALTER TABLE code_sessions ADD COLUMN task_name VARCHAR(256)"
                ))
                conn.commit()
        
        # intent_sessions.is_completed（2026会话状态新增）
        if "intent_sessions" in inspector.get_table_names():
            cols = {c["name"] for c in inspector.get_columns("intent_sessions")}
            if "is_completed" not in cols:
                conn.execute(text(
                    "ALTER TABLE intent_sessions ADD COLUMN is_completed BOOLEAN NOT NULL DEFAULT 0"
                ))
                conn.commit()


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _run_migrations(engine)
