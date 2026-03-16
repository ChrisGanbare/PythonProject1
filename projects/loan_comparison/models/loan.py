"""Loan calculation model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.core.exceptions import LoanCalculationError
from loan_comparison.models.validators import (
    validate_annual_rate,
    validate_loan_amount,
    validate_loan_years,
)


@dataclass
class MonthlyPayment:
    month: int
    principal: float
    interest: float
    total: float
    remaining_balance: float
    cumulative_interest: float

    def to_dict(self) -> dict[str, Any]:
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
    loan_amount: float
    annual_rate: float
    loan_years: int

    total_months: int = field(init=False)
    monthly_rate: float = field(init=False)

    def __post_init__(self) -> None:
        self.loan_amount = validate_loan_amount(self.loan_amount)
        self.annual_rate = validate_annual_rate(self.annual_rate)
        self.loan_years = validate_loan_years(self.loan_years)

        self.total_months = self.loan_years * 12
        self.monthly_rate = self.annual_rate / 12

    def calculate_equal_interest(self) -> tuple[list[MonthlyPayment], float]:
        try:
            monthly_payment = (
                self.loan_amount
                * self.monthly_rate
                * (1 + self.monthly_rate) ** self.total_months
                / ((1 + self.monthly_rate) ** self.total_months - 1)
            )

            payments: list[MonthlyPayment] = []
            remaining = self.loan_amount
            cumulative_interest = 0.0
            paid_principal = 0.0

            for month in range(1, self.total_months + 1):
                interest = remaining * self.monthly_rate
                principal = monthly_payment - interest

                if month == self.total_months:
                    principal = self.loan_amount - paid_principal

                paid_principal += principal
                remaining = max(0.0, self.loan_amount - paid_principal)
                cumulative_interest += interest

                payments.append(
                    MonthlyPayment(
                        month=month,
                        principal=principal,
                        interest=interest,
                        total=monthly_payment,
                        remaining_balance=remaining,
                        cumulative_interest=cumulative_interest,
                    )
                )

            return payments, monthly_payment
        except Exception as exc:
            raise LoanCalculationError(
                f"equal interest calculation failed: {exc}",
                self.loan_amount,
                self.annual_rate,
            ) from exc

    def calculate_equal_principal(self) -> tuple[list[MonthlyPayment], float, float]:
        try:
            principal_per_month = self.loan_amount / self.total_months
            payments: list[MonthlyPayment] = []
            remaining = self.loan_amount
            cumulative_interest = 0.0

            for month in range(1, self.total_months + 1):
                interest = remaining * self.monthly_rate
                total = principal_per_month + interest
                remaining = max(0.0, remaining - principal_per_month)
                cumulative_interest += interest

                payments.append(
                    MonthlyPayment(
                        month=month,
                        principal=principal_per_month,
                        interest=interest,
                        total=total,
                        remaining_balance=remaining,
                        cumulative_interest=cumulative_interest,
                    )
                )

            return payments, payments[0].total, payments[-1].total
        except Exception as exc:
            raise LoanCalculationError(
                f"equal principal calculation failed: {exc}",
                self.loan_amount,
                self.annual_rate,
            ) from exc

    def get_summary(self) -> dict[str, Any]:
        equal_interest_payments, equal_interest_monthly = self.calculate_equal_interest()
        equal_principal_payments, first_month, last_month = self.calculate_equal_principal()

        ei_total_interest = equal_interest_payments[-1].cumulative_interest
        ep_total_interest = equal_principal_payments[-1].cumulative_interest
        diff = ei_total_interest - ep_total_interest

        return {
            "loan_amount": self.loan_amount,
            "annual_rate": self.annual_rate,
            "loan_years": self.loan_years,
            "total_months": self.total_months,
            "equal_interest": {
                "monthly_payment": equal_interest_monthly,
                "total_interest": ei_total_interest,
                "total_repay": self.loan_amount + ei_total_interest,
            },
            "equal_principal": {
                "first_month_payment": first_month,
                "last_month_payment": last_month,
                "total_interest": ep_total_interest,
                "total_repay": self.loan_amount + ep_total_interest,
            },
            "comparison": {
                "interest_difference": diff,
                "difference_percentage": (diff / ei_total_interest * 100) if ei_total_interest else 0.0,
                "which_is_cheaper": "等额本金" if diff > 0 else "等额本息",
            },
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "loan_amount": self.loan_amount,
            "annual_rate": self.annual_rate,
            "loan_years": self.loan_years,
            "total_months": self.total_months,
            "monthly_rate": self.monthly_rate,
        }
