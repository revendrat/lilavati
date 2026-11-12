"""
FastMCP Server for Financial Econometrics.

Exposes deterministic time-series stationarity testing, cointegration analysis,
and GARCH volatility modeling via Model Context Protocol (FastMCP).
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from lilavati.core.econometrics import EconometricEngine

mcp = FastMCP(
    name="lilavati-econometrics",
)


@mcp.tool()
def analyze_stationarity(
    series: list[float],
    significance_level: float = 0.05,
) -> dict[str, Any]:
    """
    Tests a time series for stationarity using the Augmented Dickey-Fuller (ADF) test.
    Returns test statistics, p-value, and an econometric recommendation.
    """
    result = EconometricEngine.test_stationarity(
        series=series,
        significance_level=significance_level,
    )
    return result.model_dump()


@mcp.tool()
def analyze_cointegration(
    series_a: list[float],
    series_b: list[float],
    significance_level: float = 0.05,
) -> dict[str, Any]:
    """
    Tests whether two price series are cointegrated (for statistical arbitrage / pairs trading)
    and computes the Ornstein-Uhlenbeck mean-reversion half-life.
    """
    result = EconometricEngine.test_cointegration(
        series_a=series_a,
        series_b=series_b,
        significance_level=significance_level,
    )
    return result.model_dump()


@mcp.tool()
def fit_garch_volatility(
    returns: list[float],
    p: int = 1,
    q: int = 1,
) -> dict[str, Any]:
    """
    Fits a GARCH(p,q) model to asset returns to quantify conditional volatility
    and volatility clustering persistence.
    """
    result = EconometricEngine.fit_garch(
        returns=returns,
        p=p,
        q=q,
    )
    return result.model_dump()


if __name__ == "__main__":
    mcp.run()
