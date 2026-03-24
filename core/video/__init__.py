"""
Core Video Module

视频处理系统，支持 MoviePy 和 FFmpeg
"""

from .composer import (
    VideoComposer,
    VideoProcessor,
    VideoConfig,
    quick_compose
)

try:
    from .ffmpeg_wrapper import (
        FFmpegWrapper,
        FFmpegConfig,
        BatchVideoProcessor,
        quick_encode
    )
except ImportError:
    pass

__version__ = "1.0.0"
__all__ = [
    'VideoComposer',
    'VideoProcessor',
    'VideoConfig',
    'quick_compose',
    'FFmpegWrapper',
    'FFmpegConfig',
    'BatchVideoProcessor',
    'quick_encode'
]
