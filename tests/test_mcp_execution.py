import numpy as np

from lilavati.mcp_servers.portfolio_exec_server import (
    analyze_order_book_microstructure,
    compute_almgren_chriss_liquidation_schedule,
    optimize_portfolio_black_litterman,
    optimize_portfolio_hierarchical_risk_parity,
)


def test_mcp_lob_tool() -> None:
    res = analyze_order_book_microstructure(
        best_bid=100.0, best_ask=100.5, bid_size=500.0, ask_size=300.0
    )
    assert "spread" in res
    assert "micro_price" in res
    assert res["spread"] == 0.5


def test_mcp_almgren_chriss_tool() -> None:
    res = compute_almgren_chriss_liquidation_schedule(
        total_shares=50000.0,
        time_horizon_hours=2.0,
        n_intervals=4,
        daily_volatility=0.015,
    )
    assert "trading_trajectory" in res
    assert "expected_shortfall" in res
    assert len(res["trading_trajectory"]) == 5


def test_mcp_black_litterman_tool() -> None:
    cov = [[0.04, 0.0], [0.0, 0.04]]
    res = optimize_portfolio_black_litterman(
        assets=["A", "B"],
        covariance_matrix=cov,
        market_prior_weights=[0.5, 0.5],
        views_matrix=[[1.0, 0.0]],
        views_returns=[0.08],
        views_confidence_std=[0.02],
    )
    assert "optimal_weights" in res
    assert res["optimal_weights"][0] > res["optimal_weights"][1]


def test_mcp_hrp_tool() -> None:
    np.random.seed(42)
    rets = np.random.normal(0, 0.02, (100, 3)).tolist()
    res = optimize_portfolio_hierarchical_risk_parity(assets=["X", "Y", "Z"], returns_matrix=rets)
    assert "weights" in res
    assert len(res["weights"]) == 3
