import numpy as np
import pytest

from lilavati.core.financial_ml import FinancialMLEngine


def test_fractional_weights_convergence() -> None:
    # Weights for d=0.5 should decay to zero
    weights = FinancialMLEngine.get_fractional_weights(d=0.5, size=100, threshold=1e-3)
    assert len(weights) > 1
    assert abs(weights[0]) < 0.05
    # The last weight (most recent lag) is 1.0
    assert abs(weights[-1] - 1.0) < 1e-6


def test_find_optimal_fractional_d() -> None:
    np.random.seed(42)
    # Cumulative random walk I(1)
    random_walk = (100.0 + np.cumsum(np.random.normal(0, 1.0, 300))).tolist()

    result = FinancialMLEngine.find_optimal_fractional_d(random_walk, step=0.1, target_p_value=0.05)

    # Optimal d should be between 0.1 and 1.0
    assert 0.1 <= result.optimal_d <= 1.0
    assert result.adf_p_value <= 0.05
    # Should preserve positive correlation with original series (unlike integer d=1 which drops to near zero)
    assert result.correlation_with_original > 0.0


def test_triple_barrier_labeling() -> None:
    # Construct a simple price sequence: starts at 100, jumps to 105 on step 2
    prices = [100.0, 101.0, 105.0, 98.0, 95.0, 100.0, 102.0]

    # TP = +3%, SL = -3%, Horizon = 3 steps
    labels = FinancialMLEngine.apply_triple_barriers(
        prices=prices,
        holding_horizon=3,
        take_profit_pct=0.03,
        stop_loss_pct=0.03,
    )

    assert len(labels) == len(prices) - 3
    # Step 0: enters at 100. At step 2, price is 105 (+5% >= +3%) -> Take profit touched!
    assert labels[0].label == 1
    assert labels[0].touch_index == 2
    assert labels[0].return_at_touch == pytest.approx(0.05, abs=1e-4)
