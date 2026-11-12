"""
Core Financial Econometrics Engine.

Implements rigorous time-series stationarity testing, cointegration for statistical arbitrage,
Ornstein-Uhlenbeck mean-reversion half-life calculation, and GARCH volatility estimation.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from arch import arch_model
from pydantic import BaseModel, ConfigDict, Field
from statsmodels.tsa.stattools import adfuller, coint


class StationarityResult(BaseModel):
    """Result of unit root stationarity diagnostic testing."""

    model_config = ConfigDict(frozen=True)

    is_stationary: bool = Field(
        ..., description="True if the null hypothesis of a unit root is rejected"
    )
    test_statistic: float = Field(..., description="Augmented Dickey-Fuller test statistic")
    p_value: float = Field(..., description="MacKinnon's approximate p-value")
    lags_used: int = Field(..., description="Number of lags used in the test regression")
    n_observations: int = Field(..., description="Number of observations after lag trimming")
    critical_values: dict[str, float] = Field(
        ..., description="Critical values at 1%, 5%, and 10% levels"
    )
    recommendation: str = Field(..., description="Prescriptive guidance for modeling")


class CointegrationResult(BaseModel):
    """Result of cointegration analysis for pairs and basket trading."""

    model_config = ConfigDict(frozen=True)

    is_cointegrated: bool = Field(
        ..., description="True if the two series form a stationary linear combination"
    )
    p_value: float = Field(..., description="P-value of the Engle-Granger cointegration test")
    hedge_ratio: float = Field(
        ..., description="OLS optimal hedge ratio (beta) of series_b against series_a"
    )
    intercept: float = Field(..., description="OLS intercept (alpha)")
    half_life: float = Field(
        ..., description="Mean-reversion half-life in discrete periods via Ornstein-Uhlenbeck"
    )
    spread_std: float = Field(..., description="Standard deviation of the cointegrated spread")
    recommendation: str = Field(..., description="Strategy recommendation")


class GARCHResult(BaseModel):
    """Result of GARCH(p,q) volatility modeling."""

    model_config = ConfigDict(frozen=True)

    p: int = Field(..., description="Order of the GARCH autoregressive terms")
    q: int = Field(..., description="Order of the ARCH innovation terms")
    omega: float = Field(..., description="Baseline constant variance component")
    alpha_coeffs: list[float] = Field(
        ..., description="Coefficients for past squared shocks (ARCH)"
    )
    beta_coeffs: list[float] = Field(
        ..., description="Coefficients for past conditional variance (GARCH)"
    )
    persistence: float = Field(
        ..., description="Sum of alpha + beta measuring volatility clustering persistence"
    )
    annualized_volatility: float = Field(
        ..., description="Latest annualized conditional volatility estimate"
    )
    aic: float = Field(..., description="Akaike Information Criterion for model selection")
    bic: float = Field(..., description="Bayesian Information Criterion for model selection")


class EconometricEngine:
    """Deterministic financial econometrics calculations."""

    @staticmethod
    def test_stationarity(
        series: Sequence[float],
        significance_level: float = 0.05,
    ) -> StationarityResult:
        """
        Runs the Augmented Dickey-Fuller (ADF) test for a unit root.
        H0: Series has a unit root (non-stationary).
        H1: Series is stationary.
        """
        data = np.asarray(series, dtype=np.float64)
        if len(data) < 20:
            raise ValueError(
                f"Insufficient sample size for ADF test: {len(data)} (minimum 20 required)."
            )

        # Suppress future warning for adfuller tuple return format
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            adf_stat, p_val, used_lag, nobs, crit_vals, _ = adfuller(data, autolag="AIC")

        is_stat = bool(p_val < significance_level)
        if is_stat:
            rec = "Series is stationary (I(0)). Ready for mean-reverting modeling, ARIMA, or regression."
        else:
            rec = (
                f"Series is non-stationary (p={p_val:.4f} >= {significance_level}). "
                "Do NOT run OLS directly. Apply fractional differentiation (d*) or first differencing."
            )

        return StationarityResult(
            is_stationary=is_stat,
            test_statistic=float(adf_stat),
            p_value=float(p_val),
            lags_used=int(used_lag),
            n_observations=int(nobs),
            critical_values={k: float(v) for k, v in crit_vals.items()},
            recommendation=rec,
        )

    @staticmethod
    def test_cointegration(
        series_a: Sequence[float],
        series_b: Sequence[float],
        significance_level: float = 0.05,
    ) -> CointegrationResult:
        """
        Tests if series_a and series_b are cointegrated via Engle-Granger two-step method,
        and computes the Ornstein-Uhlenbeck mean-reversion half-life on the resulting spread.
        """
        y = np.asarray(series_a, dtype=np.float64)
        x = np.asarray(series_b, dtype=np.float64)

        if len(y) != len(x):
            raise ValueError(f"Series length mismatch: len(a)={len(y)} != len(b)={len(x)}")
        if len(y) < 30:
            raise ValueError(
                f"Insufficient sample size for cointegration: {len(y)} (minimum 30 required)."
            )

        # Step 1: OLS regression to find hedge ratio: y = alpha + beta * x
        x_with_const = np.column_stack([np.ones_like(x), x])
        coeffs, _, _, _ = np.linalg.lstsq(x_with_const, y, rcond=None)
        alpha, beta = coeffs[0], coeffs[1]

        # Form spread
        spread = y - (alpha + beta * x)

        # Step 2: Test cointegration on the pair
        _, p_val, _ = coint(y, x)
        is_coint = bool(p_val < significance_level)

        # Step 3: Compute Ornstein-Uhlenbeck half-life on spread:
        # delta_spread_t = theta * (spread_{t-1} - mu) + error
        # regressing delta_spread on lagged_spread
        lagged_spread = spread[:-1]
        delta_spread = np.diff(spread)
        x_ou = np.column_stack([np.ones_like(lagged_spread), lagged_spread])
        ou_coeffs, _, _, _ = np.linalg.lstsq(x_ou, delta_spread, rcond=None)
        theta = -ou_coeffs[1]

        half_life = float(math.log(2) / theta) if theta > 0 else float("inf")

        if is_coint:
            rec = f"Pair is cointegrated (p={p_val:.4f}). Half-life is {half_life:.1f} periods. Stat-Arb pairs trading viable."
        else:
            rec = f"Pair is not cointegrated (p={p_val:.4f} >= {significance_level}). Spread is non-stationary. Trading not advised."

        return CointegrationResult(
            is_cointegrated=is_coint,
            p_value=float(p_val),
            hedge_ratio=float(beta),
            intercept=float(alpha),
            half_life=half_life,
            spread_std=float(np.std(spread)),
            recommendation=rec,
        )

    @staticmethod
    def fit_garch(
        returns: Sequence[float],
        p: int = 1,
        q: int = 1,
        rescale: bool = True,
    ) -> GARCHResult:
        """
        Fits a GARCH(p,q) volatility model to asset returns.
        sigma_t^2 = omega + sum(alpha_i * epsilon_{t-i}^2) + sum(beta_j * sigma_{t-j}^2)
        """
        ret = np.asarray(returns, dtype=np.float64)
        if len(ret) < 100:
            raise ValueError(
                f"Insufficient sample size for GARCH: {len(ret)} (minimum 100 required)."
            )

        scale_factor = 100.0 if rescale else 1.0
        scaled_ret = ret * scale_factor

        am = arch_model(scaled_ret, vol="garch", p=p, q=q, dist="normal", rescale=False)
        res = am.fit(disp="off", show_warning=False)

        omega = float(res.params.get("omega", 0.0)) / (scale_factor**2)
        alphas = [float(res.params.get(f"alpha[{i}]", 0.0)) for i in range(1, q + 1)]
        betas = [float(res.params.get(f"beta[{j}]", 0.0)) for j in range(1, p + 1)]
        persistence = float(sum(alphas) + sum(betas))

        # Latest conditional volatility (annualized assuming 252 trading days)
        latest_conditional_vol = float(res.conditional_volatility[-1]) / scale_factor
        annualized_vol = latest_conditional_vol * math.sqrt(252)

        return GARCHResult(
            p=p,
            q=q,
            omega=omega,
            alpha_coeffs=alphas,
            beta_coeffs=betas,
            persistence=persistence,
            annualized_volatility=annualized_vol,
            aic=float(res.aic),
            bic=float(res.bic),
        )
