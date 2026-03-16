"""
贷款计算模型
支持等额本息、等额本金两种还款方式的精确计算
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from utils.validators import validate_loan_amount, validate_annual_rate, validate_loan_years
from models.exceptions import LoanCalculationError


@dataclass
class MonthlyPayment:
    """单月还款数据"""
    month: int
    principal: float  # 本月本金
    interest: float  # 本月利息
    total: float  # 月供总额
    remaining_balance: float  # 剩余本金余额
    cumulative_interest: float  # 累计利息

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "month": self.month,
            "principal": round(self.principal, 2),
            "interest": round(self.interest, 2),
            "total": round(self.total, 2),
            "remaining_balance": round(self.remaining_balance, 2),
            "cumulative_interest": round(self.cumulative_interest, 2),
        }


@dataclass
class LoanData:
    """贷款完整数据"""
    loan_amount: float
    annual_rate: float
    loan_years: int
    
    # 计算结果（自动计算）
    total_months: int = field(init=False)
    monthly_rate: float = field(init=False)
    
    def __post_init__(self):
        """初始化后自动计算派生属性"""
        # 参数验证
        self.loan_amount = validate_loan_amount(self.loan_amount)
        self.annual_rate = validate_annual_rate(self.annual_rate)
        self.loan_years = validate_loan_years(self.loan_years)
        
        # 计算派生属性
        self.total_months = self.loan_years * 12
        self.monthly_rate = self.annual_rate / 12

    def calculate_equal_interest(self) -> tuple[List[MonthlyPayment], float]:
        """
        等额本息计算（每月还款额相同）
        
        公式：M = P * r * (1 + r)^n / ((1 + r)^n - 1)
        其中：
            M: 月供
            P: 贷款本金
            r: 月利率
            n: 总期数
        
        Returns:
            (月���数据列表, 月供金额)
        
        Raises:
            LoanCalculationError: 计算失败
        """
        try:
            # 计算月供
            numerator = self.monthly_rate * ((1 + self.monthly_rate) ** self.total_months)
            denominator = ((1 + self.monthly_rate) ** self.total_months) - 1
            
            if denominator == 0:
                raise LoanCalculationError(
                    "分母为零，贷款参数无效",
                    self.loan_amount,
                    self.annual_rate
                )
            
            monthly_payment = self.loan_amount * numerator / denominator
            
            # 逐月计算
            payments: List[MonthlyPayment] = []
            remaining = self.loan_amount
            cumulative_interest = 0.0
            
            for month in range(1, self.total_months + 1):
                interest = remaining * self.monthly_rate
                principal = monthly_payment - interest
                remaining -= principal
                cumulative_interest += interest
                
                # 处理最后一月的舍入误差
                if month == self.total_months:
                    principal = self.loan_amount - (sum(p.principal for p in payments))
                    remaining = 0.0
                
                payment = MonthlyPayment(
                    month=month,
                    principal=principal,
                    interest=interest,
                    total=monthly_payment,
                    remaining_balance=max(0, remaining),
                    cumulative_interest=cumulative_interest,
                )
                payments.append(payment)
            
            return payments, monthly_payment
        
        except Exception as e:
            if isinstance(e, LoanCalculationError):
                raise
            raise LoanCalculationError(
                f"等额本息计算失败: {str(e)}",
                self.loan_amount,
                self.annual_rate
            )

    def calculate_equal_principal(self) -> tuple[List[MonthlyPayment], float, float]:
        """
        等额本金计算（每月本金相同）
        
        Returns:
            (月度数据列表, 首月月供, 末月月供)
        
        Raises:
            LoanCalculationError: 计算失败
        """
        try:
            # 每月本金固定
            fixed_principal = self.loan_amount / self.total_months
            
            # 逐月计算
            payments: List[MonthlyPayment] = []
            remaining = self.loan_amount
            cumulative_interest = 0.0
            
            for month in range(1, self.total_months + 1):
                interest = remaining * self.monthly_rate
                total_payment = fixed_principal + interest
                remaining -= fixed_principal
                cumulative_interest += interest
                
                payment = MonthlyPayment(
                    month=month,
                    principal=fixed_principal,
                    interest=interest,
                    total=total_payment,
                    remaining_balance=max(0, remaining),
                    cumulative_interest=cumulative_interest,
                )
                payments.append(payment)
            
            first_month_payment = payments[0].total
            last_month_payment = payments[-1].total
            
            return payments, first_month_payment, last_month_payment
        
        except Exception as e:
            if isinstance(e, LoanCalculationError):
                raise
            raise LoanCalculationError(
                f"等额本金计算失败: {str(e)}",
                self.loan_amount,
                self.annual_rate
            )

    def get_summary(self) -> Dict[str, Any]:
        """获取贷款摘要"""
        try:
            ei_payments, ei_monthly = self.calculate_equal_interest()
            ep_payments, ep_first, ep_last = self.calculate_equal_principal()
            
            ei_total_interest = ei_payments[-1].cumulative_interest
            ep_total_interest = ep_payments[-1].cumulative_interest
            interest_difference = ei_total_interest - ep_total_interest
            
            return {
                "loan_amount": self.loan_amount,
                "annual_rate": self.annual_rate,
                "loan_years": self.loan_years,
                "total_months": self.total_months,
                "equal_interest": {
                    "monthly_payment": ei_monthly,
                    "total_interest": ei_total_interest,
                    "total_repay": self.loan_amount + ei_total_interest,
                },
                "equal_principal": {
                    "first_month_payment": ep_first,
                    "last_month_payment": ep_last,
                    "total_interest": ep_total_interest,
                    "total_repay": self.loan_amount + ep_total_interest,
                },
                "comparison": {
                    "interest_difference": interest_difference,
                    "difference_percentage": (interest_difference / ei_total_interest * 100) if ei_total_interest > 0 else 0,
                    "which_is_cheaper": "等额本金" if interest_difference > 0 else "等额本息",
                },
            }
        except Exception as e:
            raise LoanCalculationError(
                f"生成摘要失败: {str(e)}",
                self.loan_amount,
                self.annual_rate
            )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "loan_amount": self.loan_amount,
            "annual_rate": self.annual_rate,
            "loan_years": self.loan_years,
            "total_months": self.total_months,
            "monthly_rate": self.monthly_rate,
        }

