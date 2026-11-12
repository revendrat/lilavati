"""
Forensic Financial Accounting & Distress Detection Engine.

Implements:
1. The Beneish M-Score (8-variable model to detect earnings manipulation).
2. The Altman Z-Score (bankruptcy and financial distress prediction).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BeneishMScoreResult(BaseModel):
    """Result of Beneish M-Score earnings manipulation analysis."""

    model_config = ConfigDict(frozen=True)

    m_score: float = Field(
        ...,
        description="Overall Beneish M-Score (values > -1.78 indicate high risk of manipulation)",
    )
    is_likely_manipulator: bool = Field(..., description="True if M-Score > -1.78")
    dsri: float = Field(..., description="Days Sales in Receivables Index")
    gmi: float = Field(..., description="Gross Margin Index")
    aqi: float = Field(..., description="Asset Quality Index")
    sgi: float = Field(..., description="Sales Growth Index")
    depi: float = Field(..., description="Depreciation Index")
    sgai: float = Field(..., description="Sales, General and Administrative expenses Index")
    lvgi: float = Field(..., description="Leverage Index")
    tata: float = Field(..., description="Total Accruals to Total Assets")
    risk_assessment: str


class AltmanZScoreResult(BaseModel):
    """Result of Altman Z-Score credit distress prediction."""

    model_config = ConfigDict(frozen=True)

    z_score: float = Field(..., description="Altman Z-Score value")
    distress_zone: str = Field(
        ..., description="'Distress' (<1.81), 'Grey' (1.81-2.99), or 'Safe' (>2.99)"
    )
    working_capital_to_assets: float
    retained_earnings_to_assets: float
    ebit_to_assets: float
    market_equity_to_liabilities: float
    sales_to_assets: float


class ForensicEngine:
    """Deterministic calculations for financial forensics and solvency."""

    @staticmethod
    def calculate_beneish_m_score(
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
    ) -> BeneishMScoreResult:
        """
        Calculates the complete 8-variable Beneish M-Score:
        M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 0.115*DEPI - 0.172*SGAI + 4.037*TATA + 0.0327*LVGI
        """
        # DSRI: Days Sales in Receivables Index
        dsri = (receivables_t / revenue_t) / (receivables_t_minus_1 / revenue_t_minus_1)

        # GMI: Gross Margin Index
        gm_t_minus_1 = (revenue_t_minus_1 - cogs_t_minus_1) / revenue_t_minus_1
        gm_t = (revenue_t - cogs_t) / revenue_t
        gmi = gm_t_minus_1 / gm_t if gm_t != 0 else 1.0

        # AQI: Asset Quality Index
        denom_aqi = 1.0 - (current_assets_t_minus_1 + ppe_t_minus_1) / total_assets_t_minus_1
        numer_aqi = 1.0 - (current_assets_t + ppe_t) / total_assets_t
        aqi = (numer_aqi / denom_aqi) if (denom_aqi != 0 and total_assets_t_minus_1 > 0) else 1.0

        # SGI: Sales Growth Index
        sgi = revenue_t / revenue_t_minus_1

        # DEPI: Depreciation Index
        depr_rate_t_minus_1 = depreciation_t_minus_1 / (ppe_t_minus_1 + depreciation_t_minus_1)
        depr_rate_t = depreciation_t / (ppe_t + depreciation_t)
        depi = depr_rate_t_minus_1 / depr_rate_t if depr_rate_t > 0 else 1.0

        # SGAI: Sales, General and Administrative Expenses Index
        sgai = (sga_t / revenue_t) / (sga_t_minus_1 / revenue_t_minus_1)

        # LVGI: Leverage Index
        leverage_t = (long_term_debt_t + current_liabilities_t) / total_assets_t
        leverage_t_minus_1 = (
            long_term_debt_t_minus_1 + current_liabilities_t_minus_1
        ) / total_assets_t_minus_1
        lvgi = leverage_t / leverage_t_minus_1 if leverage_t_minus_1 > 0 else 1.0

        # TATA: Total Accruals to Total Assets
        total_accruals = net_income_t - cfo_t
        tata = total_accruals / total_assets_t

        # Beneish M-Score Formula
        m_score = (
            -4.84
            + 0.920 * dsri
            + 0.528 * gmi
            + 0.404 * aqi
            + 0.892 * sgi
            + 0.115 * depi
            - 0.172 * sgai
            + 4.037 * tata
            + 0.0327 * lvgi
        )

        is_manip = m_score > -1.78
        assessment = (
            f"HIGH RISK (M-Score: {m_score:.2f} > -1.78): Financial statements exhibit patterns consistent with earnings manipulation."
            if is_manip
            else f"LOW RISK (M-Score: {m_score:.2f} <= -1.78): Financial reporting quality appears healthy."
        )

        return BeneishMScoreResult(
            m_score=float(m_score),
            is_likely_manipulator=is_manip,
            dsri=float(dsri),
            gmi=float(gmi),
            aqi=float(aqi),
            sgi=float(sgi),
            depi=float(depi),
            sgai=float(sgai),
            lvgi=float(lvgi),
            tata=float(tata),
            risk_assessment=assessment,
        )

    @staticmethod
    def calculate_altman_z_score(
        working_capital: float,
        total_assets: float,
        retained_earnings: float,
        ebit: float,
        market_value_equity: float,
        total_liabilities: float,
        sales: float,
    ) -> AltmanZScoreResult:
        """
        Calculates the Altman Z-Score for manufacturing/corporate firms:
        Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 0.999*X5
        """
        x1 = working_capital / total_assets
        x2 = retained_earnings / total_assets
        x3 = ebit / total_assets
        x4 = market_value_equity / total_liabilities
        x5 = sales / total_assets

        z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 0.999 * x5

        if z < 1.81:
            zone = "Distress"
        elif z <= 2.99:
            zone = "Grey"
        else:
            zone = "Safe"

        return AltmanZScoreResult(
            z_score=float(z),
            distress_zone=zone,
            working_capital_to_assets=float(x1),
            retained_earnings_to_assets=float(x2),
            ebit_to_assets=float(x3),
            market_equity_to_liabilities=float(x4),
            sales_to_assets=float(x5),
        )
