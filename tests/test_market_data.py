from datetime import date

import polars as pl

from lilavati.connectors.market_data import (
    MacroYieldObservation,
    MarketDataClient,
)


def test_normalize_ohlcv_dataframe() -> None:
    raw_bars = [
        {
            "timestamp": "2024-11-01 09:30:00",
            "open": 100.0,
            "high": 102.0,
            "low": 99.5,
            "close": 101.0,
            "volume": 50000.0,
        },
        {
            "timestamp": "2024-11-01 09:31:00",
            "open": 101.0,
            "high": 103.0,
            "low": 100.8,
            "close": 102.5,
            "volume": 60000.0,
        },
        {
            "timestamp": "2024-11-01 09:32:00",
            "open": 102.5,
            "high": 102.8,
            "low": 101.5,
            "close": 102.0,
            "volume": 45000.0,
        },
    ]

    df = MarketDataClient.normalize_ohlcv_dataframe(raw_bars)

    assert isinstance(df, pl.DataFrame)
    assert df.height == 3
    assert "return" in df.columns
    # Check return calculation on step 1: (102.5 - 101.0) / 101.0 = +1.485%
    returns = df["return"].to_list()
    assert returns[0] == 0.0
    assert abs(returns[1] - (102.5 - 101.0) / 101.0) < 1e-4


def test_construct_yield_curve_and_fit() -> None:
    obs = [
        MacroYieldObservation(
            observation_date=date(2024, 11, 1),
            maturity_years=1.0,
            yield_rate=0.043,
            series_name="DGS1",
        ),
        MacroYieldObservation(
            observation_date=date(2024, 11, 1),
            maturity_years=2.0,
            yield_rate=0.042,
            series_name="DGS2",
        ),
        MacroYieldObservation(
            observation_date=date(2024, 11, 1),
            maturity_years=5.0,
            yield_rate=0.041,
            series_name="DGS5",
        ),
        MacroYieldObservation(
            observation_date=date(2024, 11, 1),
            maturity_years=10.0,
            yield_rate=0.044,
            series_name="DGS10",
        ),
        MacroYieldObservation(
            observation_date=date(2024, 11, 1),
            maturity_years=30.0,
            yield_rate=0.046,
            series_name="DGS30",
        ),
    ]

    curve_res = MarketDataClient.fit_curve_from_observations(obs)

    assert curve_res.r_squared > 0.90
    assert 0.03 < curve_res.beta0_level < 0.08
