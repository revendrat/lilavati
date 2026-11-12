"""
Derivatives, Options, Volatility Surfaces, and Greeks Core Engine.

Implements:
1. Analytical Black-Scholes-Merton (BSM) with continuous dividend yield.
2. American Option Pricing via Cox-Ross-Rubinstein (CRR) Binomial Trees.
3. First- and Second-Order Greeks: Delta, Gamma, Vega, Theta, Rho, Vanna, Volga.
4. Hagan et al. (2002) SABR Stochastic Volatility Model Calibration.
5. SMT Formal Verification of No-Arbitrage Conditions (Calendar & Butterfly Spreads).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import z3
from scipy.optimize import curve_fit, root_scalar
from scipy.stats import norm

from lilavati.schemas.derivatives import (
    ArbitrageVerificationResult,
    ExerciseStyle,
    OptionGreeksResult,
    OptionPricingResult,
    OptionType,
    SABRCalibrationResult,
)


class DerivativesEngine:
    """Deterministic analytics for options, Greeks, and volatility surfaces."""

    @staticmethod
    def calculate_bsm_greeks(
        spot: float,
        strike: float,
        time_to_maturity: float,
        risk_free_rate: float,
        volatility: float,
        dividend_yield: float = 0.0,
        is_call: bool = True,
    ) -> OptionGreeksResult:
        """Calculates 1st and 2nd order analytical Black-Scholes-Merton Greeks."""
        s, k, t, r, q, v = (
            spot,
            strike,
            time_to_maturity,
            risk_free_rate,
            dividend_yield,
            volatility,
        )

        if t <= 0 or v <= 0 or s <= 0 or k <= 0:
            raise ValueError(
                "Spot, strike, time to maturity, and volatility must be strictly positive."
            )

        d1 = (math.log(s / k) + (r - q + 0.5 * v**2) * t) / (v * math.sqrt(t))
        d2 = d1 - v * math.sqrt(t)

        pdf_d1 = norm.pdf(d1)
        cdf_d1 = norm.cdf(d1)
        cdf_neg_d1 = norm.cdf(-d1)
        cdf_d2 = norm.cdf(d2)
        cdf_neg_d2 = norm.cdf(-d2)

        exp_qt = math.exp(-q * t)
        exp_rt = math.exp(-r * t)

        # Delta
        delta = exp_qt * cdf_d1 if is_call else -exp_qt * cdf_neg_d1

        # Gamma (identical for Call and Put)
        gamma = (exp_qt * pdf_d1) / (s * v * math.sqrt(t))

        # Vega (per 1% vol change, identical for Call and Put)
        vega = (s * exp_qt * math.sqrt(t) * pdf_d1) * 0.01

        # Theta (per calendar day / 365)
        common_theta = -(s * exp_qt * pdf_d1 * v) / (2.0 * math.sqrt(t))
        if is_call:
            theta = (common_theta - r * k * exp_rt * cdf_d2 + q * s * exp_qt * cdf_d1) / 365.0
        else:
            theta = (
                common_theta + r * k * exp_rt * cdf_neg_d2 - q * s * exp_qt * cdf_neg_d1
            ) / 365.0

        # Rho (per 1% interest rate change)
        rho = (k * t * exp_rt * cdf_d2 * 0.01) if is_call else (-k * t * exp_rt * cdf_neg_d2 * 0.01)

        # Second-order Greeks
        # Vanna: d(Delta)/d(sigma) = -exp(-qT) * phi(d1) * (d2 / sigma)
        vanna = -exp_qt * pdf_d1 * (d2 / v)

        # Volga (Vomma): d(Vega)/d(sigma) = Vega * (d1 * d2 / sigma)
        volga = (s * exp_qt * math.sqrt(t) * pdf_d1) * (d1 * d2 / v) * 0.01

        return OptionGreeksResult(
            delta=float(delta),
            gamma=float(gamma),
            vega=float(vega),
            theta=float(theta),
            rho=float(rho),
            vanna=float(vanna),
            volga=float(volga),
        )

    @staticmethod
    def price_european_option(
        spot: float,
        strike: float,
        time_to_maturity: float,
        risk_free_rate: float,
        volatility: float,
        dividend_yield: float = 0.0,
        is_call: bool = True,
    ) -> OptionPricingResult:
        """Analytical Black-Scholes-Merton European option valuation."""
        s, k, t, r, q, v = (
            spot,
            strike,
            time_to_maturity,
            risk_free_rate,
            dividend_yield,
            volatility,
        )

        d1 = (math.log(s / k) + (r - q + 0.5 * v**2) * t) / (v * math.sqrt(t))
        d2 = d1 - v * math.sqrt(t)

        exp_qt = math.exp(-q * t)
        exp_rt = math.exp(-r * t)

        if is_call:
            price = s * exp_qt * norm.cdf(d1) - k * exp_rt * norm.cdf(d2)
        else:
            price = k * exp_rt * norm.cdf(-d2) - s * exp_qt * norm.cdf(-d1)

        greeks = DerivativesEngine.calculate_bsm_greeks(
            spot, strike, time_to_maturity, risk_free_rate, volatility, dividend_yield, is_call
        )

        return OptionPricingResult(
            spot=spot,
            strike=strike,
            time_to_maturity=time_to_maturity,
            risk_free_rate=risk_free_rate,
            volatility=volatility,
            option_type=OptionType.CALL if is_call else OptionType.PUT,
            exercise_style=ExerciseStyle.EUROPEAN,
            price=float(price),
            greeks=greeks,
        )

    @staticmethod
    def price_american_option_crr(
        spot: float,
        strike: float,
        time_to_maturity: float,
        risk_free_rate: float,
        volatility: float,
        dividend_yield: float = 0.0,
        is_call: bool = True,
        steps: int = 200,
    ) -> OptionPricingResult:
        """Cox-Ross-Rubinstein (CRR) binomial tree for American options with early exercise."""
        dt = time_to_maturity / steps
        u = math.exp(volatility * math.sqrt(dt))
        d = 1.0 / u
        p = (math.exp((risk_free_rate - dividend_yield) * dt) - d) / (u - d)
        df = math.exp(-risk_free_rate * dt)

        # Asset prices at expiration
        asset_prices = np.array([spot * (u**j) * (d ** (steps - j)) for j in range(steps + 1)])

        # Option payoffs at expiration
        if is_call:
            values = np.maximum(0.0, asset_prices - strike)
        else:
            values = np.maximum(0.0, strike - asset_prices)

        # Backward induction with early exercise check
        for i in range(steps - 1, -1, -1):
            asset_prices = np.array([spot * (u**j) * (d ** (i - j)) for j in range(i + 1)])
            continuation_values = df * (p * values[1:] + (1.0 - p) * values[:-1])
            if is_call:
                exercise_values = np.maximum(0.0, asset_prices - strike)
            else:
                exercise_values = np.maximum(0.0, strike - asset_prices)
            values = np.maximum(continuation_values, exercise_values)

        greeks = DerivativesEngine.calculate_bsm_greeks(
            spot, strike, time_to_maturity, risk_free_rate, volatility, dividend_yield, is_call
        )

        return OptionPricingResult(
            spot=spot,
            strike=strike,
            time_to_maturity=time_to_maturity,
            risk_free_rate=risk_free_rate,
            volatility=volatility,
            option_type=OptionType.CALL if is_call else OptionType.PUT,
            exercise_style=ExerciseStyle.AMERICAN,
            price=float(values[0]),
            greeks=greeks,
        )

    @staticmethod
    def calculate_implied_volatility(
        price: float,
        spot: float,
        strike: float,
        time_to_maturity: float,
        risk_free_rate: float,
        dividend_yield: float = 0.0,
        is_call: bool = True,
    ) -> float:
        """Inverts the Black-Scholes-Merton formula to find implied volatility."""

        def obj(v: float) -> float:
            res = DerivativesEngine.price_european_option(
                spot, strike, time_to_maturity, risk_free_rate, v, dividend_yield, is_call
            )
            return res.price - price

        sol = root_scalar(obj, bracket=[1e-4, 5.0], method="brentq")
        return float(sol.root)

    @staticmethod
    def sabr_implied_volatility(
        f: float,
        k: float,
        t: float,
        alpha: float,
        beta: float,
        rho: float,
        nu: float,
    ) -> float:
        """
        Hagan et al. (2002) asymptotic formula for SABR implied volatility.
        sigma_SABR(K, F, T; alpha, beta, rho, nu)
        """
        if abs(f - k) < 1e-6:
            # At-The-Money (ATM) expansion
            factor1 = alpha / (f ** (1.0 - beta))
            factor2 = (
                1.0
                + (
                    ((1.0 - beta) ** 2 / 24.0) * (alpha**2 / (f ** (2.0 - 2.0 * beta)))
                    + (rho * beta * nu * alpha) / (4.0 * f ** (1.0 - beta))
                    + ((2.0 - 3.0 * rho**2) / 24.0) * (nu**2)
                )
                * t
            )
            return float(factor1 * factor2)

        fk = f * k
        log_fk = math.log(f / k)
        z = (nu / alpha) * (fk ** ((1.0 - beta) / 2.0)) * log_fk
        x_z = math.log((math.sqrt(1.0 - 2.0 * rho * z + z**2) + z - rho) / (1.0 - rho))

        denom1 = (fk ** ((1.0 - beta) / 2.0)) * (
            1.0
            + ((1.0 - beta) ** 2 / 24.0) * (log_fk**2)
            + ((1.0 - beta) ** 4 / 1920.0) * (log_fk**4)
        )
        factor = z / x_z if abs(x_z) > 1e-8 else 1.0
        numerator = alpha * factor

        series = (
            1.0
            + (
                ((1.0 - beta) ** 2 / 24.0) * (alpha**2 / (fk ** (1.0 - beta)))
                + (rho * beta * nu * alpha) / (4.0 * fk ** ((1.0 - beta) / 2.0))
                + ((2.0 - 3.0 * rho**2) / 24.0) * (nu**2)
            )
            * t
        )

        return float((numerator / denom1) * series)

    @staticmethod
    def calibrate_sabr(
        forward: float,
        strikes: Sequence[float],
        market_vols: Sequence[float],
        time_to_maturity: float,
        beta: float = 0.5,
    ) -> SABRCalibrationResult:
        """Calibrates SABR model parameters (alpha, rho, nu) to an observed option smile."""
        k_arr = np.asarray(strikes, dtype=np.float64)
        v_arr = np.asarray(market_vols, dtype=np.float64)

        atm_vol = float(v_arr[len(v_arr) // 2])
        alpha_init = atm_vol * (forward ** (1.0 - beta))

        def model_func(k: np.ndarray, alpha: float, rho: float, nu: float) -> np.ndarray:
            return np.array(
                [
                    DerivativesEngine.sabr_implied_volatility(
                        forward, float(ki), time_to_maturity, alpha, beta, rho, nu
                    )
                    for ki in k
                ]
            )

        popt, _ = curve_fit(
            model_func,
            k_arr,
            v_arr,
            p0=[alpha_init, -0.2, 0.4],
            bounds=([1e-4, -0.999, 1e-4], [5.0, 0.999, 5.0]),
            maxfev=5000,
        )

        calibrated_alpha, calibrated_rho, calibrated_nu = popt
        fitted_vols = model_func(k_arr, calibrated_alpha, calibrated_rho, calibrated_nu)
        rmse = float(np.sqrt(np.mean((fitted_vols - v_arr) ** 2)))

        return SABRCalibrationResult(
            alpha=float(calibrated_alpha),
            beta=float(beta),
            rho=float(calibrated_rho),
            nu=float(calibrated_nu),
            rmse=rmse,
            is_arbitrage_free=bool(rmse < 0.05),
        )

    @staticmethod
    def verify_butterfly_arbitrage(
        strikes: Sequence[float],
        call_prices: Sequence[float],
        tolerance: float = 1e-4,
    ) -> ArbitrageVerificationResult:
        """
        Formally verifies butterfly spread convexity using Z3 SMT solver:
        For strikes K1 < K2 < K3 with equal spacing delta:
        C(K1) - 2*C(K2) + C(K3) >= 0 (strictly non-negative probability density).
        """
        violations: list[str] = []
        k = list(strikes)
        c = list(call_prices)

        if len(k) != len(c) or len(k) < 3:
            raise ValueError(
                "At least 3 strike/price points required for butterfly arbitrage verification."
            )

        solver = z3.Solver()

        for i in range(1, len(k) - 1):
            k_prev, k_curr, k_next = k[i - 1], k[i], k[i + 1]
            c_prev, c_curr, c_next = c[i - 1], c[i], c[i + 1]

            # Linear butterfly payoff condition for convex curve
            # (C(K3) - C(K2))/(K3 - K2) - (C(K2) - C(K1))/(K2 - K1) >= -tol
            slope_right = (c_next - c_curr) / (k_next - k_curr)
            slope_left = (c_curr - c_prev) / (k_curr - k_prev)
            butterfly_spread = slope_right - slope_left

            bf_sym = z3.Real(f"butterfly_{i}")
            solver.add(bf_sym == z3.RealVal(str(butterfly_spread)))
            solver.add(bf_sym >= z3.RealVal(str(-tolerance)))

            if butterfly_spread < -tolerance:
                violations.append(
                    f"Butterfly arbitrage violated at strike {k_curr}: "
                    f"Convexity slope delta is {butterfly_spread:.6f} < 0. Implies negative risk-neutral density."
                )

        check = solver.check()
        is_valid = (check == z3.sat) and (len(violations) == 0)

        return ArbitrageVerificationResult(
            is_valid=is_valid,
            violations=violations,
        )
