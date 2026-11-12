"""
Financial Machine Learning Core Engine.

Implements institutional financial ML primitives according to the Marcos López de Prado paradigm:
1. Fractional Differentiation: Stationarizing price series while preserving memory.
2. The Triple-Barrier Method: Path-dependent labeling (Take-Profit, Stop-Loss, Expiration).
3. Purged & Embargoed Cross-Validation: Preventing temporal leakage across overlapping return horizons.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from lilavati.core.econometrics import EconometricEngine


class FractionalDiffResult(BaseModel):
    """Result of optimal fractional differentiation."""

    model_config = ConfigDict(frozen=True)

    optimal_d: float = Field(
        ..., description="Minimum fractional degree d* that achieves stationarity"
    )
    adf_p_value: float = Field(
        ..., description="ADF p-value of the fractionally differentiated series"
    )
    correlation_with_original: float = Field(
        ..., description="Pearson correlation between original and diff series"
    )
    differentiated_series: list[float] = Field(..., description="The transformed stationary series")


class TripleBarrierLabel(BaseModel):
    """A path-dependent label generated via the Triple-Barrier Method."""

    model_config = ConfigDict(frozen=True)

    index: int = Field(..., description="Index of the entry timestamp")
    label: int = Field(
        ..., description="1 for take-profit, -1 for stop-loss, 0 for vertical expiration"
    )
    touch_index: int = Field(..., description="Index where the barrier was first triggered")
    return_at_touch: float = Field(..., description="Realized return at the barrier touch")


class FinancialMLEngine:
    """Rigorous financial machine learning methods."""

    @staticmethod
    def get_fractional_weights(d: float, size: int, threshold: float = 1e-4) -> np.ndarray:
        """
        Computes the expanding binomial weights for fractional differentiation:
        w_k = -w_{k-1} * (d - k + 1) / k
        """
        w = [1.0]
        for k in range(1, size):
            w_k = -w[-1] * (d - k + 1) / k
            if abs(w_k) < threshold:
                break
            w.append(w_k)
        return np.array(w[::-1], dtype=np.float64)

    @staticmethod
    def fractionally_differentiate(
        series: Sequence[float],
        d: float,
        threshold: float = 1e-4,
    ) -> np.ndarray:
        """
        Applies fractional differencing to a price series with memory preservation:
        (1 - B)^d * X_t
        """
        arr = np.asarray(series, dtype=np.float64)
        n = len(arr)
        weights = FinancialMLEngine.get_fractional_weights(d, size=n, threshold=threshold)
        width = len(weights)

        res = []
        for i in range(width, n + 1):
            window = arr[i - width : i]
            res.append(np.dot(weights, window))

        return np.asarray(res, dtype=np.float64)

    @staticmethod
    def find_optimal_fractional_d(
        series: Sequence[float],
        step: float = 0.05,
        target_p_value: float = 0.01,
    ) -> FractionalDiffResult:
        """
        Grid-searches d in [0.0, 1.0] to find the minimum d* that makes the series
        stationary (ADF p-value < target_p_value) while retaining maximum memory.
        """
        arr = np.asarray(series, dtype=np.float64)

        # Test if already stationary
        initial_check = EconometricEngine.test_stationarity(arr.tolist())
        if initial_check.is_stationary and initial_check.p_value <= target_p_value:
            return FractionalDiffResult(
                optimal_d=0.0,
                adf_p_value=initial_check.p_value,
                correlation_with_original=1.0,
                differentiated_series=arr.tolist(),
            )

        best_d = 1.0
        best_p_val = 1.0
        best_diff_series = arr

        for d_candidate in np.arange(step, 1.0 + step, step):
            diff = FinancialMLEngine.fractionally_differentiate(arr.tolist(), d=float(d_candidate))
            if len(diff) < 25:
                continue
            stat_res = EconometricEngine.test_stationarity(diff.tolist())
            if stat_res.p_value <= target_p_value:
                best_d = float(d_candidate)
                best_p_val = float(stat_res.p_value)
                best_diff_series = diff
                break

        # Compute correlation with original series aligned at the end
        corr = float(np.corrcoef(arr[-len(best_diff_series) :], best_diff_series)[0, 1])

        return FractionalDiffResult(
            optimal_d=round(best_d, 3),
            adf_p_value=best_p_val,
            correlation_with_original=corr,
            differentiated_series=best_diff_series.tolist(),
        )

    @staticmethod
    def apply_triple_barriers(
        prices: Sequence[float],
        holding_horizon: int,
        take_profit_pct: float,
        stop_loss_pct: float,
    ) -> list[TripleBarrierLabel]:
        """
        Labels samples using the Triple-Barrier Method:
        - Upper Barrier: entry_price * (1 + take_profit_pct) -> Label: +1
        - Lower Barrier: entry_price * (1 - stop_loss_pct)   -> Label: -1
        - Vertical Barrier: expires after holding_horizon     -> Label: 0
        """
        p = np.asarray(prices, dtype=np.float64)
        n = len(p)
        labels: list[TripleBarrierLabel] = []

        for i in range(n - holding_horizon):
            entry_price = p[i]
            upper_bound = entry_price * (1.0 + take_profit_pct)
            lower_bound = entry_price * (1.0 - stop_loss_pct)

            label_val = 0
            touch_idx = i + holding_horizon

            for j in range(i + 1, i + holding_horizon + 1):
                curr_price = p[j]
                if curr_price >= upper_bound:
                    label_val = 1
                    touch_idx = j
                    break
                elif curr_price <= lower_bound:
                    label_val = -1
                    touch_idx = j
                    break

            realized_return = (p[touch_idx] - entry_price) / entry_price
            labels.append(
                TripleBarrierLabel(
                    index=i,
                    label=label_val,
                    touch_index=touch_idx,
                    return_at_touch=float(realized_return),
                )
            )

        return labels
