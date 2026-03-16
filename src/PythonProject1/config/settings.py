"""
配置管理系统
使用 Pydantic v2 + 环境变量支持
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, Dict, Any
import os
from pathlib import Path


class VideoConfig(BaseSettings):
    """视频生成参数"""
    
    # 视频分辨率和帧率
    width: int = Field(default=1080, description="视频宽度（像素）")
    height: int = Field(default=1920, description="视频高度（像素）")
    dpi: int = Field(default=100, description="DPI（点数/英寸）")
    fps: int = Field(default=30, description="帧率（帧/秒）")
    total_duration: int = Field(default=30, description="总时长（秒）")
    
    # FFmpeg 编码参数
    codec: str = Field(default="libx264", description="视频编码器")
    bitrate: int = Field(default=8000, description="比特率（kbps）")
    preset: str = Field(default="medium", description="编码质量预设（ultrafast/superfast/veryfast/faster/fast/medium/slow/slower/veryslow）")
    crf: int = Field(default=20, description="质量控制（0-51，越低越好）")
    pix_fmt: str = Field(default="yuv420p", description="像素格式（yuv420p 适配大多数播放器）")
    
    # 输出路径
    output_dir: Path = Field(default_factory=lambda: Path("D:/PythonProject1/outputs"), description="输出目录")
    
    class Config:
        env_prefix = "VIDEO_"
        case_sensitive = False
    
    @validator("width", "height")
    def validate_resolution(cls, v: int) -> int:
        """验证分辨率"""
        if v < 480 or v > 4096:
            raise ValueError(f"分辨率必须在 480-4096 之间，当前值: {v}")
        return v
    
    @validator("fps")
    def validate_fps(cls, v: int) -> int:
        """验证帧率"""
        if v not in [24, 25, 30, 60]:
            raise ValueError(f"帧率建议为 24/25/30/60，当前值: {v}")
        return v
    
    @validator("crf")
    def validate_crf(cls, v: int) -> int:
        """验证质量参数"""
        if not 0 <= v <= 51:
            raise ValueError(f"CRF 必须在 0-51 之间，当前值: {v}")
        return v


class APIConfig(BaseSettings):
    """第三方 API 配置"""
    
    # OpenAI API
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API 密钥")
    openai_model: str = Field(default="gpt-3.5-turbo", description="OpenAI 模型")
    openai_timeout: int = Field(default=30, description="OpenAI 请求超��（秒）")
    
    # Pexels API
    pexels_api_key: Optional[str] = Field(default=None, description="Pexels API 密钥")
    pexels_timeout: int = Field(default=15, description="Pexels 请求超时（秒）")
    pexels_cache_dir: Path = Field(default_factory=lambda: Path("D:/PythonProject1/pexels_cache"), description="Pexels 缓存目录")
    
    # 网络相关
    max_retries: int = Field(default=3, description="API 请求最大重试次数")
    retry_backoff_factor: float = Field(default=2.0, description="重试退避因子（指数退避）")
    
    class Config:
        env_prefix = "API_"
        case_sensitive = False
    
    @validator("max_retries")
    def validate_retries(cls, v: int) -> int:
        """验证重试次数"""
        if v < 1 or v > 10:
            raise ValueError(f"重试次数必须在 1-10 之间，当前值: {v}")
        return v


class LogConfig(BaseSettings):
    """日志配置"""
    
    log_level: str = Field(default="INFO", description="日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）")
    log_dir: Path = Field(default_factory=lambda: Path("D:/PythonProject1/logs"), description="日志目录")
    log_format: str = Field(
        default="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        description="日志格式"
    )
    log_to_file: bool = Field(default=True, description="是否写入文件")
    log_to_console: bool = Field(default=True, description="是否输出到控制台")
    max_log_size: int = Field(default=10_485_760, description="单个日志文件最大大小（字节，默认 10MB）")
    backup_count: int = Field(default=5, description="备份日志文件数量")
    
    class Config:
        env_prefix = "LOG_"
        case_sensitive = False


class Settings(BaseSettings):
    """全局配置"""
    
    # 环境
    env: str = Field(default="development", description="运行环境（development/production）")
    debug: bool = Field(default=False, description="调试模式")
    
    # 子配置
    video: VideoConfig = Field(default_factory=VideoConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    
    # 文件路径
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent.parent)
    cache_dir: Path = Field(default_factory=lambda: Path("D:/PythonProject1/cache"))
    temp_dir: Path = Field(default_factory=lambda: Path("D:/PythonProject1/temp"))
    
    # 贷款默认参数
    default_loan_amount: float = Field(default=1_000_000, description="默认贷款金额（元）")
    default_annual_rate: float = Field(default=0.045, description="默认年利率")
    default_loan_years: int = Field(default=30, description="默认贷款期限（年）")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        nested_delimiter = "__"  # 支持嵌套环境变量如 VIDEO__WIDTH
    
    def __init__(self, **data):
        super().__init__(**data)
        # 创建必要的目录
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        directories = [
            self.video.output_dir,
            self.api.pexels_cache_dir,
            self.log.log_dir,
            self.cache_dir,
            self.temp_dir,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典（用于日志记录）"""
        return {
            "env": self.env,
            "debug": self.debug,
            "video": {
                "resolution": f"{self.video.width}x{self.video.height}",
                "fps": self.video.fps,
                "bitrate": f"{self.video.bitrate}kbps",
            },
            "api": {
                "openai_model": self.api.openai_model,
                "max_retries": self.api.max_retries,
            },
            "log": {
                "level": self.log.log_level,
                "to_file": self.log.log_to_file,
            },
        }


# 全局单例
try:
    settings = Settings()
except Exception as e:
    import sys
    print(f"[错误] 配置加载失败: {e}")
    print("请检查 .env 文件或环境变量")
    sys.exit(1)

