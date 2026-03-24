"""
平台规格定义 - B 站/抖音/小红书/YouTube

定义各视频平台的规格要求
"""

from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
from enum import Enum


class PlatformType(str, Enum):
    """平台类型"""
    BILIBILI = "bilibili"
    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


@dataclass
class PlatformSpec:
    """平台规格"""
    
    # 基础信息
    name: str
    platform_type: PlatformType
    
    # 视频规格
    resolution: Tuple[int, int]  # (width, height)
    aspect_ratio: str  # "16:9", "9:16", "1:1", "4:5"
    fps: int = 30
    min_duration: float = 0.0  # 秒
    max_duration: float = 9999.0  # 秒
    
    # 文件大小
    max_file_size_mb: int = 500
    
    # 编码要求
    video_codec: str = "h264"
    audio_codec: str = "aac"
    bitrate: str = "5000k"
    
    # 字幕安全区
    subtitle_safe_area: Dict[str, int] = None
    
    # 封面要求
    cover_resolution: Optional[Tuple[int, int]] = None
    
    # 其他要求
    requirements: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.subtitle_safe_area is None:
            self.subtitle_safe_area = {
                "top": 100,
                "bottom": 100,
                "left": 50,
                "right": 50
            }


# 平台规格定义

BILIBILI_SPEC = PlatformSpec(
    name="哔哩哔哩",
    platform_type=PlatformType.BILIBILI,
    resolution=(1920, 1080),
    aspect_ratio="16:9",
    fps=30,
    min_duration=1.0,
    max_duration=7200.0,  # 2 小时
    max_file_size_mb=4000,
    bitrate="8000k",
    cover_resolution=(1146, 644),
    requirements={
        "title_max_length": 80,
        "description_max_length": 1000,
        "tags_max_count": 10,
        "support_4k": True,
        "support_hdr": True
    }
)

DOUYIN_SPEC = PlatformSpec(
    name="抖音",
    platform_type=PlatformType.DOUYIN,
    resolution=(1080, 1920),  # 竖屏
    aspect_ratio="9:16",
    fps=30,
    min_duration=1.0,
    max_duration=300.0,  # 5 分钟
    max_file_size_mb=500,
    bitrate="6000k",
    cover_resolution=(720, 1280),
    subtitle_safe_area={
        "top": 150,
        "bottom": 200,  # 底部有文案区域
        "left": 50,
        "right": 50
    },
    requirements={
        "title_max_length": 30,
        "description_max_length": 500,
        "hashtags_max_count": 10,
        "vertical_video": True
    }
)

XIAOHONGSHU_SPEC = PlatformSpec(
    name="小红书",
    platform_type=PlatformType.XIAOHONGSHU,
    resolution=(1080, 1920),  # 竖屏
    aspect_ratio="9:16",
    fps=30,
    min_duration=1.0,
    max_duration=300.0,  # 5 分钟
    max_file_size_mb=500,
    bitrate="6000k",
    cover_resolution=(720, 1280),
    subtitle_safe_area={
        "top": 200,  # 顶部有标题
        "bottom": 200,  # 底部有互动区
        "left": 50,
        "right": 50
    },
    requirements={
        "title_max_length": 20,
        "description_max_length": 1000,
        "tags_max_count": 20,
        "vertical_video": True,
        "cover_required": True
    }
)

YOUTUBE_SPEC = PlatformSpec(
    name="YouTube",
    platform_type=PlatformType.YOUTUBE,
    resolution=(1920, 1080),
    aspect_ratio="16:9",
    fps=30,
    min_duration=1.0,
    max_duration=43200.0,  # 12 小时
    max_file_size_mb=128000,  # 128GB
    bitrate="10000k",
    cover_resolution=(1280, 720),
    requirements={
        "title_max_length": 100,
        "description_max_length": 5000,
        "tags_max_count": 500,
        "support_4k": True,
        "support_8k": True,
        "support_hdr": True,
        "support_60fps": True
    }
)

INSTAGRAM_REEL_SPEC = PlatformSpec(
    name="Instagram Reels",
    platform_type=PlatformType.INSTAGRAM,
    resolution=(1080, 1920),
    aspect_ratio="9:16",
    fps=30,
    min_duration=3.0,
    max_duration=90.0,
    max_file_size_mb=100,
    bitrate="5000k",
    cover_resolution=(1080, 1920),
    requirements={
        "vertical_video": True,
        "music_support": True
    }
)

