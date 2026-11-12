import numpy as np

from lilavati.mcp_servers.financial_ml_server import (
    apply_triple_barrier_labels,
    find_optimal_fractional_diff,
)


def test_mcp_fractional_diff_tool() -> None:
    np.random.seed(42)
    random_walk = (100.0 + np.cumsum(np.random.normal(0, 1.0, 250))).tolist()
    report = find_optimal_fractional_diff(random_walk, step=0.1, target_p_value=0.05)

    assert "optimal_d" in report
    assert "adf_p_value" in report
    assert report["optimal_d"] > 0.0


def test_mcp_triple_barrier_tool() -> None:
    prices = [100.0, 102.0, 106.0, 101.0, 99.0, 100.0]
    labels = apply_triple_barrier_labels(
        prices=prices,
        holding_horizon=2,
        take_profit_pct=0.04,
        stop_loss_pct=0.04,
    )

    assert len(labels) == 4
    # Jump from 100 to 106 on step 2 is +6% >= +4%
    assert labels[0]["label"] == 1
