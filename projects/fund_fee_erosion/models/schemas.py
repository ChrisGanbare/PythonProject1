"""Pydantic schemas for fund_fee_erosion API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from shared.core.task_manager import TaskStatus


class GenerateFundVideoRequest(BaseModel):
    principal: float = Field(default=1_000_000, ge=10_000, le=100_000_000, description="初始本金（元）")
    gross_return: float = Field(default=0.08, ge=0.0, le=1.0, description="年化毛收益率（小数）")
    years: int = Field(default=30, ge=1, le=50, description="投资年限")

    video_duration: int = Field(default=30, ge=15, le=120, description="视频时长（秒）")
    fps: int = Field(default=30, ge=15, le=60, description="帧率")

    output_format: str = Field(default="mp4", pattern="^(mp4|webm|mov)$")


class FundSummaryResponse(BaseModel):
    principal: float
    gross_return: float
    years: int
    scenarios: dict[str, Any]


class VideoTaskResponse(BaseModel):
    task_id: str
    status: TaskStatus = TaskStatus.QUEUED
    message: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VideoProgressResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: int = Field(ge=0, le=100)
    current_step: str = ""
    eta_seconds: int | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VideoResultResponse(BaseModel):
    task_id: str
    status: TaskStatus
    video_url: str | None = None
    file_path: str | None = None
    file_size: int | None = None
    duration: float | None = None
    resolution: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    processing_time: float | None = None
    error_message: str | None = None


class HealthCheckResponse(BaseModel):
    status: str = "OK"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    message: str | None = None
