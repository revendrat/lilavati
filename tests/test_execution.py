import numpy as np
import pytest

from lilavati.core.execution import ExecutionEngine


def test_lob_microstructure() -> None:
    # Bid: $100 with size 200, Ask: $101 with size 100
    # Mid = 100.5, Microprice = (200*101 + 100*100) / 300 = 30200 / 300 = 100.667
    metrics = ExecutionEngine.analyze_lob_snapshot(
        best_bid=100.0,
        best_ask=101.0,
        bid_size=200.0,
        ask_size=100.0,
        prev_bid_size=180.0,
        prev_ask_size=110.0,
    )

    assert metrics.spread == 1.0
    assert metrics.mid_price == 100.5
    assert metrics.micro_price == pytest.approx(100.6667, abs=1e-3)
    # OFI = (200 - 180) - (100 - 110) = 20 - (-10) = +30 (positive buying pressure)
    assert metrics.order_flow_imbalance == 30.0


def test_lob_crossed_book_fails() -> None:
    with pytest.raises(ValueError):
        ExecutionEngine.analyze_lob_snapshot(
            best_bid=102.0,
            best_ask=100.0,
            bid_size=10.0,
            ask_size=10.0,
        )


def test_almgren_chriss_schedule() -> None:
    total_shares = 100_000.0
    res = ExecutionEngine.compute_almgren_chriss_schedule(
        total_shares=total_shares,
        time_horizon_hours=4.0,
        n_intervals=8,
        daily_volatility=0.02,
    )

    assert res.trading_trajectory[0] == total_shares
    assert abs(res.trading_trajectory[-1]) < 1e-4  # Fully liquidated
    assert sum(res.trade_sizes) == pytest.approx(total_shares, abs=1e-4)

    # Monotonically declining inventory
    for i in range(len(res.trading_trajectory) - 1):
        assert res.trading_trajectory[i] >= res.trading_trajectory[i + 1]

    assert res.expected_shortfall > 0.0
    assert res.shortfall_variance > 0.0


def test_black_litterman_tilt() -> None:
    assets = ["AAPL", "MSFT", "GOOGL"]
    # Diagonal covariance matrix
    cov = [
        [0.04, 0.01, 0.01],
        [0.01, 0.04, 0.01],
        [0.01, 0.01, 0.04],
    ]
    # Equal market priors: 1/3 each
    mkt_weights = [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]

    # View: MSFT will outperform by +10% absolute
    p = [[0.0, 1.0, 0.0]]
    q = [0.10]
    omega_std = [0.02]

    res = ExecutionEngine.optimize_black_litterman(
        assets=assets,
        covariance_matrix=cov,
        market_prior_weights=mkt_weights,
        views_matrix=p,
        views_returns=q,
        views_confidence_std=omega_std,
    )

    assert sum(res.optimal_weights) == pytest.approx(1.0, abs=1e-4)
    # MSFT (index 1) should have received a significant overweight tilt!
    msft_weight = res.optimal_weights[1]
    assert msft_weight > mkt_weights[1]


def test_hierarchical_risk_parity() -> None:
    np.random.seed(42)
    assets = ["AssetA", "AssetB", "AssetC", "AssetD"]

    # Asset A & B low vol, C & D high vol
    n_days = 200
    ret_a = np.random.normal(0, 0.01, n_days)
    ret_b = np.random.normal(0, 0.012, n_days)
    ret_c = np.random.normal(0, 0.03, n_days)
    ret_d = np.random.normal(0, 0.035, n_days)

    returns = np.column_stack([ret_a, ret_b, ret_c, ret_d])

    res = ExecutionEngine.optimize_hierarchical_risk_parity(assets, returns)

    assert len(res.weights) == 4
    assert sum(res.weights) == pytest.approx(1.0, abs=1e-4)
    assert all(w > 0.0 for w in res.weights)

    # Low vol assets (A & B) should receive higher allocations than high vol assets (C & D)
    assert (res.weights[0] + res.weights[1]) > (res.weights[2] + res.weights[3])
