"""Schemas for video_platform_introduction APIs."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

from shared.content.screenplay import Screenplay
from shared.platform.video_request import PlatformRenderRequest
from shared.utils.time import utc_now


class GenerateVideoRequest(PlatformRenderRequest):
    topic: str | None = Field(default=None, description="视频主题，留空则使用项目默认主题")
    sample_metric: float = Field(default=1.0, description="示例指标")


class ScreenplayPreviewRequest(GenerateVideoRequest):
    target_audience: str = Field(default="中文短视频创作者", description="目标观众")
    screenplay_provider: str | None = Field(default=None, description="可选，指定剧本 provider")


class ProviderDescriptorResponse(BaseModel):
    name: str
    description: str
    supports_remote: bool = False
    enabled: bool = True
    is_default: bool = False
    is_fallback: bool = False


class ScreenplayPreviewResponse(BaseModel):
    screenplay: Screenplay
    provider_used: str
    requested_provider: str | None = None
    fallback_used: bool = False


class ScreenplayEditRequest(BaseModel):
    screenplay: Screenplay
    screenplay_provider: str | None = Field(default=None, description="可选，指定剧本 provider")
    title: str | None = None
    logline: str | None = None
    edit_instruction: str | None = Field(default=None, description="自然语言修改指令")
    scene_narration_overrides: dict[str, str] = Field(default_factory=dict)


class ScreenplayEditResponse(ScreenplayPreviewResponse):
    changed_scene_ids: list[str] = Field(default_factory=list)


class HealthCheckResponse(BaseModel):
    status: str = "OK"
    timestamp: datetime = Field(default_factory=utc_now)
    version: str = "1.0.0"
    message: str | None = None
