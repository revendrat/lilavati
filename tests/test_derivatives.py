import math

import pytest

from lilavati.core.derivatives import DerivativesEngine


def test_black_scholes_put_call_parity() -> None:
    spot = 100.0
    strike = 105.0
    t = 1.0
    r = 0.05
    q = 0.02
    vol = 0.20

    call_res = DerivativesEngine.price_european_option(
        spot, strike, t, r, vol, dividend_yield=q, is_call=True
    )
    put_res = DerivativesEngine.price_european_option(
        spot, strike, t, r, vol, dividend_yield=q, is_call=False
    )

    # Put-Call Parity: C - P == S * exp(-qT) - K * exp(-rT)
    lhs = call_res.price - put_res.price
    rhs = spot * math.exp(-q * t) - strike * math.exp(-r * t)

    assert lhs == pytest.approx(rhs, abs=1e-4)


def test_bsm_greeks_properties() -> None:
    spot = 100.0
    strike = 100.0
    t = 0.5
    r = 0.04
    vol = 0.25

    greeks = DerivativesEngine.calculate_bsm_greeks(spot, strike, t, r, vol, is_call=True)

    # ATM Call Delta should be approximately 0.5 ~ 0.55
    assert 0.50 < greeks.delta < 0.60
    # Gamma and Vega must be strictly positive
    assert greeks.gamma > 0.0
    assert greeks.vega > 0.0
    # Theta should be negative (calendar decay)
    assert greeks.theta < 0.0
    # Volga (vomma) exists and is non-zero
    assert isinstance(greeks.volga, float)
    assert isinstance(greeks.vanna, float)


def test_american_option_early_exercise() -> None:
    spot = 80.0
    strike = 100.0  # Deep in the money Put
    t = 1.0
    r = 0.10  # High interest rate favors early exercise of puts
    vol = 0.20

    euro_put = DerivativesEngine.price_european_option(spot, strike, t, r, vol, is_call=False)
    amer_put = DerivativesEngine.price_american_option_crr(
        spot, strike, t, r, vol, is_call=False, steps=150
    )

    # American put must be worth at least as much as European put, and at least intrinsic value (100 - 80 = 20)
    assert amer_put.price >= euro_put.price
    assert amer_put.price >= (strike - spot)


def test_implied_volatility_inversion() -> None:
    target_vol = 0.28
    res = DerivativesEngine.price_european_option(100.0, 100.0, 1.0, 0.05, target_vol, is_call=True)

    recovered_vol = DerivativesEngine.calculate_implied_volatility(
        price=res.price,
        spot=100.0,
        strike=100.0,
        time_to_maturity=1.0,
        risk_free_rate=0.05,
        is_call=True,
    )

    assert recovered_vol == pytest.approx(target_vol, abs=1e-4)


def test_sabr_volatility_calibration() -> None:
    f = 100.0
    strikes = [80.0, 90.0, 100.0, 110.0, 120.0]
    # Realistic volatility smile (higher OTM put vols)
    market_vols = [0.32, 0.27, 0.24, 0.25, 0.28]
    t = 1.0

    calib = DerivativesEngine.calibrate_sabr(f, strikes, market_vols, t, beta=0.5)

    assert calib.alpha > 0.0
    assert -1.0 <= calib.rho <= 1.0
    assert calib.nu > 0.0
    assert calib.rmse < 0.03


def test_butterfly_arbitrage_verification() -> None:
    strikes = [90.0, 100.0, 110.0]

    # Valid convex call prices: C(90)=15, C(100)=8, C(110)=3
    # Butterfly spread: 15 - 2*8 + 3 = 2 >= 0
    valid_prices = [15.0, 8.0, 3.0]
    valid_res = DerivativesEngine.verify_butterfly_arbitrage(strikes, valid_prices)
    assert valid_res.is_valid is True
    assert len(valid_res.violations) == 0

    # Non-convex prices violating no-arbitrage: C(90)=15, C(100)=6, C(110)=1
    # Butterfly spread: 15 - 2*6 + 1 = 4 > 0 (convex)
    # Violating: C(90)=10, C(100)=9, C(110)=1
    # Butterfly spread: 10 - 2*9 + 1 = -7 < 0 -> Negative risk-neutral probability!
    invalid_prices = [10.0, 9.0, 1.0]
    invalid_res = DerivativesEngine.verify_butterfly_arbitrage(strikes, invalid_prices)
    assert invalid_res.is_valid is False
    assert len(invalid_res.violations) > 0
    assert "Butterfly arbitrage violated" in invalid_res.violations[0]
