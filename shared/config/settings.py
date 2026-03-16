"""
Project settings using pydantic-settings.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
    # shared/config/settings.py → parents[2] = workspace root
    return Path(__file__).resolve().parents[2]


def _runtime_root() -> Path:
    override = os.getenv("VIDEO_RUNTIME_DIR")
    return Path(override) if override else _project_root() / "runtime"


def _expand_nested_kwargs(raw_data: dict[str, Any]) -> dict[str, Any]:
    expanded: dict[str, Any] = {}
    for key, value in raw_data.items():
        if "__" not in key:
            expanded[key] = value
            continue

        parts = key.split("__")
        cursor = expanded
        for part in parts[:-1]:
            existing = cursor.get(part)
            if existing is None:
                cursor[part] = {}
                existing = cursor[part]
            if not isinstance(existing, dict):
                break
            cursor = existing
        else:
            cursor[parts[-1]] = value
            continue

        expanded[key] = value

    return expanded


class VideoConfig(BaseModel):
    width: int = Field(default=1080, description="Video width in px")
    height: int = Field(default=1920, description="Video height in px")
    dpi: int = Field(default=100, description="Render DPI")
    fps: int = Field(default=30, description="Frames per second")
    total_duration: int = Field(default=30, description="Total duration in seconds")
    codec: str = Field(default="libx264", description="Video codec")
    bitrate: int = Field(default=8000, description="Video bitrate kbps")
    preset: str = Field(default="medium", description="ffmpeg preset")
    crf: int = Field(default=20, description="Constant rate factor")
    pix_fmt: str = Field(default="yuv420p", description="Pixel format")
    output_dir: Path = Field(default_factory=lambda: _runtime_root() / "outputs")

    @field_validator("width", "height")
    @classmethod
    def validate_resolution(cls, value: int) -> int:
        if value < 480 or value > 4096:
            raise ValueError(f"resolution value out of range: {value}")
        return value

    @field_validator("fps")
    @classmethod
    def validate_fps(cls, value: int) -> int:
        if value not in {24, 25, 30, 60}:
            raise ValueError(f"unsupported fps: {value}")
        return value

    @field_validator("crf")
    @classmethod
    def validate_crf(cls, value: int) -> int:
        if value < 0 or value > 51:
            raise ValueError(f"crf out of range: {value}")
        return value


class APIConfig(BaseModel):
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-3.5-turbo", description="OpenAI model")
    openai_timeout: int = Field(default=30, description="OpenAI timeout seconds")
    pexels_api_key: str | None = Field(default=None, description="Pexels API key")
    pexels_timeout: int = Field(default=15, description="Pexels timeout seconds")
    pexels_cache_dir: Path = Field(default_factory=lambda: _runtime_root() / "pexels_cache")
    max_retries: int = Field(default=3, description="Max API retries")
    retry_backoff_factor: float = Field(default=2.0, description="Retry backoff multiplier")

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, value: int) -> int:
        if value < 1 or value > 10:
            raise ValueError(f"max_retries out of range: {value}")
        return value


class LogConfig(BaseModel):
    log_level: str = Field(default="INFO", description="Log level")
    log_dir: Path = Field(default_factory=lambda: _runtime_root() / "logs")
    log_format: str = Field(
        default="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        description="Log format",
    )
    log_to_file: bool = Field(default=True, description="Write logs to file")
    log_to_console: bool = Field(default=True, description="Print logs to console")
    max_log_size: int = Field(default=10_485_760, description="Max single log file size")
    backup_count: int = Field(default=5, description="Rotating backup count")


class Settings(BaseSettings):
    env: str = Field(default="development", description="Runtime environment")
    debug: bool = Field(default=False, description="Debug mode")

    video: VideoConfig = Field(default_factory=VideoConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    log: LogConfig = Field(default_factory=LogConfig)

    project_root: Path = Field(default_factory=_project_root)
    cache_dir: Path = Field(default_factory=lambda: _runtime_root() / "cache")
    temp_dir: Path = Field(default_factory=lambda: _runtime_root() / "temp")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    def __init__(self, **data: Any):
        expanded = _expand_nested_kwargs(data)
        super().__init__(**expanded)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        for directory in [
            self.video.output_dir,
            self.api.pexels_cache_dir,
            self.log.log_dir,
            self.cache_dir,
            self.temp_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "env": self.env,
            "debug": self.debug,
            "video": {
                "resolution": f"{self.video.width}x{self.video.height}",
                "fps": self.video.fps,
                "bitrate": f"{self.video.bitrate}kbps",
                "output_dir": str(self.video.output_dir),
            },
            "api": {
                "openai_model": self.api.openai_model,
                "max_retries": self.api.max_retries,
                "pexels_cache_dir": str(self.api.pexels_cache_dir),
            },
            "log": {
                "level": self.log.log_level,
                "to_file": self.log.log_to_file,
                "log_dir": str(self.log.log_dir),
            },
        }


settings = Settings()
