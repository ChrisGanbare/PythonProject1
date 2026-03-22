"""时间辅助函数。"""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """返回带 UTC 时区的当前时间。"""
    return datetime.now(timezone.utc)

