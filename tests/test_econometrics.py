import numpy as np

from lilavati.core.econometrics import EconometricEngine


def test_stationarity_white_noise() -> None:
    np.random.seed(42)
    # White noise should be stationary I(0)
    white_noise = np.random.normal(0, 1, 200).tolist()
    result = EconometricEngine.test_stationarity(white_noise)

    assert result.is_stationary is True
    assert result.p_value < 0.05
    assert "stationary" in result.recommendation.lower()


def test_non_stationarity_random_walk() -> None:
    np.random.seed(42)
    # Cumulative sum of white noise is a random walk I(1)
    random_walk = np.cumsum(np.random.normal(0, 1, 200)).tolist()
    result = EconometricEngine.test_stationarity(random_walk)

    assert result.is_stationary is False
    assert result.p_value >= 0.05
    assert "non-stationary" in result.recommendation.lower()


def test_cointegration_synthetic_pair() -> None:
    np.random.seed(42)
    n = 250
    # Common random walk
    common_factor = np.cumsum(np.random.normal(0, 1, n))
    noise_a = np.random.normal(0, 0.5, n)
    noise_b = np.random.normal(0, 0.5, n)

    # Series A and Series B share common factor -> Cointegrated
    series_b = (common_factor + noise_b).tolist()
    series_a = (2.0 * common_factor + noise_a).tolist()

    result = EconometricEngine.test_cointegration(series_a, series_b)

    assert result.is_cointegrated is True
    assert result.p_value < 0.05
    # Hedge ratio should be close to 2.0
    assert abs(result.hedge_ratio - 2.0) < 0.2
    assert result.half_life > 0
    assert result.half_life != float("inf")


def test_garch_fit() -> None:
    np.random.seed(42)
    n = 300
    # Simulate basic returns
    returns = np.random.normal(0.0005, 0.015, n).tolist()
    result = EconometricEngine.fit_garch(returns, p=1, q=1)

    assert result.p == 1
    assert result.q == 1
    assert len(result.alpha_coeffs) == 1
    assert len(result.beta_coeffs) == 1
    assert 0.0 <= result.persistence <= 1.05
    assert result.annualized_volatility > 0.0
