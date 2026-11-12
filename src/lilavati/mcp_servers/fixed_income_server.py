"""
FastMCP Server for Fixed Income, Yield Curves, and Credit Risk.

Exposes deterministic bond pricing, Nelson-Siegel yield curve calibration,
and the Merton structural credit risk model via Model Context Protocol (FastMCP).
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from lilavati.core.fixed_income import FixedIncomeEngine

mcp = FastMCP(
    name="lilavati-fixed-income",
)


@mcp.tool()
def analyze_bond(
    face_value: float,
    coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    frequency: int = 2,
) -> dict[str, Any]:
    """
    Computes clean price, Macaulay duration, modified duration, convexity, and DV01 for a bond.
    """
    result = FixedIncomeEngine.analyze_bond(
        face_value=face_value,
        coupon_rate=coupon_rate,
        ytm=ytm,
        years_to_maturity=years_to_maturity,
        frequency=frequency,
    )
    return result.model_dump()


@mcp.tool()
def fit_yield_curve(
    maturities: list[float],
    yields: list[float],
) -> dict[str, Any]:
    """
    Fits the Nelson-Siegel 4-parameter model to observed benchmark yields and maturities.
    """
    result = FixedIncomeEngine.fit_nelson_siegel(
        maturities=maturities,
        yields=yields,
    )
    return result.model_dump()


@mcp.tool()
def evaluate_credit_risk_merton(
    equity_value: float,
    equity_volatility: float,
    debt_face_value: float,
    risk_free_rate: float,
    maturity_years: float,
) -> dict[str, Any]:
    """
    Solves the Merton structural credit risk model for implied asset value,
    asset volatility, distance-to-default, default probability, and theoretical credit spread.
    """
    result = FixedIncomeEngine.solve_merton_model(
        equity_value=equity_value,
        equity_volatility=equity_volatility,
        debt_face_value=debt_face_value,
        risk_free_rate=risk_free_rate,
        maturity_years=maturity_years,
    )
    return result.model_dump()


if __name__ == "__main__":
    mcp.run()
