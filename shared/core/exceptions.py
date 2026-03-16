"""Custom exceptions used across the workspace."""

from __future__ import annotations


class VideoProjectException(Exception):
    """Base exception."""


class ConfigurationError(VideoProjectException):
    def __init__(self, message: str, config_key: str | None = None):
        extra = f" (key={config_key})" if config_key else ""
        super().__init__(f"[config] {message}{extra}")


class APIError(VideoProjectException):
    def __init__(self, message: str, api_name: str, status_code: int | None = None):
        extra = f" (HTTP {status_code})" if status_code else ""
        super().__init__(f"[{api_name}] {message}{extra}")


class FileDownloadError(VideoProjectException):
    def __init__(self, message: str, url: str | None = None, retry_count: int = 0):
        extra = ""
        if url:
            extra += f" (url={url})"
        if retry_count > 0:
            extra += f" (retry={retry_count})"
        super().__init__(f"[download] {message}{extra}")


class RenderError(VideoProjectException):
    def __init__(self, message: str, step: str | None = None, ffmpeg_stderr: str | None = None):
        extra = f" (step={step})" if step else ""
        if ffmpeg_stderr:
            extra += f" stderr={ffmpeg_stderr[:200]}"
        super().__init__(f"[render] {message}{extra}")


class LoanCalculationError(VideoProjectException):
    def __init__(self, message: str, loan_amount: float | None = None, annual_rate: float | None = None):
        extra = ""
        if loan_amount is not None:
            extra += f" loan_amount={loan_amount}"
        if annual_rate is not None:
            extra += f" annual_rate={annual_rate}"
        super().__init__(f"[loan] {message}{extra}")


class ParameterValidationError(VideoProjectException):
    def __init__(self, message: str, parameter_name: str, value: str, expected: str):
        super().__init__(
            f"[validation] {message}; parameter={parameter_name}; value={value}; expected={expected}"
        )
