"""
FastMCP Server for Sustainable Finance, Climate Risk, and Carbon Accounting.

Exposes deterministic carbon intensity analytics (WACI), climate transition risk stress testing,
and Sustainability-Linked Bond (SLB) covenant evaluation via Model Context Protocol (FastMCP).
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from lilavati.core.sustainability import SustainabilityEngine
from lilavati.schemas.sustainability import SustainabilityLinkedBond

mcp = FastMCP(
    name="lilavati-sustainability",
)


@mcp.tool()
def calculate_portfolio_carbon_intensity(
    weights: list[float],
    emissions: list[float],
    revenues_millions: list[float],
    paris_aligned_threshold: float = 100.0,
) -> dict[str, Any]:
    """
    Computes portfolio Weighted Average Carbon Intensity (WACI) according to TCFD guidelines.
    """
    result = SustainabilityEngine.calculate_waci(
        portfolio_weights=weights,
        emissions=emissions,
        revenues_millions=revenues_millions,
        paris_aligned_threshold=paris_aligned_threshold,
    )
    return result.model_dump()


@mcp.tool()
def stress_test_carbon_tax_impact(
    revenue: float,
    ebit: float,
    interest_expense: float,
    scope1_emissions: float,
    scope2_emissions: float,
    carbon_price_per_ton: float,
    pass_through_rate: float = 0.50,
    covenant_interest_floor: float = 2.50,
) -> dict[str, Any]:
    """
    Stress tests corporate operating income, EBIT margin, and debt covenant headroom
    under statutory or shadow carbon price shocks.
    """
    result = SustainabilityEngine.stress_test_carbon_tax(
        revenue=revenue,
        ebit=ebit,
        interest_expense=interest_expense,
        scope1_emissions=scope1_emissions,
        scope2_emissions=scope2_emissions,
        carbon_price_per_ton=carbon_price_per_ton,
        pass_through_rate=pass_through_rate,
        covenant_interest_floor=covenant_interest_floor,
    )
    return result.model_dump()


@mcp.tool()
def evaluate_sustainability_linked_bond_covenant(
    isin: str,
    notional: float,
    base_coupon_rate: float,
    target_reduction_pct: float,
    baseline_emissions: float,
    step_up_bps: float,
    target_year: int,
    reported_emissions: float,
) -> dict[str, Any]:
    """
    Evaluates an SLB Sustainability Performance Target (SPT) and determines whether
    the coupon step-up penalty covenant triggers.
    """
    bond = SustainabilityLinkedBond(
        isin=isin,
        notional=notional,
        base_coupon_rate=base_coupon_rate,
        target_reduction_pct=target_reduction_pct,
        baseline_emissions=baseline_emissions,
        step_up_bps=step_up_bps,
        target_year=target_year,
    )
    result = SustainabilityEngine.evaluate_slb_covenant(
        bond=bond,
        reported_emissions=reported_emissions,
    )
    return result.model_dump()


if __name__ == "__main__":
    mcp.run()
