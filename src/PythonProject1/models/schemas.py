"""
FastAPI 数据模型（Pydantic）
用于 API 请求/响应验证
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime


class TaskStatus(str, Enum):
    """任务状态枚举"""
    QUEUED = "queued"  # 等待中
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class ColorScheme(str, Enum):
    """配色方案"""
    DARK_FLOURISH = "dark_flourish"  # 深色 Flourish 风格（默认）
    LIGHT_MODERN = "light_modern"  # 浅色现代风格
    NEON_CYBERPUNK = "neon_cyberpunk"  # 霓虹朋克风格


class GenerateVideoRequest(BaseModel):
    """生成视频请求"""
    
    # 贷款参数
    loan_amount: float = Field(
        default=1_000_000,
        ge=10_000,
        le=10_000_000,
        description="贷款金额（元）"
    )
    annual_rate: float = Field(
        default=0.045,
        ge=0.001,
        le=0.2,
        description="年利率（小数，如 0.045 表示 4.5%）"
    )
    loan_years: int = Field(
        default=30,
        ge=1,
        le=40,
        description="贷款期限（年）"
    )
    
    # 视频参数
    video_duration: int = Field(
        default=30,
        ge=15,
        le=120,
        description="视频时长（秒）"
    )
    fps: int = Field(
        default=30,
        description="帧率（24/25/30/60）"
    )
    
    # 样式参数
    color_scheme: ColorScheme = Field(
        default=ColorScheme.DARK_FLOURISH,
        description="配色方案"
    )
    include_subtitles: bool = Field(
        default=False,
        description="是否添加字幕"
    )
    background_music: Optional[str] = Field(
        default=None,
        description="背景音乐 URL（可选）"
    )
    
    # 其他参数
    output_format: str = Field(
        default="mp4",
        regex="^(mp4|webm|mov)$",
        description="输出格式"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
                "video_duration": 30,
                "fps": 30,
                "color_scheme": "dark_flourish",
                "include_subtitles": False,
                "output_format": "mp4",
            }
        }


class VideoTaskResponse(BaseModel):
    """视频任务响应"""
    
    task_id: str = Field(..., description="任务 ID")
    status: TaskStatus = Field(default=TaskStatus.QUEUED, description="任务状态")
    message: str = Field(default="", description="状态消息")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "queued",
                "message": "任务已加入队列",
                "created_at": "2024-03-16T10:30:00Z",
            }
        }


class VideoProgressResponse(BaseModel):
    """视频生成进度响应"""
    
    task_id: str = Field(..., description="任务 ID")
    status: TaskStatus = Field(..., description="任务状态")
    progress: int = Field(
        ge=0,
        le=100,
        description="完成进度（百分比）"
    )
    current_step: str = Field(default="", description="当前处理步骤")
    eta_seconds: Optional[int] = Field(default=None, description="预计剩余时间（秒）")
    error_message: Optional[str] = Field(default=None, description="错误信息（如果失败）")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "progress": 45,
                "current_step": "rendering_frames",
                "eta_seconds": 120,
                "created_at": "2024-03-16T10:30:00Z",
                "updated_at": "2024-03-16T10:35:00Z",
            }
        }


class VideoResultResponse(BaseModel):
    """视频生成结果响应"""
    
    task_id: str = Field(..., description="任务 ID")
    status: TaskStatus = Field(..., description="任务状态")
    video_url: Optional[str] = Field(default=None, description="视频下载 URL")
    file_path: Optional[str] = Field(default=None, description="本地文件路径")
    file_size: Optional[int] = Field(default=None, description="文件大小（字节）")
    duration: Optional[float] = Field(default=None, description="视频时长（秒）")
    resolution: Optional[str] = Field(default=None, description="分辨率（如 1080x1920）")
    created_at: datetime = Field(..., description="创建时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    processing_time: Optional[float] = Field(default=None, description="处理耗时（秒）")
    error_message: Optional[str] = Field(default=None, description="错误信息（如果失败）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "video_url": "/api/download/550e8400-e29b-41d4-a716-446655440000",
                "file_path": "D:/PythonProject1/outputs/loan_comparison_550e8400.mp4",
                "file_size": 25_165_824,
                "duration": 30.0,
                "resolution": "1080x1920",
                "created_at": "2024-03-16T10:30:00Z",
                "completed_at": "2024-03-16T10:40:00Z",
                "processing_time": 600.5,
            }
        }


class LoanSummaryResponse(BaseModel):
    """贷款计算摘要响应"""
    
    loan_amount: float = Field(..., description="贷款金额")
    annual_rate: float = Field(..., description="年利率")
    loan_years: int = Field(..., description="贷款期限（年）")
    total_months: int = Field(..., description="总期数（月）")
    
    equal_interest: Dict[str, float] = Field(..., description="等额本息信息")
    equal_principal: Dict[str, float] = Field(..., description="等额本金信息")
    comparison: Dict[str, Any] = Field(..., description="两种方式���比")
    
    class Config:
        json_schema_extra = {
            "example": {
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
                "total_months": 360,
                "equal_interest": {
                    "monthly_payment": 5066.57,
                    "total_interest": 823_967.69,
                    "total_repay": 1_823_967.69,
                },
                "equal_principal": {
                    "first_month_payment": 5458.33,
                    "last_month_payment": 2778.75,
                    "total_interest": 695_208.33,
                    "total_repay": 1_695_208.33,
                },
                "comparison": {
                    "interest_difference": 128_759.36,
                    "difference_percentage": 15.64,
                    "which_is_cheaper": "等额本金",
                },
            }
        }


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    
    status: str = Field(default="OK", description="服务状态")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="检查时间")
    version: str = Field(default="1.0.0", description="API 版本")
    message: Optional[str] = Field(default=None, description="附加信息")

