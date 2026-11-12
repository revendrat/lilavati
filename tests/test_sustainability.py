import pytest

from lilavati.core.sustainability import SustainabilityEngine
from lilavati.schemas.sustainability import SustainabilityLinkedBond


def test_waci_calculation() -> None:
    # 3-asset portfolio: weights 50%, 30%, 20%
    weights = [0.50, 0.30, 0.20]
    # Emissions in tCO2e: 50,000, 120,000, 10,000
    emissions = [50000.0, 120000.0, 10000.0]
    # Revenues in $M: $1,000M, $1,500M, $500M
    revenues = [1000.0, 1500.0, 500.0]

    result = SustainabilityEngine.calculate_waci(weights, emissions, revenues)

    # Individual intensities: 50, 80, 20
    # Weighted avg = 0.5*50 + 0.3*80 + 0.2*20 = 25 + 24 + 4 = 53.0
    assert result.waci == pytest.approx(53.0, abs=1e-3)
    assert result.carbon_intensity_clean is True  # Below 100 benchmark


def test_carbon_tax_stress_test_healthy() -> None:
    # Company with $1B revenue, $200M EBIT, $40M interest expense
    # Scope 1+2 = 200,000 tCO2e
    # Carbon tax = $50/ton, pass-through = 50%
    # Gross liability = $10M, Net cost = $5M
    # EBIT after = $195M, Interest coverage = 195 / 40 = 4.875x > 2.5x floor
    result = SustainabilityEngine.stress_test_carbon_tax(
        revenue=1000.0,
        ebit=200.0,
        interest_expense=40.0,
        scope1_emissions=120000.0,
        scope2_emissions=80000.0,
        carbon_price_per_ton=0.00005,  # $50/ton scaled to millions
        pass_through_rate=0.50,
        covenant_interest_floor=2.50,
    )

    assert result.is_covenant_at_risk is False
    assert result.net_carbon_expense == pytest.approx(5.0, abs=1e-3)
    assert result.interest_coverage_after == pytest.approx(4.875, abs=1e-3)


def test_carbon_tax_stress_test_covenant_breach() -> None:
    # Carbon-intensive utility under heavy $150/ton tax with zero pass-through
    # Revenue $500M, EBIT $60M, Interest $20M (Coverage was 3.0x)
    # Scope 1+2 = 400,000 tCO2e ($0.4M tons * $150 = $60M tax!)
    # EBIT after = $0M -> Coverage = 0.0x < 2.5x -> Breach!
    result = SustainabilityEngine.stress_test_carbon_tax(
        revenue=500.0,
        ebit=60.0,
        interest_expense=20.0,
        scope1_emissions=300000.0,
        scope2_emissions=100000.0,
        carbon_price_per_ton=0.00015,  # $150/ton in millions
        pass_through_rate=0.0,
        covenant_interest_floor=2.50,
    )

    assert result.is_covenant_at_risk is True
    assert result.ebit_margin_after_pct == pytest.approx(0.0, abs=1e-3)
    assert result.interest_coverage_after == pytest.approx(0.0, abs=1e-3)


def test_slb_covenant_spt_achieved() -> None:
    bond = SustainabilityLinkedBond(
        isin="XS2345678901",
        notional=500_000_000.0,
        base_coupon_rate=0.035,
        target_reduction_pct=0.25,  # 25% reduction target
        baseline_emissions=1_000_000.0,
        step_up_bps=25.0,  # 25 bps step-up
        target_year=2028,
    )

    # Actual emissions reported: 700,000 tCO2e (30% reduction > 25% target)
    result = SustainabilityEngine.evaluate_slb_covenant(bond, reported_emissions=700_000.0)

    assert result.spt_achieved is True
    assert result.realized_reduction_pct == pytest.approx(0.30, abs=1e-3)
    assert result.active_coupon_rate == 0.035
    assert result.annual_interest_penalty == 0.0


def test_slb_covenant_spt_missed_step_up_triggered() -> None:
    bond = SustainabilityLinkedBond(
        isin="XS2345678901",
        notional=500_000_000.0,
        base_coupon_rate=0.035,
        target_reduction_pct=0.25,
        baseline_emissions=1_000_000.0,
        step_up_bps=25.0,  # 25 bps penalty
        target_year=2028,
    )

    # Actual emissions reported: 850,000 tCO2e (only 15% reduction < 25% target)
    result = SustainabilityEngine.evaluate_slb_covenant(bond, reported_emissions=850_000.0)

    assert result.spt_achieved is False
    assert result.realized_reduction_pct == pytest.approx(0.15, abs=1e-3)
    # Coupon steps up from 3.50% to 3.75%
    assert result.active_coupon_rate == pytest.approx(0.0375, abs=1e-5)
    # 25 bps on $500M = $1,250,000 annual penalty
    assert result.annual_interest_penalty == pytest.approx(1_250_000.0, abs=1.0)
