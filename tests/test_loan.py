"""
贷款计算模块单元测试
"""

import pytest
from models.loan import LoanData, MonthlyPayment
from models.exceptions import LoanCalculationError, ParameterValidationError


class TestLoanDataInitialization:
    """贷款数据初始化测试"""
    
    def test_valid_loan_data(self):
        """测试有效的贷款数据"""
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
        """测试贷款金额过低"""
        with pytest.raises(ParameterValidationError):
            LoanData(
                loan_amount=5_000,
                annual_rate=0.045,
                loan_years=30,
            )
    
    def test_loan_amount_too_high(self):
        """测试贷款金额过高"""
        with pytest.raises(ParameterValidationError):
            LoanData(
                loan_amount=20_000_000,
                annual_rate=0.045,
                loan_years=30,
            )
    
    def test_annual_rate_invalid(self):
        """测试年利率无效"""
        with pytest.raises(ParameterValidationError):
            LoanData(
                loan_amount=1_000_000,
                annual_rate=0.5,  # 50% 太高
                loan_years=30,
            )
    
    def test_loan_years_invalid(self):
        """测试贷款期限无效"""
        with pytest.raises(ParameterValidationError):
            LoanData(
                loan_amount=1_000_000,
                annual_rate=0.045,
                loan_years=50,  # 超过最大 40 年
            )


class TestEqualInterestCalculation:
    """等额本息计算测试"""
    
    def test_equal_interest_basic(self, loan_data):
        """测试等额本息基本计算"""
        payments, monthly_payment = loan_data.calculate_equal_interest()
        
        assert len(payments) == 360
        assert monthly_payment > 0
        
        # 验证月供一致性
        for payment in payments:
            assert abs(payment.total - monthly_payment) < 1e-2
    
    def test_equal_interest_total_repay(self, loan_data):
        """测试等额本息总还款额"""
        payments, monthly_payment = loan_data.calculate_equal_interest()
        
        total_repay = sum(p.principal for p in payments)
        
        # 验证本金和等于借款额
        assert abs(total_repay - loan_data.loan_amount) < 1
    
    def test_equal_interest_cumulative(self, loan_data):
        """测试等额本息累计利息"""
        payments, _ = loan_data.calculate_equal_interest()
        
        last_payment = payments[-1]
        
        # 验证累计利息大于 0
        assert last_payment.cumulative_interest > 0
        
        # 验证累计利息 = 总利息
        total_interest = sum(p.interest for p in payments)
        assert abs(last_payment.cumulative_interest - total_interest) < 1


class TestEqualPrincipalCalculation:
    """等额本金计算测试"""
    
    def test_equal_principal_basic(self, loan_data):
        """测试等额本金基本计算"""
        payments, first_month, last_month = loan_data.calculate_equal_principal()
        
        assert len(payments) == 360
        assert first_month > last_month  # 首月高于末月
        
        # 验证本金一致
        for payment in payments:
            assert abs(payment.principal - loan_data.loan_amount / 360) < 1e-2
    
    def test_equal_principal_total_repay(self, loan_data):
        """测试等额本金总还款额"""
        payments, _, _ = loan_data.calculate_equal_principal()
        
        total_repay = sum(p.principal for p in payments)
        
        # 验证本金和等于借款额
        assert abs(total_repay - loan_data.loan_amount) < 1
    
    def test_equal_principal_decreasing(self, loan_data):
        """测试等额本金月供递减"""
        payments, _, _ = loan_data.calculate_equal_principal()
        
        # 验证月供递减
        for i in range(len(payments) - 1):
            assert payments[i].total >= payments[i + 1].total


class TestComparison:
    """两种方案对比测试"""
    
    def test_equal_principal_cheaper(self, loan_data):
        """测试等额本金总利息更少"""
        ei_payments, _ = loan_data.calculate_equal_interest()
        ep_payments, _, _ = loan_data.calculate_equal_principal()
        
        ei_total_interest = ei_payments[-1].cumulative_interest
        ep_total_interest = ep_payments[-1].cumulative_interest
        
        # 等额本金应该总利息少
        assert ep_total_interest < ei_total_interest
    
    def test_summary(self, loan_data):
        """测试摘要生成"""
        summary = loan_data.get_summary()
        
        assert "equal_interest" in summary
        assert "equal_principal" in summary
        assert "comparison" in summary
        
        # 验证对比数据
        comparison = summary["comparison"]
        assert comparison["interest_difference"] > 0
        assert comparison["which_is_cheaper"] == "等额本金"

