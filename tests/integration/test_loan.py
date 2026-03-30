import pytest

from shared.render.core.exceptions import ParameterValidationError
from loan_comparison.models.loan import LoanData


class TestLoanDataInitialization:
    def test_valid_loan_data(self):
        loan = LoanData(
            loan_amount=1_000_000,
            annual_rate=0.045,
            loan_years=30,
        )

        assert loan.loan_amount == 1_000_000
        assert loan.annual_rate == 0.045
        assert loan.loan_years == 30
        assert loan.total_months == 360
        assert abs(loan.monthly_rate - 0.045 / 12) < 1e-6

    def test_loan_amount_too_low(self):
        with pytest.raises(ParameterValidationError):
            LoanData(loan_amount=5_000, annual_rate=0.045, loan_years=30)

    def test_loan_amount_too_high(self):
        with pytest.raises(ParameterValidationError):
            LoanData(loan_amount=20_000_000, annual_rate=0.045, loan_years=30)

    def test_annual_rate_invalid(self):
        with pytest.raises(ParameterValidationError):
            LoanData(loan_amount=1_000_000, annual_rate=0.5, loan_years=30)

    def test_loan_years_invalid(self):
        with pytest.raises(ParameterValidationError):
            LoanData(loan_amount=1_000_000, annual_rate=0.045, loan_years=50)


class TestEqualInterestCalculation:
    def test_equal_interest_basic(self, loan_data):
        payments, monthly_payment = loan_data.calculate_equal_interest()

        assert len(payments) == 360
        assert monthly_payment > 0

        for payment in payments:
            assert abs(payment.total - monthly_payment) < 1e-2

    def test_equal_interest_total_repay(self, loan_data):
        payments, _ = loan_data.calculate_equal_interest()
        total_repay = sum(p.principal for p in payments)
        assert abs(total_repay - loan_data.loan_amount) < 1

    def test_equal_interest_cumulative(self, loan_data):
        payments, _ = loan_data.calculate_equal_interest()
        last_payment = payments[-1]

        assert last_payment.cumulative_interest > 0

        total_interest = sum(p.interest for p in payments)
        assert abs(last_payment.cumulative_interest - total_interest) < 1


class TestEqualPrincipalCalculation:
    def test_equal_principal_basic(self, loan_data):
        payments, first_month, last_month = loan_data.calculate_equal_principal()

        assert len(payments) == 360
        assert first_month > last_month

        for payment in payments:
            assert abs(payment.principal - loan_data.loan_amount / 360) < 1e-2

    def test_equal_principal_total_repay(self, loan_data):
        payments, _, _ = loan_data.calculate_equal_principal()
        total_repay = sum(p.principal for p in payments)
        assert abs(total_repay - loan_data.loan_amount) < 1

    def test_equal_principal_decreasing(self, loan_data):
        payments, _, _ = loan_data.calculate_equal_principal()

        for i in range(len(payments) - 1):
            assert payments[i].total >= payments[i + 1].total


class TestComparison:
    def test_equal_principal_cheaper(self, loan_data):
        ei_payments, _ = loan_data.calculate_equal_interest()
        ep_payments, _, _ = loan_data.calculate_equal_principal()

        ei_total_interest = ei_payments[-1].cumulative_interest
        ep_total_interest = ep_payments[-1].cumulative_interest

        assert ep_total_interest < ei_total_interest

    def test_summary(self, loan_data):
        summary = loan_data.get_summary()

        assert "equal_interest" in summary
        assert "equal_principal" in summary
        assert "comparison" in summary

        comparison = summary["comparison"]
        assert comparison["interest_difference"] > 0
        assert comparison["which_is_cheaper"] == "等额本金"
