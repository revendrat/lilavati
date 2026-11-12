"""
Golden Datasets and Canonical Evaluation Scenarios for Līlāvatī-Bench.

Contains authoritative reference test cases across all seven foundational tracks:
Track 1: Three-Statement Dynamic Reconciliation
Track 2: Fixed Income, Credit & Debt Waterfalls
Track 3: Econometric Rigor & Spurious Correlation Resistance
Track 4: Financial ML Methodological Soundness (de Prado)
Track 5: Derivatives & Volatility Arbitrage Invariance
Track 6: Market Microstructure & Optimal Execution
Track 7: Sustainable Finance & Climate Stress Testing
"""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkTestCase(BaseModel):
    """Canonical test case specification for financial agent evaluation."""

    model_config = ConfigDict(frozen=True)

    case_id: str = Field(..., description="Unique case identifier (e.g. LILAVATI-T1-001)")
    track: str = Field(..., description="Evaluation track identifier")
    title: str = Field(..., description="Descriptive title of the scenario")
    prompt: str = Field(..., description="The query presented to the financial agent")
    as_of_date: date = Field(..., description="Point-in-time cutoff date")
    doc_hash: str = Field(..., description="SHA-256 hash of statutory source document")
    source_citation: str = Field(..., description="Document provenance reference")
    context_data: dict[str, Any] = Field(
        default_factory=dict, description="Input parameters and time-series"
    )
    expected_values: dict[str, Any] = Field(..., description="Ground-truth quantitative values")
    tolerance: float = Field(
        default=1e-3, description="Acceptable numerical relative error tolerance"
    )


def _gen_doc_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Ground truth statutory source document hashes
DOC_HASH_AAPL_2024 = _gen_doc_hash("SEC_EDGAR_AAPL_10K_FY2024_ANNUAL_REPORT_STATUTORY")
DOC_HASH_US_TREASURY_2024 = _gen_doc_hash("US_DEPARTMENT_OF_THE_TREASURY_YIELD_CURVE_2024")
DOC_HASH_FED_MACRO_2024 = _gen_doc_hash("FEDERAL_RESERVE_ECONOMIC_DATA_ST_LOUIS_FRED_2024")
DOC_HASH_CBOE_SPX_2024 = _gen_doc_hash("CBOE_SPX_OPTIONS_VOLATILITY_SURFACE_2024")
DOC_HASH_NASDAQ_ITCH_2024 = _gen_doc_hash("NASDAQ_TOTALVIEW_ITCH_5_0_ORDER_BOOK_FEED_2024")
DOC_HASH_GHG_PROTOCOL_2024 = _gen_doc_hash("GHG_PROTOCOL_SCOPE_1_2_3_STANDARDS_TCFD_2024")


