"""
Canonical Pydantic V2 Schemas for Trading Microstructure, Execution, and Portfolio Optimization.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LOBMetrics(BaseModel):
    """Limit Order Book (LOB) microstructure snapshot metrics."""

    model_config = ConfigDict(frozen=True)

    best_bid: float = Field(..., description="Highest active bid price")
    best_ask: float = Field(..., description="Lowest active ask price")
    bid_size: float = Field(..., description="Aggregate volume available at best bid")
    ask_size: float = Field(..., description="Aggregate volume available at best ask")
    spread: float = Field(..., description="Bid-ask spread (ask - bid)")
    mid_price: float = Field(..., description="Simple arithmetic mid price")
    micro_price: float = Field(..., description="Volume-weighted microprice")
    order_flow_imbalance: float = Field(..., description="Order Flow Imbalance (OFI) proxy")


class AlmgrenChrissResult(BaseModel):
    """Optimal trade trajectory generated via the Almgren-Chriss framework."""

    model_config = ConfigDict(frozen=True)

    total_shares: float
    time_horizon_hours: float
    n_intervals: int
    trading_trajectory: list[float] = Field(
        ..., description="Shares remaining at each time interval"
    )
    trade_sizes: list[float] = Field(..., description="Shares to execute in each time interval")
    expected_shortfall: float = Field(
        ..., description="Expected monetary execution cost (market impact)"
    )
    shortfall_variance: float = Field(
        ..., description="Variance of execution cost due to price volatility"
    )
    half_life_hours: float = Field(
        ..., description="Decay half-life of position liquidation (1/kappa)"
    )


class BlackLittermanResult(BaseModel):
    """Optimal portfolio allocation resulting from Black-Litterman model."""

    model_config = ConfigDict(frozen=True)

    assets: list[str]
    market_prior_weights: list[float]
    optimal_weights: list[float]
    expected_returns: list[float]
    implied_prior_returns: list[float]


class HRPAllocationResult(BaseModel):
    """Optimal portfolio allocation via Hierarchical Risk Parity (HRP)."""

    model_config = ConfigDict(frozen=True)

    assets: list[str]
    weights: list[float] = Field(..., description="Allocated portfolio weights summing to 1.0")
    ordered_indices: list[int] = Field(
        ..., description="Quasi-diagonalized hierarchical tree order"
    )
