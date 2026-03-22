from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from shared.studio.config import get_database_url, is_sqlite


class Base(DeclarativeBase):
    pass


_engine = None


def get_engine():
    """懒加载；便于测试在 import 前设置 ``STUDIO__DATABASE_URL``。"""
    global _engine
    if _engine is None:
        url = get_database_url()
        kwargs: dict = {"echo": False, "future": True}
        if is_sqlite(url):
            kwargs["connect_args"] = {"check_same_thread": False}
        _engine = create_engine(url, **kwargs)
    return _engine


def reset_engine() -> None:
    """仅测试：切换 ``STUDIO__DATABASE_URL`` 后释放旧连接池。"""
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None


# 未绑定引擎的工厂；每次 ``SessionLocal(bind=get_engine())`` 使用当前 URL
SessionLocal = sessionmaker(autoflush=False, autocommit=False, future=True)
