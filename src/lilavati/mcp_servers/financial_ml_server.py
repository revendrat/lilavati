"""
FastMCP Server for Financial Machine Learning.

Exposes Marcos López de Prado's institutional financial ML primitives:
1. Fractional Differentiation (finding optimal d* preserving memory)
2. Triple-Barrier Method (path-dependent labeling)
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from lilavati.core.financial_ml import FinancialMLEngine

mcp = FastMCP(
    name="lilavati-financial-ml",
)


@mcp.tool()
def find_optimal_fractional_diff(
    series: list[float],
    step: float = 0.05,
    target_p_value: float = 0.01,
) -> dict[str, Any]:
    """
    Finds the minimum degree of fractional differentiation d* in [0, 1] that makes
    the series stationary while preserving maximum long-term memory.
    """
    result = FinancialMLEngine.find_optimal_fractional_d(
        series=series,
        step=step,
        target_p_value=target_p_value,
    )
    return result.model_dump()


@mcp.tool()
def apply_triple_barrier_labels(
    prices: list[float],
    holding_horizon: int,
    take_profit_pct: float,
    stop_loss_pct: float,
) -> list[dict[str, Any]]:
    """
    Applies the Triple-Barrier Method to asset prices to produce path-dependent
    labels (+1 take-profit, -1 stop-loss, 0 expiration).
    """
    labels = FinancialMLEngine.apply_triple_barriers(
        prices=prices,
        holding_horizon=holding_horizon,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
    )
    return [label.model_dump() for label in labels]


if __name__ == "__main__":
    mcp.run()
