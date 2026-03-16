"""
参数验证工具函数
"""

from typing import Union, Optional
from models.exceptions import ParameterValidationError


def validate_loan_amount(amount: Union[int, float]) -> float:
    """
    验证贷款金额
    
    Args:
        amount: 贷款金额（元）
    
    Returns:
        验证后的金额
    
    Raises:
        ParameterValidationError: 验证失败
    """
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ParameterValidationError(
            "贷款金额必须是数字",
            "loan_amount",
            str(amount),
            "float (> 10000)"
        )
    
    if amount < 10_000:
        raise ParameterValidationError(
            "贷款金额不能低于 10,000 元",
            "loan_amount",
            str(amount),
            ">= 10000"
        )
    
    if amount > 10_000_000:
        raise ParameterValidationError(
            "贷款金额不能超过 1000 万元",
            "loan_amount",
            str(amount),
            "<= 10000000"
        )
    
    return amount


def validate_annual_rate(rate: Union[int, float]) -> float:
    """
    验证年利率
    
    Args:
        rate: 年利率（小数，如 0.045 表示 4.5%）
    
    Returns:
        验证后的利率
    
    Raises:
        ParameterValidationError: 验证失败
    """
    try:
        rate = float(rate)
    except (TypeError, ValueError):
        raise ParameterValidationError(
            "年利率必须是数字",
            "annual_rate",
            str(rate),
            "float (0.001 - 0.2)"
        )
    
    if rate < 0.001:
        raise ParameterValidationError(
            "年利率不能低于 0.1%",
            "annual_rate",
            f"{rate * 100:.2f}%",
            ">= 0.001"
        )
    
    if rate > 0.2:
        raise ParameterValidationError(
            "年利率不能超过 20%",
            "annual_rate",
            f"{rate * 100:.2f}%",
            "<= 0.2"
        )
    
    return rate


def validate_loan_years(years: Union[int, float]) -> int:
    """
    验证贷款期限
    
    Args:
        years: 贷款期限（年）
    
    Returns:
        验证后的期限
    
    Raises:
        ParameterValidationError: 验证失败
    """
    try:
        years = int(years)
    except (TypeError, ValueError):
        raise ParameterValidationError(
            "贷款期限必须是整数",
            "loan_years",
            str(years),
            "int (1 - 40)"
        )
    
    if years < 1:
        raise ParameterValidationError(
            "贷款期限不能低于 1 年",
            "loan_years",
            str(years),
            ">= 1"
        )
    
    if years > 40:
        raise ParameterValidationError(
            "贷款期限不能超过 40 年",
            "loan_years",
            str(years),
            "<= 40"
        )
    
    return years


def validate_color_hex(color: str) -> str:
    """
    验证十六进制颜色代码
    
    Args:
        color: 颜色代码（如 '#FF5733'）
    
    Returns:
        验证后的颜色代码
    
    Raises:
        ParameterValidationError: 验证失败
    """
    color = str(color).strip()
    
    if not color.startswith('#'):
        raise ParameterValidationError(
            "颜色代码必须以 '#' 开头",
            "color",
            color,
            "#RRGGBB"
        )
    
    if len(color) != 7:
        raise ParameterValidationError(
            "颜色代码长度必须为 7（#RRGGBB）",
            "color",
            color,
            "#RRGGBB"
        )
    
    try:
        int(color[1:], 16)
    except ValueError:
        raise ParameterValidationError(
            "颜色代码必须包含有效的十六进制字符",
            "color",
            color,
            "#RRGGBB"
        )
    
    return color


def validate_fps(fps: int) -> int:
    """
    验证帧率
    
    Args:
        fps: 帧率（每秒帧数）
    
    Returns:
        验证后的帧率
    
    Raises:
        ParameterValidationError: 验证失败
    """
    try:
        fps = int(fps)
    except (TypeError, ValueError):
        raise ParameterValidationError(
            "帧率必须是整数",
            "fps",
            str(fps),
            "int (24/25/30/60)"
        )
    
    valid_fps_values = [24, 25, 30, 60]
    if fps not in valid_fps_values:
        raise ParameterValidationError(
            f"帧率必须为 {'/'.join(map(str, valid_fps_values))} 之一",
            "fps",
            str(fps),
            " / ".join(map(str, valid_fps_values))
        )
    
    return fps


def validate_resolution(width: int, height: int) -> tuple[int, int]:
    """
    验证视频分辨率
    
    Args:
        width: 宽度（像素）
        height: 高度（像素）
    
    Returns:
        (width, height) 元组
    
    Raises:
        ParameterValidationError: 验证失败
    """
    try:
        width = int(width)
        height = int(height)
    except (TypeError, ValueError):
        raise ParameterValidationError(
            "分辨率必须是整数",
            "resolution",
            f"{width}x{height}",
            "int x int"
        )
    
    min_resolution = 480
    max_resolution = 4096
    
    if width < min_resolution or height < min_resolution:
        raise ParameterValidationError(
            f"分辨率不能低于 {min_resolution}x{min_resolution}",
            "resolution",
            f"{width}x{height}",
            f">= {min_resolution}"
        )
    
    if width > max_resolution or height > max_resolution:
        raise ParameterValidationError(
            f"分辨率不能超过 {max_resolution}x{max_resolution}",
            "resolution",
            f"{width}x{height}",
            f"<= {max_resolution}"
        )
    
    return width, height

