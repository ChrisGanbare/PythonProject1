"""
数据可视化视频：默认后端 **Matplotlib**（帧动画 / 与 FFmpeg 衔接成熟）；
可选 **Plotly 静态导出**（见 `backends/plotly_static.py`，需 kaleido）。

详见 `docs/DATA_VIZ_VIDEO_ARCHITECTURE.md`。
"""

from shared.visualization.protocol import VizRenderBackend
from shared.visualization.registry import (
    default_backend_name,
    get_backend,
    list_backends,
    register_backend,
)
from shared.visualization.render_cache import render_cache_dir, sanitize_cache_segment
from shared.visualization.runtime import cache_key_components_from_env, frame_request_from_env
from shared.visualization.types import BackendName, FrameRequest, VideoFormatSpec, VizSceneRef

__all__ = [
    "BackendName",
    "FrameRequest",
    "VideoFormatSpec",
    "VizSceneRef",
    "VizRenderBackend",
    "cache_key_components_from_env",
    "default_backend_name",
    "frame_request_from_env",
    "get_backend",
    "list_backends",
    "register_backend",
    "render_cache_dir",
    "sanitize_cache_segment",
]
