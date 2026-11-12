from lilavati.mcp_servers.fixed_income_server import (
    analyze_bond,
    evaluate_credit_risk_merton,
    fit_yield_curve,
)


def test_mcp_bond_tool() -> None:
    res = analyze_bond(face_value=100.0, coupon_rate=0.04, ytm=0.04, years_to_maturity=10.0)
    assert "clean_price" in res
    assert "modified_duration" in res
    assert abs(res["clean_price"] - 100.0) < 1e-3


def test_mcp_yield_curve_tool() -> None:
    maturities = [1.0, 2.0, 5.0, 10.0, 30.0]
    yields = [0.04, 0.042, 0.045, 0.048, 0.051]
    res = fit_yield_curve(maturities, yields)

    assert "beta0_level" in res
    assert "r_squared" in res
    assert res["r_squared"] > 0.90


def test_mcp_merton_tool() -> None:
    res = evaluate_credit_risk_merton(
        equity_value=150.0,
        equity_volatility=0.35,
        debt_face_value=100.0,
        risk_free_rate=0.04,
        maturity_years=1.0,
    )

    assert "distance_to_default" in res
    assert "default_probability" in res
    assert res["distance_to_default"] > 0.0

