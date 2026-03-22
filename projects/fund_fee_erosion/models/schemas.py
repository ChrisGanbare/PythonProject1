"""Pydantic schemas for fund_fee_erosion API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from shared.core.task_manager import TaskStatus
from shared.platform.video_request import PlatformRenderRequest
from shared.utils.time import utc_now


class GenerateFundVideoRequest(PlatformRenderRequest):
    principal: float = Field(default=1_000_000, ge=10_000, le=100_000_000, description="初始本金（元）")
    gross_return: float = Field(default=0.08, ge=0.0, le=1.0, description="年化毛收益率（小数）")
    years: int = Field(default=30, ge=1, le=50, description="投资年限")



class FundSummaryResponse(BaseModel):
    principal: float
    gross_return: float
    years: int
    scenarios: dict[str, Any]


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
    render_manifest_path: str | None = None
    render_fingerprint: str | None = None
    file_size: int | None = None
    duration: float | None = None
    resolution: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    processing_time: float | None = None
    error_message: str | None = None


class HealthCheckResponse(BaseModel):
    status: str = "OK"
    timestamp: datetime = Field(default_factory=utc_now)
    version: str = "1.0.0"
    message: str | None = None
