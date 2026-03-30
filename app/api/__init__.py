"""
API 包。

统一 ASGI 应用由 ``scripts.dashboard`` 提供；``python -m api.main`` 仅启动该应用。
"""

from .main import main

__all__ = ["main"]
