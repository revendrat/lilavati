"""
FastMCP Server for the Adversarial Investment Committee & Forensic Accounting.

Exposes multi-agent deliberation, Beneish M-Score manipulation detection,
and Altman Z-Score distress analysis over FastMCP.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from lilavati.agents.committee import AdversarialCommittee
from lilavati.agents.forensics import ForensicEngine

mcp = FastMCP(
    name="lilavati-adversarial-committee",
)


@mcp.tool()
def evaluate_investment_committee_memo(
    symbol: str,
    fiscal_year: int,
    bull_revenue_growth_target: float,
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
) -> dict[str, Any]:
    """
    Runs the multi-role adversarial investment committee debate (Bull, Bear, Auditor, PM)
    and verifies formal Z3 accounting invariants before emitting the final binding recommendation.
    """
    memo = AdversarialCommittee.evaluate_company(
        symbol=symbol,
        fiscal_year=fiscal_year,
        bull_revenue_growth_target=bull_revenue_growth_target,
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
        cfi_t=cfi_t,
        cff_t=cff_t,
        market_value_equity=market_value_equity,
    )
    return memo.model_dump()


@mcp.tool()
def compute_forensic_beneish_m_score(
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
) -> dict[str, Any]:
    """Calculates the 8-variable Beneish M-Score to detect earnings manipulation."""
    res = ForensicEngine.calculate_beneish_m_score(
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
    return res.model_dump()


if __name__ == "__main__":
    mcp.run()
