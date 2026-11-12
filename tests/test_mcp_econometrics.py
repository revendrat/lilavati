import numpy as np

from lilavati.mcp_servers.econometrics_server import (
    analyze_cointegration,
    analyze_stationarity,
    fit_garch_volatility,
)


def test_mcp_stationarity_tool() -> None:
    np.random.seed(42)
    series = np.random.normal(0, 1, 100).tolist()
    report = analyze_stationarity(series)

    assert "is_stationary" in report
    assert report["is_stationary"] is True
    assert "p_value" in report


def test_mcp_cointegration_tool() -> None:
    np.random.seed(42)
    base = np.cumsum(np.random.normal(0, 1, 150))
    a = (1.8 * base + np.random.normal(0, 0.2, 150)).tolist()
    b = (base + np.random.normal(0, 0.2, 150)).tolist()

    report = analyze_cointegration(a, b)

    assert "is_cointegrated" in report
    assert report["is_cointegrated"] is True
    assert "hedge_ratio" in report
    assert abs(report["hedge_ratio"] - 1.8) < 0.2


def test_mcp_garch_tool() -> None:
    np.random.seed(42)
    returns = np.random.normal(0.0002, 0.012, 150).tolist()
    report = fit_garch_volatility(returns)

    assert "annualized_volatility" in report
    assert "persistence" in report
    assert report["annualized_volatility"] > 0
