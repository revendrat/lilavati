from lilavati.mcp_servers.derivatives_server import (
    calculate_option_greeks,
    calibrate_sabr_volatility_model,
    check_butterfly_arbitrage,
    price_american_option,
    price_european_option,
)


def test_mcp_bsm_tool() -> None:
    res = price_european_option(
        spot=100.0, strike=100.0, time_to_maturity=1.0, risk_free_rate=0.05, volatility=0.20
    )
    assert "price" in res
    assert "greeks" in res
    assert res["price"] > 0.0


def test_mcp_american_tool() -> None:
    res = price_american_option(
        spot=80.0,
        strike=100.0,
        time_to_maturity=1.0,
        risk_free_rate=0.08,
        volatility=0.20,
        is_call=False,
    )
    assert res["price"] >= 20.0


def test_mcp_greeks_tool() -> None:
    greeks = calculate_option_greeks(
        spot=100.0, strike=100.0, time_to_maturity=0.5, risk_free_rate=0.04, volatility=0.25
    )
    assert "delta" in greeks
    assert "gamma" in greeks
    assert "vega" in greeks
    assert "vanna" in greeks


def test_mcp_sabr_tool() -> None:
    res = calibrate_sabr_volatility_model(
        forward=100.0,
        strikes=[80.0, 90.0, 100.0, 110.0, 120.0],
        market_vols=[0.30, 0.26, 0.23, 0.24, 0.27],
        time_to_maturity=1.0,
    )
    assert "alpha" in res
    assert "rho" in res
    assert "nu" in res


def test_mcp_butterfly_arbitrage_tool() -> None:
    res = check_butterfly_arbitrage(strikes=[90.0, 100.0, 110.0], call_prices=[15.0, 8.0, 3.0])
    assert res["is_valid"] is True
    assert len(res["violations"]) == 0
