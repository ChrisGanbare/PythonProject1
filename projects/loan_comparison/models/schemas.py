"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from shared.content.screenplay import Screenplay
from shared.core.task_manager import TaskStatus
from shared.platform.video_request import PlatformRenderRequest
from shared.utils.time import utc_now


class GenerateVideoRequest(PlatformRenderRequest):
    loan_amount: float = Field(default=1_000_000, ge=10_000, le=10_000_000)
    annual_rate: float = Field(default=0.045, ge=0.001, le=0.2)
    loan_years: int = Field(default=30, ge=1, le=40)
    script_id: str | None = Field(default=None, description="已保存的剧本项目 ID；若填写则使用该版本的 Screenplay 驱动画面")
    script_version: int | None = Field(default=None, description="版本号；默认使用最新版本")
    require_approved_script: bool = Field(
        default=False,
        description="为 True 时仅允许已定稿(approved)的版本参与成片",
    )


class ScreenplayPreviewRequest(GenerateVideoRequest):
    topic: str | None = Field(default=None, description="可选，自定义视频主题")
    target_audience: str = Field(default="中文自媒体观众", description="目标观众")
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



class VideoTaskResponse(BaseModel):
    task_id: str
    status: TaskStatus = TaskStatus.QUEUED
    message: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class VideoProgressResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: int = Field(ge=0, le=100)
    current_step: str = ""
    eta_seconds: int | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime = Field(default_factory=utc_now)


class VideoResultResponse(BaseModel):
    task_id: str
    status: TaskStatus
    platform: str | None = None
    quality: str | None = None
    content_style: str | None = None
    content_variant: str | None = None
    conclusion_card_title: str | None = None
    theme_name: str | None = None
    visual_focus: str | None = None
    subtitle_burned: bool | None = None
    bgm_applied: bool | None = None
    rendered_video_path: str | None = None
    final_video_path: str | None = None
    video_url: str | None = None
    file_path: str | None = None
    subtitle_path: str | None = None
    styled_subtitle_path: str | None = None
    subtitle_render_mode: str | None = None
    cover_path: str | None = None
    scene_schedule_path: str | None = None
    scene_schedule: dict[str, Any] | None = None
    render_manifest_path: str | None = None
    file_size: int | None = None
    duration: float | None = None
    resolution: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    processing_time: float | None = None
    error_message: str | None = None


class LoanSummaryResponse(BaseModel):
    loan_amount: float
    annual_rate: float
    loan_years: int
    total_months: int
    equal_interest: dict[str, float]
    equal_principal: dict[str, float]
    comparison: dict[str, Any]


class HealthCheckResponse(BaseModel):
    status: str = "OK"
    timestamp: datetime = Field(default_factory=utc_now)
    version: str = "1.0.0"
    message: str | None = None


class ScriptCreateRequest(BaseModel):
    goal: str = Field(default="", description="创作目标，如转化/科普/引流")
    platform: str = Field(default="", description="目标平台标识，自由文本")
    topic: str = Field(default="", description="选题简述")
    screenplay: Screenplay = Field(description="首版剧本内容")


class ScriptCreateResponse(BaseModel):
    script_id: str
    version: int
    status: str


class ScriptVersionCreateRequest(BaseModel):
    screenplay: Screenplay
    parent_version: int | None = None
    status: str = Field(default="draft", description="draft 或 approved")


class ScriptRefineRequest(BaseModel):
    base_version: int | None = Field(default=None, description="基于哪一版；默认最新")
    edit_instruction: str | None = None
    title: str | None = None
    logline: str | None = None
    scene_narration_overrides: dict[str, str] = Field(default_factory=dict)
    screenplay_provider: str | None = None


class AssetListItem(BaseModel):
    id: str
    type: str
    path: str
    description: str
    tags: list[str] = Field(default_factory=list)
