"""
平台模块
"""

from .specs import (
    PlatformType,
    PlatformSpec,
    get_platform_spec,
    list_platforms,
    validate_for_platform,
    BILIBILI_SPEC,
    DOUYIN_SPEC,
    XIAOHONGSHU_SPEC,
    YOUTUBE_SPEC
)

__all__ = [
    'PlatformType',
    'PlatformSpec',
    'get_platform_spec',
    'list_platforms',
    'validate_for_platform',
    'BILIBILI_SPEC',
    'DOUYIN_SPEC',
    'XIAOHONGSHU_SPEC',
    'YOUTUBE_SPEC'
]