GOLDEN_BENCHMARK_CASES: list[BenchmarkTestCase] = [
    # Track 1: Three-Statement Dynamic Reconciliation
    BenchmarkTestCase(
        case_id="LILAVATI-T1-001",
        track="track1_three_statement",
        title="Dynamic Balance Sheet & Cash Flow Reconciliation under Revenue Shock",
        prompt=(
            "Given Apple Inc. FY2024 canonical statement baselines (Assets=364980, Liabilities=308030, "
            "Equity=56950, Cash=29943), apply a revenue shock. Reconcile the 3 statements "
            "and verify that Cash End reconciles and Balance Sheet balances via SMT invariant."
        ),
        as_of_date=date(2024, 11, 1),
        doc_hash=DOC_HASH_AAPL_2024,
        source_citation="Apple Inc. Form 10-K FY2024 (SEC CIK: 0000320193), Item 8, pp. 48-52",
        context_data={
            "total_assets": 364980.0,
            "total_liabilities": 308030.0,
            "total_equity": 56950.0,
            "cash_start": 29943.0,
            "revenue": 391035.0,
            "net_income": 93736.0,
            "cfo": 118264.0,
            "cfi": -2400.0,
            "cff": -115867.0,
            "cash_end": 29940.0,
        },
        expected_values={
            "is_balanced": True,
            "cash_reconciled": True,
            "assets_equal_liab_equity": True,
        },
    ),
    # Track 2: Fixed Income, Credit & Debt Waterfalls
    BenchmarkTestCase(
        case_id="LILAVATI-T2-001",
        track="track2_fixed_income",
        title="Corporate Bond Duration, Convexity and Structural Merton Default Probability",
        prompt=(
            "Calculate Macaulay duration and modified duration for a 5-year par bond with face 100, "
            "coupon 5% paid annually, yield-to-maturity 5%. Then evaluate the 1-year Merton structural "
            "model for a firm with equity value E=100, debt face D=80, equity volatility 40%, and risk-free rate 5%."
        ),
        as_of_date=date(2024, 10, 15),
        doc_hash=DOC_HASH_US_TREASURY_2024,
        source_citation="US Treasury Yield Curve Bulletin & Moody's Credit Methodology 2024",
        context_data={
            "face_value": 100.0,
            "coupon_rate": 0.05,
            "ytm": 0.05,
            "maturity_years": 5.0,
            "equity_value": 100.0,
            "debt_face": 80.0,
            "equity_volatility": 0.40,
            "risk_free_rate": 0.05,
            "horizon_years": 1.0,
        },
        expected_values={
            "bond_price": 100.0,
            "macaulay_duration_in_range": True,
            "merton_distance_to_default_positive": True,
            "default_probability_in_range": True,
        },
        tolerance=0.05,
    ),
    # Track 3: Econometric Rigor & Spurious Correlation Resistance
    BenchmarkTestCase(
        case_id="LILAVATI-T3-001",
        track="track3_econometrics",
        title="Spurious Regression Rejection via Augmented Dickey-Fuller & Cointegration Testing",
        prompt=(
            "Test whether a unit-root random walk is stationary, and compute the Ornstein-Uhlenbeck "
            "mean-reversion half-life. The agent must reject stationarity on raw random walks."
        ),
        as_of_date=date(2024, 9, 30),
        doc_hash=DOC_HASH_FED_MACRO_2024,
        source_citation="St. Louis Fed Econometric Research Series & Engle-Granger Cointegration Standards",
        context_data={
            "n_samples": 200,
        },
        expected_values={
            "series_non_stationary": True,
            "rejects_spurious_relationship": True,
        },
    ),
    # Track 4: Financial ML Methodological Soundness (de Prado)
    BenchmarkTestCase(
        case_id="LILAVATI-T4-001",
        track="track4_financial_ml",
        title="Optimal Fractional Differentiation d* and Stationarity Memory Preservation",
        prompt=(
            "Given a non-stationary price series, determine the minimal fractional differentiation order d* "
            "in [0, 1] that achieves ADF stationarity (p-value < 0.05) while retaining memory (correlation > 0.70)."
        ),
        as_of_date=date(2024, 8, 31),
        doc_hash=DOC_HASH_FED_MACRO_2024,
        source_citation="Advances in Financial Machine Learning (Marcos Lopez de Prado, 2018)",
        context_data={
            "min_correlation": 0.70,
            "adf_p_threshold": 0.05,
        },
        expected_values={
            "is_stationary_after_fracdiff": True,
            "memory_preserved": True,
        },
    ),
    # Track 5: Derivatives & Volatility Arbitrage Invariance
    BenchmarkTestCase(
        case_id="LILAVATI-T5-001",
        track="track5_derivatives",
        title="BSM Greek Neutrality and SMT Butterfly Spread Arbitrage Verification",
        prompt=(
            "Price a 1-year European call option with S=100, K=100, r=5%, sigma=20%. Calculate Delta, "
            "Gamma, Vega. Then formally verify with Z3 that a butterfly spread with strikes K1=90, K2=100, "
            "K3=110 satisfies non-negative risk-neutral density condition (C(K1) - 2C(K2) + C(K3) >= 0)."
        ),
        as_of_date=date(2024, 10, 1),
        doc_hash=DOC_HASH_CBOE_SPX_2024,
        source_citation="CBOE SPX Options Specifications & Carr-Madan Risk Neutral Density Arbitrage Bounds",
        context_data={
            "spot": 100.0,
            "strike": 100.0,
            "rate": 0.05,
            "volatility": 0.20,
            "maturity": 1.0,
            "k1": 90.0,
            "k2": 100.0,
            "k3": 110.0,
        },
        expected_values={
            "call_price": 10.45,
            "delta": 0.637,
            "gamma": 0.0187,
            "vega": 0.375,
            "butterfly_arbitrage_free": True,
        },
        tolerance=0.05,
    ),
    # Track 6: Market Microstructure & Optimal Execution
    BenchmarkTestCase(
        case_id="LILAVATI-T6-001",
        track="track6_microstructure",
        title="Limit Order Book Microprice, OFI, and Almgren-Chriss Liquidation Trajectory",
        prompt=(
            "Given Level 2 order book snapshot (Bid=100.00 x 500 shares, Ask=100.10 x 200 shares), calculate "
            "the volume-weighted microprice and spread. Then compute the Almgren-Chriss optimal liquidation "
            "trajectory for 100,000 shares over 5 intervals."
        ),
        as_of_date=date(2024, 11, 8),
        doc_hash=DOC_HASH_NASDAQ_ITCH_2024,
        source_citation="NASDAQ TotalView-ITCH 5.0 Market Data & Almgren-Chriss (2000) Optimal Execution",
        context_data={
            "bid_price": 100.00,
            "bid_size": 500.0,
            "ask_price": 100.10,
            "ask_size": 200.0,
            "total_shares": 100000.0,
            "periods": 5,
        },
        expected_values={
            "spread": 0.10,
            "microprice": 100.071,
            "initial_liquidation_shares": 100000.0,
            "final_shares_remaining": 0.0,
        },
        tolerance=0.05,
    ),
    # Track 7: Sustainable Finance & Climate Stress Testing
    BenchmarkTestCase(
        case_id="LILAVATI-T7-001",
        track="track7_sustainability",
        title="Weighted Average Carbon Intensity (WACI) and SLB Coupon Step-Up Invariant",
        prompt=(
            "Calculate the portfolio WACI for an equity basket of 2 firms. Then evaluate whether a "
            "Sustainability-Linked Bond with baseline Scope 1+2 emissions of 100,000 tCO2e triggers a "
            "25 bps coupon step-up when target reduction is 20% but reported emissions are 90,000 tCO2e (only 10% reduction)."
        ),
        as_of_date=date(2024, 10, 31),
        doc_hash=DOC_HASH_GHG_PROTOCOL_2024,
        source_citation="TCFD Recommendations (2017) & ICMA Sustainability-Linked Bond Principles (2023)",
        context_data={
            "weights": [0.6, 0.4],
            "emissions": [50000.0, 120000.0],
            "revenues_mil": [500.0, 800.0],
            "slb_isin": "XS2345678901",
            "slb_notional": 50000000.0,
            "slb_base_coupon": 0.04,
            "slb_target_reduction": 0.20,
            "slb_baseline_emissions": 100000.0,
            "slb_step_up_bps": 25.0,
            "slb_target_year": 2026,
            "slb_reported_emissions": 90000.0,
        },
        expected_values={
            "portfolio_waci": 120.0,
            "slb_spt_achieved": False,
            "slb_active_coupon": 0.0425,
            "slb_penalty_triggered": True,
        },
        tolerance=0.01,
    ),
]


def load_all_test_cases() -> list[BenchmarkTestCase]:
    """Returns the complete list of canonical golden test cases."""
    return list(GOLDEN_BENCHMARK_CASES)


def get_cases_by_track(track: str) -> list[BenchmarkTestCase]:
    """Filters golden benchmark cases by track identifier."""
    return [c for c in GOLDEN_BENCHMARK_CASES if c.track == track]
