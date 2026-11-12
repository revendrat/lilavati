"""
FastMCP Server for Derivatives, Options Pricing, Greeks, and Volatility Surfaces.

Exposes Black-Scholes-Merton, American CRR binomial trees, 1st & 2nd order Greeks,
SABR stochastic volatility calibration, and SMT butterfly arbitrage verification.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from lilavati.core.derivatives import DerivativesEngine

mcp = FastMCP(
    name="lilavati-derivatives",
)


@mcp.tool()
def price_european_option(
    spot: float,
    strike: float,
    time_to_maturity: float,
    risk_free_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
    is_call: bool = True,
) -> dict[str, Any]:
    """Prices a European option via Black-Scholes-Merton and calculates all Greeks."""
    result = DerivativesEngine.price_european_option(
        spot=spot,
        strike=strike,
        time_to_maturity=time_to_maturity,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
        is_call=is_call,
    )
    return result.model_dump()


@mcp.tool()
def price_american_option(
    spot: float,
    strike: float,
    time_to_maturity: float,
    risk_free_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
    is_call: bool = True,
    steps: int = 150,
) -> dict[str, Any]:
    """Prices an American option with early exercise via Cox-Ross-Rubinstein (CRR) binomial tree."""
    result = DerivativesEngine.price_american_option_crr(
        spot=spot,
        strike=strike,
        time_to_maturity=time_to_maturity,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
        is_call=is_call,
        steps=steps,
    )
    return result.model_dump()


@mcp.tool()
def calculate_option_greeks(
    spot: float,
    strike: float,
    time_to_maturity: float,
    risk_free_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
    is_call: bool = True,
) -> dict[str, Any]:
    """Calculates analytical 1st & 2nd order Greeks (Delta, Gamma, Vega, Theta, Rho, Vanna, Volga)."""
    result = DerivativesEngine.calculate_bsm_greeks(
        spot=spot,
        strike=strike,
        time_to_maturity=time_to_maturity,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
        is_call=is_call,
    )
    return result.model_dump()


@mcp.tool()
def calibrate_sabr_volatility_model(
    forward: float,
    strikes: list[float],
    market_vols: list[float],
    time_to_maturity: float,
    beta: float = 0.5,
) -> dict[str, Any]:
    """Calibrates the SABR stochastic volatility model (alpha, rho, nu) to market option smiles."""
    result = DerivativesEngine.calibrate_sabr(
        forward=forward,
        strikes=strikes,
        market_vols=market_vols,
        time_to_maturity=time_to_maturity,
        beta=beta,
    )
    return result.model_dump()


@mcp.tool()
def check_butterfly_arbitrage(
    strikes: list[float],
    call_prices: list[float],
) -> dict[str, Any]:
    """Formally verifies butterfly spread convexity across option strikes via Z3 SMT solver."""
    result = DerivativesEngine.verify_butterfly_arbitrage(
        strikes=strikes,
        call_prices=call_prices,
    )
    return result.model_dump()


if __name__ == "__main__":
    mcp.run()
