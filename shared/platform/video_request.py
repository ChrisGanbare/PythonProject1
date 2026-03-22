"""公共平台渲染请求模型。"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from shared.config.settings import VideoConfig, get_quality_preset
from shared.content.schemas import ContentStyle, ContentVariant
from shared.platform.presets import PlatformPreset, get_platform_preset


class PlatformName(str, Enum):
    """统一的平台枚举。"""

    BILIBILI_LANDSCAPE = "bilibili_landscape"
    BILIBILI_VERTICAL = "bilibili_vertical"
    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"


class RenderQuality(str, Enum):
    """统一渲染质量档。"""

    PREVIEW = "preview"
    DRAFT = "draft"
    FINAL = "final"


class PlatformRenderRequest(BaseModel):
    """所有视频生成请求共享的渲染参数。"""

    platform: PlatformName = Field(description="目标发布平台")
    style: ContentStyle = Field(default=ContentStyle.TECH, description="内容风格")
    content_variant: ContentVariant | None = Field(default=None, description="内容结构版本；为空时按时长自动推断")
    quality: RenderQuality = Field(default=RenderQuality.DRAFT, description="渲染质量档")
    video_duration: int = Field(default=30, description="视频时长（秒）")
    fps: int | None = Field(
        default=None,
        description="可选，仅允许填写与平台标准一致的帧率；为空时自动使用平台默认值",
    )
    output_format: Literal["mp4"] = Field(default="mp4", description="当前仅支持 mp4 输出")
    burn_subtitles: bool = Field(default=True, description="是否将字幕直接烧录到最终视频")
    background_music: str | None = Field(default=None, description="可选，本地 BGM 文件路径")
    bgm_volume: float = Field(default=0.22, ge=0.0, le=1.0, description="BGM 音量")
    video_audio_volume: float = Field(default=1.0, ge=0.0, le=2.0, description="原视频音量")
    bgm_loop: bool = Field(default=True, description="BGM 长度不足时是否循环")
    ducking_enabled: bool = Field(default=True, description="原视频存在音轨时是否对 BGM 做压低处理")
    ducking_strength: float = Field(default=0.6, ge=0.0, le=1.0, description="ducking 强度")

    @property
    def platform_preset(self) -> PlatformPreset:
        return get_platform_preset(self.platform.value)

    @model_validator(mode="after")
    def validate_platform_constraints(self) -> "PlatformRenderRequest":
        preset = self.platform_preset

        if not (preset.min_duration <= self.video_duration <= preset.max_duration):
            raise ValueError(
                f"{preset.name} 视频时长必须在 {preset.min_duration}-{preset.max_duration} 秒之间"
            )

        if self.fps is not None and self.fps != preset.fps:
            raise ValueError(f"{preset.name} 仅支持 {preset.fps}fps")

        return self

    def build_video_config(self, base_config: VideoConfig) -> VideoConfig:
        """将平台规格与当前请求合成为实际渲染配置。"""
        preset = self.platform_preset
        merged = base_config.model_dump()
        quality_preset = get_quality_preset(self.quality.value)
        merged.update(
            width=preset.width,
            height=preset.height,
            fps=self.fps or preset.fps,
            total_duration=self.video_duration,
            dpi=int(quality_preset["dpi"]),
            bitrate=int(quality_preset["bitrate"]),
            preset=str(quality_preset["preset"]),
            crf=int(quality_preset["crf"]),
        )
        return VideoConfig(**merged)

