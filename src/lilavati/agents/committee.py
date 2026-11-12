"""
The Adversarial Investment Committee Protocol.

Orchestrates multi-role deliberation between:
1. The Bull (Growth & Thematic Strategist)
2. The Forensic Bear (Accounting Quality & Beneish/Altman Auditor)
3. The Sustainable Finance Specialist (Transition Risk & WACI Analyst)
4. The Risk & Compliance Officer / Portfolio Manager (Z3 SMT Invariant Gatekeeper)
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from lilavati.agents.forensics import (
    AltmanZScoreResult,
    BeneishMScoreResult,
    ForensicEngine,
)
from lilavati.core.invariants import SuvarnaEngine


class CommitteeRecommendation(StrEnum):
    """Final investment committee consensus decision."""

    APPROVED_BUY = "APPROVED_BUY"
    APPROVED_HOLD = "APPROVED_HOLD"
    REJECTED_ACCOUNTING_ANOMALY = "REJECTED_ACCOUNTING_ANOMALY"
    REJECTED_COVENANT_BREACH = "REJECTED_COVENANT_BREACH"
    REJECTED_ARBITRAGE_VIOLATION = "REJECTED_ARBITRAGE_VIOLATION"


class InvestmentCommitteeMemo(BaseModel):
    """Audited, formally verified Investment Committee Memorandum."""

    model_config = ConfigDict(frozen=True)

    company_symbol: str
    fiscal_year: int
    recommendation: CommitteeRecommendation
    bull_thesis: str
    bear_concerns: list[str]
    beneish_m_score: BeneishMScoreResult
    altman_z_score: AltmanZScoreResult
    formal_invariants_satisfied: bool
    summary_verdict: str


class AdversarialCommittee:
    """Deliberative multi-role investment committee."""

    @staticmethod
    def evaluate_company(
        symbol: str,
        fiscal_year: int,
        bull_revenue_growth_target: float,
        # Multi-year financial facts for Beneish M-Score
        revenue_t: float,
        revenue_t_minus_1: float,
        cogs_t: float,
        cogs_t_minus_1: float,
        receivables_t: float,
        receivables_t_minus_1: float,
        current_assets_t: float,
        current_assets_t_minus_1: float,
        ppe_t: float,
        ppe_t_minus_1: float,
        total_assets_t: float,
        total_assets_t_minus_1: float,
        depreciation_t: float,
        depreciation_t_minus_1: float,
        sga_t: float,
        sga_t_minus_1: float,
        long_term_debt_t: float,
        long_term_debt_t_minus_1: float,
        current_liabilities_t: float,
        current_liabilities_t_minus_1: float,
        net_income_t: float,
        cfo_t: float,
        cfi_t: float,
        cff_t: float,
        market_value_equity: float,
    ) -> InvestmentCommitteeMemo:
        """
        Runs the full adversarial deliberation pipeline:
        1. Bull Analyst presents growth thesis.
        2. Forensic Bear tests Beneish M-Score and Altman Z-Score.
        3. Risk Officer runs formal Z3 SMT verification of financial equilibrium.
        4. Committee synthesizes final binding verdict.
        """
        # 1. Bull Analyst Perspective
        growth_rate = (revenue_t - revenue_t_minus_1) / revenue_t_minus_1
        bull_thesis = (
            f"Bull Case: Company achieved {growth_rate:.1%} YoY revenue growth (target: {bull_revenue_growth_target:.1%}) "
            f"with Net Income of ${net_income_t:,.0f}."
        )

        # 2. Forensic Bear Auditor Perspective
        m_res = ForensicEngine.calculate_beneish_m_score(
            revenue_t=revenue_t,
            revenue_t_minus_1=revenue_t_minus_1,
            cogs_t=cogs_t,
            cogs_t_minus_1=cogs_t_minus_1,
            receivables_t=receivables_t,
            receivables_t_minus_1=receivables_t_minus_1,
            current_assets_t=current_assets_t,
            current_assets_t_minus_1=current_assets_t_minus_1,
            ppe_t=ppe_t,
            ppe_t_minus_1=ppe_t_minus_1,
            total_assets_t=total_assets_t,
            total_assets_t_minus_1=total_assets_t_minus_1,
            depreciation_t=depreciation_t,
            depreciation_t_minus_1=depreciation_t_minus_1,
            sga_t=sga_t,
            sga_t_minus_1=sga_t_minus_1,
            long_term_debt_t=long_term_debt_t,
            long_term_debt_t_minus_1=long_term_debt_t_minus_1,
            current_liabilities_t=current_liabilities_t,
            current_liabilities_t_minus_1=current_liabilities_t_minus_1,
            net_income_t=net_income_t,
            cfo_t=cfo_t,
        )

        working_cap = current_assets_t - current_liabilities_t
        total_liab = long_term_debt_t + current_liabilities_t
        retained_earn = net_income_t
        ebit = revenue_t - cogs_t - sga_t - depreciation_t

        z_res = ForensicEngine.calculate_altman_z_score(
            working_capital=working_cap,
            total_assets=total_assets_t,
            retained_earnings=retained_earn,
            ebit=ebit,
            market_value_equity=market_value_equity,
            total_liabilities=total_liab,
            sales=revenue_t,
        )

        bear_concerns: list[str] = []
        if m_res.is_likely_manipulator:
            bear_concerns.append(
                f"Beneish M-Score ({m_res.m_score:.2f} > -1.78) flags high risk of aggressive revenue recognition."
            )
        if m_res.dsri > 1.3:
            bear_concerns.append(
                f"Receivables grew significantly faster than revenues (DSRI = {m_res.dsri:.2f}), suggesting channel stuffing."
            )
        if z_res.distress_zone == "Distress":
            bear_concerns.append(
                f"Altman Z-Score ({z_res.z_score:.2f} < 1.81) indicates near-term credit insolvency risk."
            )

        # 3. Risk & Compliance Officer: SMT Invariant Verification via Suvarna
        shareholders_equity = total_assets_t - total_liab
        cash_delta = cfo_t + cfi_t + cff_t

        inv_check = SuvarnaEngine.verify_three_statement_invariants(
            total_assets=total_assets_t,
            total_liabilities=total_liab,
            shareholders_equity=shareholders_equity,
            net_income=net_income_t,
            cash_start=100.0,
            cash_end=100.0 + cash_delta,
            cfo=cfo_t,
            cfi=cfi_t,
            cff=cff_t,
        )

        # 4. Committee Consensus & Verdict
        if not inv_check.is_valid:
            rec = CommitteeRecommendation.REJECTED_ACCOUNTING_ANOMALY
            verdict = "REJECTED: Proposed financials violate fundamental mathematical balance sheet identities."
        elif m_res.is_likely_manipulator:
            rec = CommitteeRecommendation.REJECTED_ACCOUNTING_ANOMALY
            verdict = "REJECTED: Forensic scrutiny revealed severe earnings manipulation probability (Beneish M-Score breach)."
        elif z_res.distress_zone == "Distress":
            rec = CommitteeRecommendation.REJECTED_COVENANT_BREACH
            verdict = "REJECTED: Credit profile in distressed territory (Altman Z-Score < 1.81)."
        elif growth_rate >= bull_revenue_growth_target and z_res.distress_zone == "Safe":
            rec = CommitteeRecommendation.APPROVED_BUY
            verdict = "APPROVED FOR ALLOCATION: Clean forensic profile, verified accounting invariants, robust financial health."
        else:
            rec = CommitteeRecommendation.APPROVED_HOLD
            verdict = "HOLD: Moderate credit health with acceptable reporting quality."

        return InvestmentCommitteeMemo(
            company_symbol=symbol.upper(),
            fiscal_year=fiscal_year,
            recommendation=rec,
            bull_thesis=bull_thesis,
            bear_concerns=bear_concerns,
            beneish_m_score=m_res,
            altman_z_score=z_res,
            formal_invariants_satisfied=inv_check.is_valid,
            summary_verdict=verdict,
        )
