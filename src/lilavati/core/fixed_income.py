"""
Fixed Income, Debt & Credit Risk Core Engine.

Implements:
1. Bond analytics: Macaulay duration, modified duration, convexity, and DV01.
2. Nelson-Siegel parametric yield curve fitting.
3. Merton Structural Credit Risk model (Distance-to-Default and credit spread).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from scipy.optimize import curve_fit, root
from scipy.stats import norm


class BondAnalyticsResult(BaseModel):
    """Result of bond pricing and sensitivity analysis."""

    model_config = ConfigDict(frozen=True)

    clean_price: float = Field(..., description="Clean price per 100 par value")
    macaulay_duration: float = Field(..., description="Macaulay duration in years")
    modified_duration: float = Field(
        ..., description="Modified duration (percentage price sensitivity per 1% yield change)"
    )
    convexity: float = Field(..., description="Bond convexity measure")
    dv01: float = Field(..., description="Dollar Value of 01 basis point per 100 par")


class NelsonSiegelCurveResult(BaseModel):
    """Result of Nelson-Siegel yield curve parameter estimation."""

    model_config = ConfigDict(frozen=True)

    beta0_level: float = Field(..., description="Long-term asymptotic rate level")
    beta1_slope: float = Field(..., description="Short-term slope parameter")
    beta2_curvature: float = Field(..., description="Medium-term curvature parameter")
    lambda_decay: float = Field(..., description="Decay parameter governing curve peak location")
    r_squared: float = Field(..., description="Goodness of fit R^2 measure")


class MertonCreditResult(BaseModel):
    """Result of the Merton structural default risk model."""

    model_config = ConfigDict(frozen=True)

    asset_value: float = Field(..., description="Implied total economic asset value of the firm")
    asset_volatility: float = Field(..., description="Implied annual asset volatility")
    distance_to_default: float = Field(
        ..., description="Standard deviations of asset value above debt face value"
    )
    default_probability: float = Field(
        ..., description="Theoretical risk-neutral probability of default"
    )
    theoretical_credit_spread_bps: float = Field(
        ..., description="Theoretical credit spread over risk-free rate in bps"
    )


class FixedIncomeEngine:
    """Deterministic analytics for bonds, yield curves, and credit risk."""

    @staticmethod
    def analyze_bond(
        face_value: float,
        coupon_rate: float,
        ytm: float,
        years_to_maturity: float,
        frequency: int = 2,
    ) -> BondAnalyticsResult:
        """
        Calculates bond price, Macaulay duration, modified duration, convexity, and DV01.
        """
        n_periods = int(round(years_to_maturity * frequency))
        coupon = (face_value * coupon_rate) / frequency
        period_yield = ytm / frequency

        price = 0.0
        weighted_time = 0.0
        convexity_acc = 0.0

        for t in range(1, n_periods + 1):
            cf = coupon + (face_value if t == n_periods else 0.0)
            df = (1.0 + period_yield) ** (-t)
            pv_cf = cf * df

            price += pv_cf
            time_years = t / frequency
            weighted_time += time_years * pv_cf
            convexity_acc += (t * (t + 1) * cf) / ((1.0 + period_yield) ** (t + 2))

        mac_dur = weighted_time / price
        mod_dur = mac_dur / (1.0 + period_yield)
        convexity = convexity_acc / (price * (frequency**2))
        dv01 = mod_dur * price * 0.0001

        return BondAnalyticsResult(
            clean_price=float(price),
            macaulay_duration=float(mac_dur),
            modified_duration=float(mod_dur),
            convexity=float(convexity),
            dv01=float(dv01),
        )

    @staticmethod
    def _nelson_siegel_func(
        t: np.ndarray,
        b0: float,
        b1: float,
        b2: float,
        lam: float,
    ) -> np.ndarray:
        # Avoid division by zero
        t_lam = np.maximum(t / max(lam, 1e-4), 1e-6)
        factor1 = (1.0 - np.exp(-t_lam)) / t_lam
        factor2 = factor1 - np.exp(-t_lam)
        return b0 + b1 * factor1 + b2 * factor2

    @staticmethod
    def fit_nelson_siegel(
        maturities: Sequence[float],
        yields: Sequence[float],
    ) -> NelsonSiegelCurveResult:
        """
        Fits the 4-parameter Nelson-Siegel model to observed term structure yields:
        y(t) = beta0 + beta1 * ((1 - e^(-t/lam))/(t/lam)) + beta2 * (((1 - e^(-t/lam))/(t/lam)) - e^(-t/lam))
        """
        t = np.asarray(maturities, dtype=np.float64)
        y = np.asarray(yields, dtype=np.float64)

        if len(t) < 4:
            raise ValueError(f"Nelson-Siegel requires at least 4 maturity points, got {len(t)}.")

        # Initial parameter estimates
        b0_init = float(y[-1])
        b1_init = float(y[0] - y[-1])
        b2_init = 0.0
        lam_init = 2.0

        popt, _ = curve_fit(
            FixedIncomeEngine._nelson_siegel_func,
            t,
            y,
            p0=[b0_init, b1_init, b2_init, lam_init],
            bounds=([-0.1, -0.2, -0.2, 0.1], [0.5, 0.2, 0.2, 10.0]),
            maxfev=5000,
        )

        b0, b1, b2, lam = popt
        y_pred = FixedIncomeEngine._nelson_siegel_func(t, b0, b1, b2, lam)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0

        return NelsonSiegelCurveResult(
            beta0_level=float(b0),
            beta1_slope=float(b1),
            beta2_curvature=float(b2),
            lambda_decay=float(lam),
            r_squared=float(r2),
        )

    @staticmethod
    def solve_merton_model(
        equity_value: float,
        equity_volatility: float,
        debt_face_value: float,
        risk_free_rate: float,
        maturity_years: float,
    ) -> MertonCreditResult:
        """
        Solves the Merton (1974) structural model for unobserved asset value (V_A)
        and asset volatility (sigma_A) using equity value and equity volatility.
        """
        e = equity_value
        sig_e = equity_volatility
        d = debt_face_value
        r = risk_free_rate
        t = maturity_years

        def equations(vars_guess: np.ndarray) -> np.ndarray:
            va, sig_a = vars_guess
            if va <= 0 or sig_a <= 0:
                return np.array([1e6, 1e6])

            d1 = (np.log(va / d) + (r + 0.5 * sig_a**2) * t) / (sig_a * np.sqrt(t))
            d2 = d1 - sig_a * np.sqrt(t)

            # Eq 1: Call option pricing for equity
            eq1 = va * norm.cdf(d1) - d * np.exp(-r * t) * norm.cdf(d2) - e
            # Eq 2: Volatility relation: sig_e * e = norm.cdf(d1) * sig_a * va
            eq2 = norm.cdf(d1) * sig_a * va - sig_e * e
            return np.array([eq1, eq2])

        # Initial guess: V_A = Equity + Debt, sigma_A = sigma_E * (E / (E + D))
        va_guess = e + d
        sig_a_guess = sig_e * (e / va_guess)

        sol = root(equations, [va_guess, sig_a_guess], method="hybr")
        va_sol, sig_a_sol = float(sol.x[0]), float(sol.x[1])

        # Distance to default
        d1 = (math.log(va_sol / d) + (r + 0.5 * sig_a_sol**2) * t) / (sig_a_sol * math.sqrt(t))
        d2 = d1 - sig_a_sol * math.sqrt(t)

        dd = float(d2)
        pd = float(norm.cdf(-dd))

        # Theoretical credit spread: y_D - r = -(1/T) * ln( (V_A/D)*norm.cdf(-d1) + e^(-rT)*norm.cdf(d2) ) - r
        # Debt value = V_A - Equity
        debt_val = va_sol - e
        implied_yield = -(1.0 / t) * math.log(debt_val / d) if debt_val > 0 else 0.0
        spread_bps = max(0.0, (implied_yield - r) * 10000.0)

        return MertonCreditResult(
            asset_value=va_sol,
            asset_volatility=sig_a_sol,
            distance_to_default=dd,
            default_probability=pd,
            theoretical_credit_spread_bps=spread_bps,
        )
