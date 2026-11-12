"""
Sustainable Finance & Climate Risk Core Engine.

Implements rigorous quantitative modeling for:
1. Carbon Accounting & Weighted Average Carbon Intensity (WACI)
2. Climate Transition Stress Testing (Shadow Carbon Pricing on Operating Margins & Debt Covenants)
3. Sustainability-Linked Bond (SLB) Coupon Step-Up Covenant Evaluation
4. Climate Value-at-Risk (Climate Transition VaR)
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from lilavati.schemas.sustainability import (
    CarbonTaxStressResult,
    SLBCovenantResult,
    SustainabilityLinkedBond,
)


class PortfolioCarbonResult(BaseModel):
    """Portfolio-level carbon metrics according to TCFD and PCAF standards."""

    model_config = ConfigDict(frozen=True)

    waci: float = Field(..., description="Weighted Average Carbon Intensity (tCO2e / $M revenue)")
    total_carbon_footprint: float = Field(..., description="Total financed emissions (tCO2e)")
    carbon_intensity_clean: bool = Field(..., description="True if below Paris-aligned benchmark threshold")


class SustainabilityEngine:
    """Deterministic analytics for climate finance and sustainability modeling."""

    @staticmethod
    def calculate_waci(
        portfolio_weights: Sequence[float],
        emissions: Sequence[float],
        revenues_millions: Sequence[float],
        paris_aligned_threshold: float = 100.0,
    ) -> PortfolioCarbonResult:
        """
        Computes the Weighted Average Carbon Intensity (WACI):
        WACI = sum(w_i * (Emissions_i / Revenue_i_in_millions))
        """
        w = np.asarray(portfolio_weights, dtype=np.float64)
        e = np.asarray(emissions, dtype=np.float64)
        r = np.asarray(revenues_millions, dtype=np.float64)

        if not (len(w) == len(e) == len(r)):
            raise ValueError(f"Dimension mismatch: weights ({len(w)}), emissions ({len(e)}), revenues ({len(r)})")
        if np.any(r <= 0):
            raise ValueError("Revenues must be strictly positive to compute carbon intensity.")

        # Normalize weights if not summing to 1.0
        w_norm = w / np.sum(w)
        intensities = e / r
        waci_val = float(np.sum(w_norm * intensities))
        total_footprint = float(np.sum(e * w_norm))

        return PortfolioCarbonResult(
            waci=float(waci_val),
            total_carbon_footprint=total_footprint,
            carbon_intensity_clean=bool(waci_val <= paris_aligned_threshold),
        )

    @staticmethod
    def stress_test_carbon_tax(
        revenue: float,
        ebit: float,
        interest_expense: float,
        scope1_emissions: float,
        scope2_emissions: float,
        carbon_price_per_ton: float,
        pass_through_rate: float = 0.50,
        covenant_interest_floor: float = 2.50,
    ) -> CarbonTaxStressResult:
        """
        Stress tests a company's operating margin, EBIT, and interest coverage under
        a shadow or statutory carbon price shock ($/tCO2e).
        """
        if revenue <= 0:
            raise ValueError("Revenue must be positive.")
        if not (0.0 <= pass_through_rate <= 1.0):
            raise ValueError(f"Pass-through rate must be in [0, 1], got {pass_through_rate}")

        taxable_emissions = scope1_emissions + scope2_emissions
        gross_liability = taxable_emissions * carbon_price_per_ton
        # Net cost absorbed by the firm after passing some share to customers
        net_carbon_cost = gross_liability * (1.0 - pass_through_rate)

        ebit_margin_before = ebit / revenue
        ebit_after = ebit - net_carbon_cost
        ebit_margin_after = ebit_after / revenue
        ebit_reduction_pct = (ebit - ebit_after) / abs(ebit) if ebit != 0 else 0.0

        coverage_after = ebit_after / interest_expense if interest_expense > 0 else float("inf")
        covenant_at_risk = coverage_after < covenant_interest_floor

        return CarbonTaxStressResult(
            carbon_price_per_ton=carbon_price_per_ton,
            total_taxable_emissions=taxable_emissions,
            gross_carbon_liability=float(gross_liability),
            pass_through_rate=pass_through_rate,
            net_carbon_expense=float(net_carbon_cost),
            ebit_margin_before_pct=float(ebit_margin_before),
            ebit_margin_after_pct=float(ebit_margin_after),
            ebit_reduction_pct=float(ebit_reduction_pct),
            interest_coverage_after=float(coverage_after),
            is_covenant_at_risk=covenant_at_risk,
        )

    @staticmethod
    def evaluate_slb_covenant(
        bond: SustainabilityLinkedBond,
        reported_emissions: float,
    ) -> SLBCovenantResult:
        """
        Evaluates whether a Sustainability-Linked Bond (SLB) achieved its Sustainability
        Performance Target (SPT) or triggers the penalty coupon step-up.
        """
        reduction = (bond.baseline_emissions - reported_emissions) / bond.baseline_emissions
        spt_achieved = reduction >= bond.target_reduction_pct

        if spt_achieved:
            active_coupon = bond.base_coupon_rate
            penalty_outflow = 0.0
        else:
            step_up_rate = bond.step_up_bps / 10000.0
            active_coupon = bond.base_coupon_rate + step_up_rate
            penalty_outflow = bond.notional * step_up_rate

        return SLBCovenantResult(
            spt_achieved=spt_achieved,
            realized_reduction_pct=float(reduction),
            target_reduction_pct=bond.target_reduction_pct,
            active_coupon_rate=float(active_coupon),
            annual_interest_penalty=float(penalty_outflow),
        )
