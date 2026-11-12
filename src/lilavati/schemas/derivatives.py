"""
Canonical Pydantic V2 Schemas for Derivatives, Options, Volatility Surfaces, and Greeks.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class OptionType(StrEnum):
    """Option exercise type."""

    CALL = "CALL"
    PUT = "PUT"


class ExerciseStyle(StrEnum):
    """Exercise style."""

    EUROPEAN = "EUROPEAN"
    AMERICAN = "AMERICAN"


class OptionGreeksResult(BaseModel):
    """First- and second-order Greeks sensitivities."""

    model_config = ConfigDict(frozen=True)

    delta: float = Field(
        ..., description="dV/dS - Rate of change of option value with respect to spot price"
    )
    gamma: float = Field(
        ..., description="d^2V/dS^2 - Rate of change of delta with respect to spot price"
    )
    vega: float = Field(
        ..., description="dV/dsigma - Sensitivity to 1% change in implied volatility"
    )
    theta: float = Field(..., description="dV/dt - Sensitivity to time decay per calendar day")
    rho: float = Field(
        ..., description="dV/dr - Sensitivity to 1% change in risk-free interest rate"
    )
    vanna: float = Field(
        ..., description="d^2V/(dS dsigma) - Cross-derivative of delta with respect to volatility"
    )
    volga: float = Field(
        ..., description="d^2V/dsigma^2 - Sensitivity of vega to changes in volatility (vomma)"
    )


class OptionPricingResult(BaseModel):
    """Complete option valuation result including pricing, implied vol, and Greeks."""

    model_config = ConfigDict(frozen=True)

    spot: float
    strike: float
    time_to_maturity: float
    risk_free_rate: float
    volatility: float
    option_type: OptionType
    exercise_style: ExerciseStyle
    price: float = Field(..., description="Theoretical fair value of the option")
    greeks: OptionGreeksResult


class SABRCalibrationResult(BaseModel):
    """Calibrated parameters of the SABR stochastic volatility model."""

    model_config = ConfigDict(frozen=True)

    alpha: float = Field(..., description="Initial volatility level")
    beta: float = Field(..., description="CEV elasticity parameter (fixed in [0, 1])")
    rho: float = Field(
        ..., description="Correlation between underlying price and volatility Wiener processes"
    )
    nu: float = Field(..., description="Volatility of volatility parameter")
    rmse: float = Field(
        ..., description="Root Mean Squared Error of fitted volatilities against market quotes"
    )
    is_arbitrage_free: bool = Field(
        ..., description="True if no butterfly or calendar arbitrage is present"
    )


class ArbitrageVerificationResult(BaseModel):
    """SMT-verified validation of no-arbitrage bounds across an option strike/expiry surface."""

    model_config = ConfigDict(frozen=True)

    is_valid: bool
    violations: list[str] = Field(default_factory=list)
