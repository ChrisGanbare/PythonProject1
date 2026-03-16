"""Unit tests for fund_fee_erosion.models.calculator."""

from __future__ import annotations

import math

import pytest

from fund_fee_erosion.models.calculator import (
    DEFAULT_SCENARIOS,
    FeeScenario,
    FundParams,
    validate_gross_return,
    validate_principal,
    validate_years,
)
from shared.core.exceptions import ParameterValidationError


# ── FundParams 基础校验 ──────────────────────────────────────

class TestFundParamsValidation:
    def test_default_construction(self, default_params: FundParams):
        assert default_params.principal == 1_000_000
        assert default_params.gross_return == 0.08
        assert default_params.years == 30

    def test_invalid_principal_zero(self):
        with pytest.raises(ParameterValidationError):
            FundParams(principal=0)

    def test_invalid_principal_negative(self):
        with pytest.raises(ParameterValidationError):
            FundParams(principal=-100)

    def test_invalid_principal_too_large(self):
        with pytest.raises(ParameterValidationError):
            FundParams(principal=2e10)

    def test_invalid_gross_return_too_high(self):
        with pytest.raises(ParameterValidationError):
            FundParams(gross_return=1.5)

    def test_invalid_gross_return_too_low(self):
        with pytest.raises(ParameterValidationError):
            FundParams(gross_return=-0.6)

    def test_invalid_years_zero(self):
        with pytest.raises(ParameterValidationError):
            FundParams(years=0)

    def test_invalid_years_too_long(self):
        with pytest.raises(ParameterValidationError):
            FundParams(years=51)


# ── 核心计算 ─────────────────────────────────────────────────

class TestFinalValue:
    def test_zero_fee_equals_compound_formula(self, default_params: FundParams):
        expected = 1_000_000 * (1.08 ** 30)
        assert math.isclose(default_params.final_value(0.0), expected, rel_tol=1e-9)

    def test_higher_fee_gives_lower_value(self, default_params: FundParams):
        v_etf    = default_params.final_value(0.0015)
        v_active = default_params.final_value(0.015)
        v_high   = default_params.final_value(0.02)
        assert default_params.final_value(0.0) > v_etf > v_active > v_high

    def test_fee_drag_is_nonnegative(self, default_params: FundParams):
        for fee in (0.0015, 0.015, 0.02):
            assert default_params.fee_drag(fee) >= 0

    def test_fee_drag_pct_in_range(self, default_params: FundParams):
        for fee in (0.0015, 0.015, 0.02):
            pct = default_params.fee_drag_pct(fee)
            assert 0.0 <= pct <= 1.0

    def test_zero_fee_gives_zero_drag(self, default_params: FundParams):
        assert math.isclose(default_params.fee_drag(0.0), 0.0, abs_tol=1e-6)

    def test_active_fund_drag_magnitude(self, default_params: FundParams):
        # 100万, 8%毛收益, 30年, 1.5%费用 → 差距应 > 200万 < 500万
        drag_wan = default_params.fee_drag(0.015) / 10_000
        assert 200 < drag_wan < 500


class TestYearlyValues:
    def test_first_value_is_principal(self, default_params: FundParams):
        vals = default_params.yearly_values(0.0)
        assert math.isclose(vals[0], default_params.principal, rel_tol=1e-9)

    def test_length_equals_years_plus_one(self, default_params: FundParams):
        vals = default_params.yearly_values(0.015)
        assert len(vals) == default_params.years + 1

    def test_monotone_increasing_positive_net_return(self, default_params: FundParams):
        vals = default_params.yearly_values(0.015)   # net 6.5%
        for i in range(len(vals) - 1):
            assert vals[i + 1] > vals[i]

    def test_last_value_matches_final_value(self, default_params: FundParams):
        fee = 0.015
        assert math.isclose(
            default_params.yearly_values(fee)[-1],
            default_params.final_value(fee),
            rel_tol=1e-9,
        )


# ── 汇总报告 ─────────────────────────────────────────────────

class TestGetSummary:
    def test_all_default_scenarios_present(self, default_params: FundParams):
        summary = default_params.get_summary()
        for s in DEFAULT_SCENARIOS:
            assert s.key in summary

    def test_summary_fields(self, default_params: FundParams):
        summary = default_params.get_summary()
        required = {
            "label", "fee_rate", "fee_rate_pct",
            "final_value", "final_value_wan",
            "fee_drag", "fee_drag_wan", "fee_drag_pct",
        }
        for row in summary.values():
            assert required.issubset(row.keys())

    def test_zero_fee_scenario_has_zero_drag(self, default_params: FundParams):
        summary = default_params.get_summary()
        assert math.isclose(summary["zero"]["fee_drag"], 0.0, abs_tol=1e-4)

    def test_custom_scenarios(self, default_params: FundParams):
        custom = [FeeScenario("my", "自定义", 0.005, "#FFFFFF")]
        summary = default_params.get_summary(scenarios=custom)
        assert list(summary.keys()) == ["my"]


# ── 独立校验函数 ─────────────────────────────────────────────

class TestValidators:
    def test_validate_principal_ok(self):
        assert validate_principal(500_000) == 500_000

    def test_validate_principal_zero_raises(self):
        with pytest.raises(ParameterValidationError):
            validate_principal(0.0)

    def test_validate_gross_return_boundary(self):
        assert validate_gross_return(-0.5) == -0.5
        assert validate_gross_return(1.0) == 1.0

    def test_validate_gross_return_out_of_range(self):
        with pytest.raises(ParameterValidationError):
            validate_gross_return(1.01)

    def test_validate_years_boundary(self):
        assert validate_years(1) == 1
        assert validate_years(50) == 50

    def test_validate_years_out_of_range(self):
        with pytest.raises(ParameterValidationError):
            validate_years(0)
        with pytest.raises(ParameterValidationError):
            validate_years(51)


# ── 整合：smoke check 逻辑 ───────────────────────────────────

class TestSmokeIntegration:
    def test_smoke_check_runs(self):
        from fund_fee_erosion.entrypoints import run_smoke_check
        result = run_smoke_check()
        assert "zero" in result
        assert "active" in result
        assert result["active"]["final_value_wan"] < result["zero"]["final_value_wan"]
