from lilavati.mcp_servers.sustainability_server import (
    calculate_portfolio_carbon_intensity,
    evaluate_sustainability_linked_bond_covenant,
    stress_test_carbon_tax_impact,
)


def test_mcp_waci_tool() -> None:
    res = calculate_portfolio_carbon_intensity(
        weights=[0.6, 0.4],
        emissions=[60000.0, 40000.0],
        revenues_millions=[1000.0, 500.0],
    )
    assert "waci" in res
    assert res["waci"] > 0.0


def test_mcp_carbon_tax_tool() -> None:
    res = stress_test_carbon_tax_impact(
        revenue=1000.0,
        ebit=200.0,
        interest_expense=30.0,
        scope1_emissions=100000.0,
        scope2_emissions=50000.0,
        carbon_price_per_ton=0.00005,
    )
    assert "net_carbon_expense" in res
    assert "interest_coverage_after" in res
    assert res["is_covenant_at_risk"] is False


def test_mcp_slb_tool() -> None:
    res = evaluate_sustainability_linked_bond_covenant(
        isin="XS1122334455",
        notional=100_000_000.0,
        base_coupon_rate=0.04,
        target_reduction_pct=0.20,
        baseline_emissions=500_000.0,
        step_up_bps=25.0,
        target_year=2028,
        reported_emissions=350_000.0,  # 30% reduction > 20%
    )
    assert res["spt_achieved"] is True
    assert res["active_coupon_rate"] == 0.04
