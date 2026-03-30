"""Studio 控制面路由（HTTP 前缀由主应用设为 ``/api/studio/v1``）。"""

from shared.ops.studio.api.control_plane.router import create_v1_router

__all__ = ["create_v1_router"]
