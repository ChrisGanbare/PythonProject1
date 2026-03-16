"""基金手续费复利侵蚀计算模型。

核心公式：终值 = 本金 × (1 + 毛收益率 - 年费率) ^ 年限
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from shared.core.exceptions import ParameterValidationError


# ── 费用场景定义 ──────────────────────────────────────────────

@dataclass(frozen=True)
class FeeScenario:
    key: str
    label: str
    fee_rate: float   # 年费率，如 0.0015 代表 0.15%
    color: str        # 图表颜色（hex）


DEFAULT_SCENARIOS: List[FeeScenario] = [
    FeeScenario("zero",   "无费用基准",        0.0000, "#22D47E"),
    FeeScenario("etf",    "ETF  0.15%/年",     0.0015, "#4F9EFF"),
    FeeScenario("active", "主动基金  1.5%/年", 0.0150, "#FF7F35"),
    FeeScenario("high",   "高费用  2.0%/年",   0.0200, "#F43F5E"),
]


# ── 参数校验 ──────────────────────────────────────────────────

def validate_principal(value: float) -> float:
    if value <= 0:
        raise ParameterValidationError("参数不合法", "principal", str(value), "> 0")
    if value > 1e10:
        raise ParameterValidationError("参数不合法", "principal", str(value), "<= 1e10")
    return value


def validate_gross_return(value: float) -> float:
    if not (-0.5 <= value <= 1.0):
        raise ParameterValidationError(
            "参数不合法", "gross_return", str(value), "-0.5 ~ 1.0"
        )
    return value


def validate_years(value: int) -> int:
    if not (1 <= value <= 50):
        raise ParameterValidationError("参数不合法", "years", str(value), "1 ~ 50")
    return value


# ── 主计算类 ──────────────────────────────────────────────────

@dataclass
class FundParams:
    """基金投资参数。"""

    principal: float = 1_000_000.0  # 初始本金（元）
    gross_return: float = 0.08      # 年化毛收益率（小数）
    years: int = 30                 # 投资年限

    def __post_init__(self) -> None:
        self.principal = validate_principal(float(self.principal))
        self.gross_return = validate_gross_return(float(self.gross_return))
        self.years = validate_years(int(self.years))

    # ── 单场景计算 ────────────────────────────────────────────

    def final_value(self, fee_rate: float = 0.0) -> float:
        """扣除年费后的最终资产值（元）。"""
        net_rate = self.gross_return - fee_rate
        return self.principal * (1 + net_rate) ** self.years

    def yearly_values(self, fee_rate: float = 0.0) -> List[float]:
        """返回各年末资产值列表（含第 0 年 = 本金），共 years+1 个元素。"""
        net_rate = self.gross_return - fee_rate
        return [self.principal * (1 + net_rate) ** y for y in range(self.years + 1)]

    def fee_drag(self, fee_rate: float) -> float:
        """相对于无费用基准，实际损失的金额（元）。"""
        return self.final_value(0.0) - self.final_value(fee_rate)

    def fee_drag_pct(self, fee_rate: float) -> float:
        """费用侵蚀占无费用基准终值的比例（0~1）。"""
        baseline = self.final_value(0.0)
        if baseline == 0:
            return 0.0
        return self.fee_drag(fee_rate) / baseline

    # ── 多场景汇总 ────────────────────────────────────────────

    def get_summary(
        self,
        scenarios: List[FeeScenario] | None = None,
    ) -> dict:
        """返回所有场景的对比汇总字典。"""
        scenarios = scenarios or DEFAULT_SCENARIOS
        result: dict = {}
        for s in scenarios:
            fv = self.final_value(s.fee_rate)
            result[s.key] = {
                "label": s.label,
                "fee_rate": s.fee_rate,
                "fee_rate_pct": f"{s.fee_rate * 100:.2f}%",
                "final_value": round(fv, 2),
                "final_value_wan": round(fv / 10_000, 2),
                "fee_drag": round(self.fee_drag(s.fee_rate), 2),
                "fee_drag_wan": round(self.fee_drag(s.fee_rate) / 10_000, 2),
                "fee_drag_pct": round(self.fee_drag_pct(s.fee_rate) * 100, 2),
            }
        return result
