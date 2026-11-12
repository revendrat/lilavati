"""
Market & Macroeconomic Data Connector.

Fetches and normalizes:
1. Benchmark sovereign yield curves (Treasury yields, SOFR, Fed Funds).
2. Historical OHLCV asset price series normalized into high-performance Polars DataFrames.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import polars as pl
from pydantic import BaseModel, ConfigDict

from lilavati.core.fixed_income import FixedIncomeEngine, NelsonSiegelCurveResult


class MacroYieldObservation(BaseModel):
    """Sovereign benchmark yield observation."""

    model_config = ConfigDict(frozen=True)

    observation_date: date
    maturity_years: float
    yield_rate: float
    series_name: str


class MarketDataClient:
    """Async/sync client for market and macroeconomic series."""

    # Standard US Treasury benchmark constant maturity series IDs
    TREASURY_MATURITY_MAP: dict[str, float] = {
        "DGS1MO": 1.0 / 12.0,
        "DGS3MO": 3.0 / 12.0,
        "DGS6MO": 6.0 / 12.0,
        "DGS1": 1.0,
        "DGS2": 2.0,
        "DGS5": 5.0,
        "DGS10": 10.0,
        "DGS20": 20.0,
        "DGS30": 30.0,
    }

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    @staticmethod
    def normalize_ohlcv_dataframe(
        records: list[dict[str, Any]],
    ) -> pl.DataFrame:
        """
        Normalizes raw price bars into a canonical, sorted Polars DataFrame.
        Columns: timestamp (Datetime), open (Float64), high (Float64), low (Float64),
                 close (Float64), volume (Float64), return (Float64).
        """
        if not records:
            return pl.DataFrame(
                schema={
                    "timestamp": pl.Datetime,
                    "open": pl.Float64,
                    "high": pl.Float64,
                    "low": pl.Float64,
                    "close": pl.Float64,
                    "volume": pl.Float64,
                    "return": pl.Float64,
                }
            )

        df = pl.DataFrame(records)
        # Ensure timestamp is datetime and sort chronologically
        if "timestamp" in df.columns and df["timestamp"].dtype == pl.String:
            df = df.with_columns(pl.col("timestamp").str.to_datetime())

        df = df.sort("timestamp")
        # Vectorized simple return calculation
        if "close" in df.columns:
            df = df.with_columns(
                ((pl.col("close") - pl.col("close").shift(1)) / pl.col("close").shift(1))
                .fill_null(0.0)
                .alias("return")
            )

        return df

    @staticmethod
    def construct_yield_curve_dataframe(
        observations: list[MacroYieldObservation],
    ) -> pl.DataFrame:
        """Constructs a sorted Polars DataFrame of observed term structure yields."""
        dicts = [obs.model_dump() for obs in observations]
        df = pl.DataFrame(dicts)
        return df.sort("maturity_years")

    @staticmethod
    def fit_curve_from_observations(
        observations: list[MacroYieldObservation],
    ) -> NelsonSiegelCurveResult:
        """Directly fits the Nelson-Siegel yield curve model to normalized yield observations."""
        df = MarketDataClient.construct_yield_curve_dataframe(observations)
        maturities = df["maturity_years"].to_list()
        yields = df["yield_rate"].to_list()
        return FixedIncomeEngine.fit_nelson_siegel(maturities, yields)
