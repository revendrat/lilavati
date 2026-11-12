from lilavati.agents.committee import (
    AdversarialCommittee,
    CommitteeRecommendation,
)


def test_committee_healthy_firm_approved() -> None:
    # A financially healthy growth firm (e.g. similar to Apple or Microsoft)
    memo = AdversarialCommittee.evaluate_company(
        symbol="HEALTHY_CORP",
        fiscal_year=2024,
        bull_revenue_growth_target=0.10,
        revenue_t=1200.0,
        revenue_t_minus_1=1000.0,  # 20% growth > 10% target
        cogs_t=600.0,
        cogs_t_minus_1=500.0,
        receivables_t=180.0,
        receivables_t_minus_1=150.0,
        current_assets_t=500.0,
        current_assets_t_minus_1=450.0,
        ppe_t=800.0,
        ppe_t_minus_1=750.0,
        total_assets_t=1600.0,
        total_assets_t_minus_1=1450.0,
        depreciation_t=60.0,
        depreciation_t_minus_1=55.0,
        sga_t=180.0,
        sga_t_minus_1=150.0,
        long_term_debt_t=200.0,
        long_term_debt_t_minus_1=200.0,
        current_liabilities_t=150.0,
        current_liabilities_t_minus_1=140.0,
        net_income_t=250.0,
        cfo_t=280.0,  # Healthy CFO > Net Income
        cfi_t=-100.0,
        cff_t=-80.0,
        market_value_equity=3500.0,  # High market cap
    )

    assert memo.recommendation == CommitteeRecommendation.APPROVED_BUY
    assert memo.formal_invariants_satisfied is True
    assert memo.beneish_m_score.is_likely_manipulator is False
    assert memo.altman_z_score.distress_zone == "Safe"
    assert len(memo.bear_concerns) == 0


def test_committee_earnings_manipulator_rejected() -> None:
    # A firm with aggressive channel stuffing and ballooning accruals (Enron style)
    # Revenue jumped from 1000 to 1800, but receivables exploded from 100 to 600!
    # Net income reported as 300, but CFO is actually negative (-50)!
    memo = AdversarialCommittee.evaluate_company(
        symbol="SHADY_INC",
        fiscal_year=2024,
        bull_revenue_growth_target=0.15,
        revenue_t=1800.0,
        revenue_t_minus_1=1000.0,
        cogs_t=1100.0,
        cogs_t_minus_1=600.0,
        receivables_t=600.0,  # Huge receivables spike
        receivables_t_minus_1=100.0,
        current_assets_t=800.0,
        current_assets_t_minus_1=300.0,
        ppe_t=500.0,
        ppe_t_minus_1=500.0,
        total_assets_t=1800.0,
        total_assets_t_minus_1=1000.0,
        depreciation_t=20.0,
        depreciation_t_minus_1=40.0,
        sga_t=200.0,
        sga_t_minus_1=150.0,
        long_term_debt_t=600.0,
        long_term_debt_t_minus_1=200.0,
        current_liabilities_t=300.0,
        current_liabilities_t_minus_1=100.0,
        net_income_t=300.0,
        cfo_t=-50.0,  # Severe cash-to-earnings divergence!
        cfi_t=-50.0,
        cff_t=100.0,
        market_value_equity=1200.0,
    )

    # Must be rejected due to forensic accounting anomalies!
    assert memo.recommendation == CommitteeRecommendation.REJECTED_ACCOUNTING_ANOMALY
    assert memo.beneish_m_score.is_likely_manipulator is True
    assert any("Beneish M-Score" in c for c in memo.bear_concerns)
    assert any("channel stuffing" in c for c in memo.bear_concerns)
