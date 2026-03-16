"""
自定义异常类
遵循 PEP 8，为所有异常提供清晰的说明和错误链接
"""

from typing import Optional


class VideoProjectException(Exception):
    """项目基础异常"""
    pass


class ConfigurationError(VideoProjectException):
    """配置错误"""
    def __init__(self, message: str, config_key: Optional[str] = None):
        self.message = message
        self.config_key = config_key
        super().__init__(f"[配置] {message}" + (f" (key: {config_key})" if config_key else ""))


class APIError(VideoProjectException):
    """API 调用错误"""
    def __init__(self, message: str, api_name: str, status_code: Optional[int] = None):
        self.message = message
        self.api_name = api_name
        self.status_code = status_code
        super().__init__(
            f"[{api_name} API] {message}" + (f" (HTTP {status_code})" if status_code else "")
        )


class FileDownloadError(VideoProjectException):
    """文件下载错误"""
    def __init__(self, message: str, url: Optional[str] = None, retry_count: int = 0):
        self.message = message
        self.url = url
        self.retry_count = retry_count
        super().__init__(
            f"[文件下载] {message}" +
            (f" (url: {url})" if url else "") +
            (f" (已重试 {retry_count} 次)" if retry_count > 0 else "")
        )


class RenderError(VideoProjectException):
    """视频渲染错误"""
    def __init__(self, message: str, step: Optional[str] = None, ffmpeg_stderr: Optional[str] = None):
        self.message = message
        self.step = step
        self.ffmpeg_stderr = ffmpeg_stderr
        error_msg = f"[渲染] {message}"
        if step:
            error_msg += f" (步骤: {step})"
        if ffmpeg_stderr:
            error_msg += f"\nFFmpeg 输出: {ffmpeg_stderr[:200]}"
        super().__init__(error_msg)


class LoanCalculationError(VideoProjectException):
    """贷款计算错误"""
    def __init__(self, message: str, loan_amount: Optional[float] = None, annual_rate: Optional[float] = None):
        self.message = message
        self.loan_amount = loan_amount
        self.annual_rate = annual_rate
        error_msg = f"[贷款计算] {message}"
        if loan_amount is not None:
            error_msg += f" (贷款金额: {loan_amount})"
        if annual_rate is not None:
            error_msg += f" (年利率: {annual_rate})"
        super().__init__(error_msg)


class ParameterValidationError(VideoProjectException):
    """参数验证错误"""
    def __init__(self, message: str, parameter_name: str, value: str, expected: str):
        self.message = message
        self.parameter_name = parameter_name
        self.value = value
        self.expected = expected
        super().__init__(
            f"[参数验证] {message}\n  参数: {parameter_name}\n  当前值: {value}\n  期望值: {expected}"
        )

