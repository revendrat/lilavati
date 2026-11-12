"""
Trading Microstructure, Optimal Execution, and Portfolio Optimization Engine.

Implements:
1. Limit Order Book (LOB) metrics: Microprice, Spread, and Order Flow Imbalance (OFI).
2. The Almgren-Chriss (2000) optimal liquidation trajectory framework.
3. Black-Litterman asset allocation combining market equilibrium priors with agent views.
4. Hierarchical Risk Parity (HRP) using tree clustering without matrix inversion.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import cvxpy as cp
import numpy as np
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform

from lilavati.schemas.execution import (
    AlmgrenChrissResult,
    BlackLittermanResult,
    HRPAllocationResult,
    LOBMetrics,
)


class ExecutionEngine:
    """Deterministic analytics for execution scheduling, microstructure, and portfolio optimization."""

    @staticmethod
    def analyze_lob_snapshot(
        best_bid: float,
        best_ask: float,
        bid_size: float,
        ask_size: float,
        prev_bid_size: float | None = None,
        prev_ask_size: float | None = None,
    ) -> LOBMetrics:
        """
        Computes microstructure metrics from an L1/L2 limit order book quote.
        Microprice = (bid_size * ask_price + ask_size * bid_price) / (bid_size + ask_size)
        """
        if best_bid >= best_ask:
            raise ValueError(
                f"Crossed or locked book: best_bid ({best_bid}) >= best_ask ({best_ask})"
            )
        if bid_size <= 0 or ask_size <= 0:
            raise ValueError("Bid and ask sizes must be positive.")

        spread = best_ask - best_bid
        mid_price = (best_ask + best_bid) / 2.0
        micro_price = (bid_size * best_ask + ask_size * best_bid) / (bid_size + ask_size)

        # Simplified Order Flow Imbalance (OFI) proxy
        ofi = 0.0
        if prev_bid_size is not None and prev_ask_size is not None:
            delta_bid = bid_size - prev_bid_size
            delta_ask = ask_size - prev_ask_size
            ofi = delta_bid - delta_ask

        return LOBMetrics(
            best_bid=float(best_bid),
            best_ask=float(best_ask),
            bid_size=float(bid_size),
            ask_size=float(ask_size),
            spread=float(spread),
            mid_price=float(mid_price),
            micro_price=float(micro_price),
            order_flow_imbalance=float(ofi),
        )

    @staticmethod
    def compute_almgren_chriss_schedule(
        total_shares: float,
        time_horizon_hours: float,
        n_intervals: int,
        daily_volatility: float,
        permanent_impact_gamma: float = 2.5e-7,
        temporary_impact_eta: float = 2.5e-6,
        risk_aversion_lambda: float = 1e-6,
        hours_per_day: float = 6.5,
    ) -> AlmgrenChrissResult:
        """
        Computes the Almgren-Chriss optimal trade liquidation trajectory:
        Balances market impact against price volatility risk.
        x_j = sinh(kappa * (T - t_j)) / sinh(kappa * T) * X_0
        """
        x0 = total_shares
        t_total = time_horizon_hours
        n = n_intervals
        dt = t_total / n

        # Scale volatility to hourly terms
        hourly_vol = daily_volatility / math.sqrt(hours_per_day)
        sigma2 = hourly_vol**2

        gamma = permanent_impact_gamma
        eta = temporary_impact_eta
        lam = risk_aversion_lambda

        # Characteristic decay parameter: kappa^2 = (lambda * sigma^2) / eta
        kappa = math.sqrt((lam * sigma2) / max(eta, 1e-9))
        half_life = 1.0 / kappa if kappa > 0 else float("inf")

        # Trajectory calculation
        sinh_kappa_t = math.sinh(min(kappa * t_total, 50.0))  # Avoid float overflow

        trajectory: list[float] = [x0]
        trade_sizes: list[float] = []

        for j in range(1, n + 1):
            t_rem = t_total - j * dt
            if sinh_kappa_t > 0:
                xj = (math.sinh(min(kappa * t_rem, 50.0)) / sinh_kappa_t) * x0
            else:
                xj = (t_rem / t_total) * x0
            xj = max(0.0, float(xj))
            trajectory.append(xj)
            trade_sizes.append(trajectory[-2] - trajectory[-1])

        # Expected execution shortfall and variance
        # E[x] = 0.5 * gamma * X0^2 + eta * sum(nj^2 / dt)
        exp_impact = 0.5 * gamma * (x0**2) + eta * sum((nj**2) / dt for nj in trade_sizes)
        variance = 0.5 * sigma2 * sum((trajectory[j] ** 2) * dt for j in range(len(trajectory) - 1))

        return AlmgrenChrissResult(
            total_shares=total_shares,
            time_horizon_hours=time_horizon_hours,
            n_intervals=n_intervals,
            trading_trajectory=trajectory,
            trade_sizes=trade_sizes,
            expected_shortfall=float(exp_impact),
            shortfall_variance=float(variance),
            half_life_hours=float(half_life),
        )

    @staticmethod
    def optimize_black_litterman(
        assets: list[str],
        covariance_matrix: Sequence[Sequence[float]],
        market_prior_weights: Sequence[float],
        views_matrix: Sequence[Sequence[float]],
        views_returns: Sequence[float],
        views_confidence_std: Sequence[float],
        risk_aversion: float = 2.5,
        tau: float = 0.05,
    ) -> BlackLittermanResult:
        """
        Solves the Black-Litterman model fusing market equilibrium priors with views.
        E[R] = [ (tau*Sigma)^(-1) + P^T Omega^(-1) P ]^(-1) * [ (tau*Sigma)^(-1) Pi + P^T Omega^(-1) Q ]
        """
        n = len(assets)
        sigma = np.asarray(covariance_matrix, dtype=np.float64)
        w_mkt = np.asarray(market_prior_weights, dtype=np.float64)
        p = np.asarray(views_matrix, dtype=np.float64)
        q = np.asarray(views_returns, dtype=np.float64)
        omega_diag = np.asarray(views_confidence_std, dtype=np.float64) ** 2
        omega = np.diag(omega_diag)

        # 1. Reverse-engineer implied equilibrium returns (Pi = delta * Sigma * w_mkt)
        pi = risk_aversion * (sigma @ w_mkt)

        # 2. Black-Litterman posterior return calculation
        tau_sigma_inv = np.linalg.inv(tau * sigma)
        omega_inv = np.linalg.inv(omega)

        post_cov_inv = tau_sigma_inv + p.T @ omega_inv @ p
        post_cov = np.linalg.inv(post_cov_inv)
        post_er = post_cov @ (tau_sigma_inv @ pi + p.T @ omega_inv @ q)

        # 3. Solve for constrained optimal weights (Long-only, sum to 1.0) using CVXPY
        w_var = cp.Variable(n)
        port_ret = post_er.T @ w_var
        port_risk = cp.quad_form(w_var, sigma)  # type: ignore[attr-defined]
        objective = cp.Maximize(port_ret - 0.5 * risk_aversion * port_risk)
        constraints = [cp.sum(w_var) == 1.0, w_var >= 0.0]  # type: ignore[attr-defined]

        problem = cp.Problem(objective, constraints)
        problem.solve()  # type: ignore[no-untyped-call]

        if w_var.value is not None:
            optimal_weights = [max(0.0, float(wi)) for wi in w_var.value]
        else:
            optimal_weights = [1.0 / n] * n

        # Renormalize to exact 1.0 sum
        s = sum(optimal_weights)
        optimal_weights = [w / s for w in optimal_weights]

        return BlackLittermanResult(
            assets=assets,
            market_prior_weights=[float(w) for w in w_mkt],
            optimal_weights=optimal_weights,
            expected_returns=[float(r) for r in post_er],
            implied_prior_returns=[float(r) for r in pi],
        )

    @staticmethod
    def optimize_hierarchical_risk_parity(
        assets: list[str],
        returns_matrix: Sequence[Sequence[float]],
    ) -> HRPAllocationResult:
        """
        Solves Hierarchical Risk Parity (HRP) portfolio optimization (Marcos López de Prado 2016).
        Does not require matrix inversion; stable under high correlation and collinearity.
        """
        r_arr = np.asarray(returns_matrix, dtype=np.float64)
        cov = np.cov(r_arr, rowvar=False)
        corr = np.corrcoef(r_arr, rowvar=False)

        n = len(assets)
        if n == 1:
            return HRPAllocationResult(assets=assets, weights=[1.0], ordered_indices=[0])

        # Step 1: Distance matrix D_ij = sqrt(0.5 * (1 - rho_ij))
        dist = np.sqrt(np.clip(0.5 * (1.0 - corr), 0.0, 1.0))
        np.fill_diagonal(dist, 0.0)

        # Step 2: Hierarchical tree clustering
        dist_condensed = squareform(dist)
        link = linkage(dist_condensed, method="single")

        # Step 3: Quasi-diagonalization
        ordered_idx = list(leaves_list(link))

        # Step 4: Recursive Bisection
        weights = np.ones(n, dtype=np.float64)
        clusters = [ordered_idx]

        while len(clusters) > 0:
            new_clusters = []
            for c in clusters:
                if len(c) > 1:
                    mid = len(c) // 2
                    c1, c2 = c[:mid], c[mid:]

                    cov1 = cov[np.ix_(c1, c1)]
                    cov2 = cov[np.ix_(c2, c2)]

                    # Inverse-variance allocation between the two clusters
                    inv_v1 = 1.0 / np.trace(cov1)
                    inv_v2 = 1.0 / np.trace(cov2)
                    alpha1 = inv_v1 / (inv_v1 + inv_v2)
                    alpha2 = 1.0 - alpha1

                    weights[c1] *= alpha1
                    weights[c2] *= alpha2

                    new_clusters.extend([c1, c2])
            clusters = new_clusters

        # Normalize weights
        weights = weights / np.sum(weights)

        return HRPAllocationResult(
            assets=assets,
            weights=[float(w) for w in weights],
            ordered_indices=ordered_idx,
        )
