"""
Example 02: Quantitative Statistical Arbitrage & Cointegration Testing.

Demonstrates:
1. Synthesizing paired price series.
2. Testing Augmented Dickey-Fuller (ADF) stationarity.
3. Estimating optimal OLS hedge ratio and Ornstein-Uhlenbeck mean-reversion half-life.
4. Fitting GARCH(1,1) volatility persistence.
"""

import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lilavati.core.econometrics import EconometricEngine

console = Console()


def main() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Project Līlāvatī: Statistical Arbitrage & Econometric Modeling[/bold cyan]\n"
            "Testing cointegration, mean-reversion half-life, and GARCH volatility.",
            title="Quantitative Trading & Econometrics",
        )
    )

    np.random.seed(42)
    n = 250

    # Simulate Asset B as an I(1) random walk
    innovations = np.random.normal(0, 1.0, n)
    series_b = (100.0 + np.cumsum(innovations)).tolist()

    # Simulate Asset A cointegrated with B (hedge ratio beta=1.5, mean-reverting spread)
    theta = 0.20  # Mean reversion speed
    spread = np.zeros(n)
    for t in range(1, n):
        spread[t] = spread[t - 1] - theta * spread[t - 1] + np.random.normal(0, 0.5)

    series_a = [10.0 + 1.5 * b + s for b, s in zip(series_b, spread, strict=True)]

    # 1. Test Stationarity of Individual Series
    adf_a = EconometricEngine.test_stationarity(series_a)
    adf_b = EconometricEngine.test_stationarity(series_b)

    # 2. Test Cointegration
    coint_res = EconometricEngine.test_cointegration(series_a, series_b)

    # 3. Fit GARCH(1,1) Volatility
    returns = np.diff(np.log(series_a)).tolist()
    garch_res = EconometricEngine.fit_garch(returns)

    # Output Results
    table = Table(title="Econometric Diagnostics & Stat-Arb Summary", show_header=True)
    table.add_column("Diagnostic Test", style="cyan")
    table.add_column("Result", style="bold green", justify="right")
    table.add_column("Interpretation", style="dim")

    table.add_row(
        "Series A Unit Root (ADF)",
        f"p={adf_a.p_value:.4f}",
        "Non-Stationary (I(1))" if not adf_a.is_stationary else "Stationary",
    )
    table.add_row(
        "Series B Unit Root (ADF)",
        f"p={adf_b.p_value:.4f}",
        "Non-Stationary (I(1))" if not adf_b.is_stationary else "Stationary",
    )
    table.add_row(
        "Engle-Granger Cointegration",
        f"p={coint_res.p_value:.4f}",
        "Cointegrated Pair" if coint_res.is_cointegrated else "Spurious",
    )
    table.add_row(
        "Optimal Hedge Ratio (Beta)", f"{coint_res.hedge_ratio:.3f}", "Units of B per 1 unit of A"
    )
    table.add_row(
        "OU Mean-Reversion Half-Life",
        f"{coint_res.half_life:.1f} days",
        "Expected time to decay 50%",
    )
    table.add_row(
        "GARCH(1,1) Persistence (α + β)",
        f"{garch_res.persistence:.3f}",
        "Volatility clustering memory",
    )
    table.add_row(
        "Annualized Volatility Forecast",
        f"{garch_res.annualized_volatility * 100:.1f}%",
        "Latest conditional volatility",
    )

    console.print(table)


if __name__ == "__main__":
    main()
