from lilavati.mcp_servers.committee_server import (
    compute_forensic_beneish_m_score,
    evaluate_investment_committee_memo,
)


def test_mcp_beneish_tool() -> None:
    res = compute_forensic_beneish_m_score(
        revenue_t=1000.0,
        revenue_t_minus_1=900.0,
        cogs_t=500.0,
        cogs_t_minus_1=450.0,
        receivables_t=120.0,
        receivables_t_minus_1=110.0,
        current_assets_t=400.0,
        current_assets_t_minus_1=350.0,
        ppe_t=600.0,
        ppe_t_minus_1=550.0,
        total_assets_t=1200.0,
        total_assets_t_minus_1=1100.0,
        depreciation_t=50.0,
        depreciation_t_minus_1=45.0,
        sga_t=150.0,
        sga_t_minus_1=140.0,
        long_term_debt_t=200.0,
        long_term_debt_t_minus_1=200.0,
        current_liabilities_t=100.0,
        current_liabilities_t_minus_1=90.0,
        net_income_t=150.0,
        cfo_t=180.0,
    )
    assert "m_score" in res
    assert "is_likely_manipulator" in res
    assert res["is_likely_manipulator"] is False


def test_mcp_committee_memo_tool() -> None:
    res = evaluate_investment_committee_memo(
        symbol="ACME",
        fiscal_year=2024,
        bull_revenue_growth_target=0.08,
        revenue_t=1100.0,
        revenue_t_minus_1=1000.0,
        cogs_t=550.0,
        cogs_t_minus_1=500.0,
        receivables_t=110.0,
        receivables_t_minus_1=100.0,
        current_assets_t=450.0,
        current_assets_t_minus_1=400.0,
        ppe_t=700.0,
        ppe_t_minus_1=650.0,
        total_assets_t=1400.0,
        total_assets_t_minus_1=1300.0,
        depreciation_t=50.0,
        depreciation_t_minus_1=45.0,
        sga_t=150.0,
        sga_t_minus_1=140.0,
        long_term_debt_t=200.0,
        long_term_debt_t_minus_1=200.0,
        current_liabilities_t=100.0,
        current_liabilities_t_minus_1=90.0,
        net_income_t=200.0,
        cfo_t=220.0,
        cfi_t=-80.0,
        cff_t=-50.0,
        market_value_equity=2500.0,
    )
    assert "recommendation" in res
    assert "formal_invariants_satisfied" in res
    assert res["formal_invariants_satisfied"] is True
