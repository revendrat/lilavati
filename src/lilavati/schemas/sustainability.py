"""
Canonical Pydantic V2 Schemas for Sustainable Finance, Climate Risk, and Carbon Accounting.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class NGFSScenario(StrEnum):
    """Network for Greening the Financial System (NGFS) Climate Scenarios."""

    NET_ZERO_2050 = "Net Zero 2050 (Orderly 1.5°C)"
    BELOW_2C = "Below 2°C (Orderly)"
    DELAYED_TRANSITION = "Delayed Transition (Disorderly 2.0°C)"
    DIVERGENT_NET_ZERO = "Divergent Net Zero (Disorderly)"
    CURRENT_POLICIES = "Current Policies (Hot House World 3.0°C+)"
    NATIONALLY_DETERMINED = "NDCs (Hot House World 2.6°C)"


class ScopeEmissions(BaseModel):
    """GHG Protocol Carbon Emissions Inventory (in metric tonnes CO2 equivalent - tCO2e)."""

    model_config = ConfigDict(frozen=True)

    scope1: float = Field(..., ge=0.0, description="Direct emissions from owned/controlled sources (tCO2e)")
    scope2_location: float = Field(..., ge=0.0, description="Indirect emissions from purchased energy (location-based)")
    scope2_market: float | None = Field(default=None, ge=0.0, description="Indirect emissions (market-based instruments)")
    scope3_upstream: float | None = Field(default=None, ge=0.0, description="Upstream supply chain emissions")
    scope3_downstream: float | None = Field(default=None, ge=0.0, description="Downstream product lifecycle emissions")
    reporting_year: int = Field(..., ge=2000, le=2100, description="Fiscal year of reporting")
    has_reasonable_assurance: bool = Field(default=False, description="True if third-party audit performed")


class CarbonTaxStressResult(BaseModel):
    """Financial impact of a shadow or statutory carbon price shock on corporate cash flows."""

    model_config = ConfigDict(frozen=True)

    carbon_price_per_ton: float = Field(..., description="Applied carbon price ($/tCO2e)")
    total_taxable_emissions: float = Field(..., description="Scope 1 + Scope 2 emissions assessed")
    gross_carbon_liability: float = Field(..., description="Gross unmitigated carbon penalty ($)")
    pass_through_rate: float = Field(..., ge=0.0, le=1.0, description="Fraction of cost passed to customers")
    net_carbon_expense: float = Field(..., description="Net unhedged expense borne by the firm ($)")
    ebit_margin_before_pct: float = Field(..., description="Operating margin before carbon shock")
    ebit_margin_after_pct: float = Field(..., description="Operating margin after carbon shock")
    ebit_reduction_pct: float = Field(..., description="Percentage decline in operating income")
    interest_coverage_after: float = Field(..., description="Adjusted interest coverage ratio (EBIT / Interest)")
    is_covenant_at_risk: bool = Field(..., description="True if interest coverage drops below covenant floor")


class SustainabilityLinkedBond(BaseModel):
    """Debt structure for Sustainability-Linked Bonds (SLBs) with step-up covenants."""

    model_config = ConfigDict(frozen=True)

    isin: str = Field(..., description="International Securities Identification Number")
    notional: float = Field(..., description="Principal face value ($)")
    base_coupon_rate: float = Field(..., description="Base annual coupon rate (e.g. 0.045 for 4.5%)")
    target_reduction_pct: float = Field(..., ge=0.0, le=1.0, description="Mandatory emission reduction % by target date")
    baseline_emissions: float = Field(..., description="Baseline emissions at bond issuance (tCO2e)")
    step_up_bps: float = Field(..., description="Penalty coupon step-up in basis points (e.g. 25 bps = 0.0025)")
    target_year: int = Field(..., description="Observation year for the Sustainability Performance Target (SPT)")


class SLBCovenantResult(BaseModel):
    """Evaluation of an SLB Sustainability Performance Target (SPT)."""

    model_config = ConfigDict(frozen=True)

    spt_achieved: bool = Field(..., description="True if emissions reduction met or exceeded target")
    realized_reduction_pct: float = Field(..., description="Actual percentage reduction achieved")
    target_reduction_pct: float = Field(..., description="Required reduction target")
    active_coupon_rate: float = Field(..., description="Resulting coupon rate after covenant evaluation")
    annual_interest_penalty: float = Field(..., description="Additional annual interest cash outflow ($)")
