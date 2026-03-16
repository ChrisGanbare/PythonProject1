"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from shared.core.task_manager import TaskStatus


class ColorScheme(str, Enum):
    DARK_FLOURISH = "dark_flourish"
    LIGHT_MODERN = "light_modern"
    NEON_CYBERPUNK = "neon_cyberpunk"


class GenerateVideoRequest(BaseModel):
    loan_amount: float = Field(default=1_000_000, ge=10_000, le=10_000_000)
    annual_rate: float = Field(default=0.045, ge=0.001, le=0.2)
    loan_years: int = Field(default=30, ge=1, le=40)

    video_duration: int = Field(default=30, ge=15, le=120)
    fps: int = Field(default=30)

    color_scheme: ColorScheme = Field(default=ColorScheme.DARK_FLOURISH)
    include_subtitles: bool = Field(default=False)
    background_music: str | None = Field(default=None)

    output_format: str = Field(default="mp4", pattern="^(mp4|webm|mov)$")


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
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    message: str | None = None