TIKTOK_SPEC = PlatformSpec(
    name="TikTok",
    platform_type=PlatformType.TIKTOK,
    resolution=(1080, 1920),
    aspect_ratio="9:16",
    fps=30,
    min_duration=3.0,
    max_duration=600.0,  # 10 分钟
    max_file_size_mb=287.6,
    bitrate="6000k",
    cover_resolution=(1080, 1920),
    requirements={
        "vertical_video": True,
        "music_support": True,
        "effects_support": True
    }
)


# 平台规格注册表

PLATFORM_SPECS: Dict[PlatformType, PlatformSpec] = {
    PlatformType.BILIBILI: BILIBILI_SPEC,
    PlatformType.DOUYIN: DOUYIN_SPEC,
    PlatformType.XIAOHONGSHU: XIAOHONGSHU_SPEC,
    PlatformType.YOUTUBE: YOUTUBE_SPEC,
    PlatformType.INSTAGRAM: INSTAGRAM_REEL_SPEC,
    PlatformType.TIKTOK: TIKTOK_SPEC,
}


def get_platform_spec(platform: str) -> Optional[PlatformSpec]:
    """获取平台规格"""
    
    if isinstance(platform, PlatformType):
        return PLATFORM_SPECS.get(platform)
    
    # 字符串查找
    platform_lower = platform.lower()
    
    for spec in PLATFORM_SPECS.values():
        if spec.platform_type.value == platform_lower or \
           spec.name.lower() == platform_lower or \
           spec.name.lower().startswith(platform_lower):
            return spec
    
    return None


def list_platforms() -> Dict[str, PlatformSpec]:
    """列出所有平台"""
    return {
        spec.platform_type.value: spec
        for spec in PLATFORM_SPECS.values()
    }


def validate_for_platform(
    video_path: str,
    platform: str
) -> tuple[bool, list]:
    """
    验证视频是否符合平台要求
    
    Args:
        video_path: 视频文件路径
        platform: 平台名称
        
    Returns:
        (是否合格，问题列表)
    """
    import subprocess
    from pathlib import Path
    
    spec = get_platform_spec(platform)
    if not spec:
        return False, [f"Unknown platform: {platform}"]
    
    issues = []
    
    # 检查文件是否存在
    if not Path(video_path).exists():
        return False, ["Video file not found"]
    
    # 检查文件大小
    file_size_mb = Path(video_path).stat().st_size / (1024 * 1024)
    if file_size_mb > spec.max_file_size_mb:
        issues.append(
            f"File size ({file_size_mb:.1f}MB) exceeds limit ({spec.max_file_size_mb}MB)"
        )
    
    # 使用 ffprobe 获取视频信息
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            import json
            info = json.loads(result.stdout)
            
            # 检查视频流
            video_streams = [
                s for s in info.get("streams", [])
                if s.get("codec_type") == "video"
            ]
            
            if video_streams:
                video_info = video_streams[0]
                
                # 检查分辨率
                width = video_info.get("width", 0)
                height = video_info.get("height", 0)
                
                if (width, height) != spec.resolution:
                    issues.append(
                        f"Resolution {width}x{height} doesn't match "
                        f"platform requirement {spec.resolution[0]}x{spec.resolution[1]}"
                    )
                
                # 检查帧率
                fps = eval(video_info.get("r_frame_rate", "30/1"))
                if abs(fps - spec.fps) > 1:
                    issues.append(
                        f"FPS {fps:.1f} doesn't match platform requirement {spec.fps}"
                    )
                
                # 检查编码
                codec = video_info.get("codec_name", "")
                if codec != spec.video_codec:
                    issues.append(
                        f"Codec {codec} doesn't match platform requirement {spec.video_codec}"
                    )
    except Exception as e:
        issues.append(f"Failed to analyze video: {e}")
    
    return len(issues) == 0, issues


# 导出
__all__ = [
    'PlatformType',
    'PlatformSpec',
    'get_platform_spec',
    'list_platforms',
    'validate_for_platform',
    'BILIBILI_SPEC',
    'DOUYIN_SPEC',
    'XIAOHONGSHU_SPEC',
    'YOUTUBE_SPEC',
    'INSTAGRAM_REEL_SPEC',
    'TIKTOK_SPEC'
]
