"""
Example 03: Sustainable Finance, Carbon Accounting, and Climate Risk Stress Testing.

Demonstrates:
1. Portfolio Weighted Average Carbon Intensity (WACI) under TCFD standards.
2. Shadow carbon tax sensitivity on corporate operating margin and interest coverage covenants.
3. Sustainability-Linked Bond (SLB) coupon step-up evaluation.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lilavati.core.sustainability import SustainabilityEngine
from lilavati.schemas.sustainability import SustainabilityLinkedBond

console = Console()


def main() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Project Līlāvatī: Climate Risk & Sustainability Stress Testing[/bold cyan]\n"
            "Evaluating carbon intensity, shadow carbon tax impacts, and SLB covenants.",
            title="Sustainable Finance Engine",
        )
    )

    # 1. Compute Portfolio WACI
    weights = [0.40, 0.35, 0.25]
    emissions = [45000.0, 120000.0, 15000.0]  # Scope 1+2 tCO2e
    revenues_mil = [500.0, 800.0, 300.0]  # $M revenue

    waci_res = SustainabilityEngine.calculate_waci(
        portfolio_weights=weights,
        emissions=emissions,
        revenues_millions=revenues_mil,
    )

    # 2. Stress Test Shadow Carbon Tax on Firm 2
    # Firm 2: $800M Revenue, $120M EBIT, $25M Interest, 120k tCO2e emissions
    stress_res = SustainabilityEngine.stress_test_carbon_tax(
        revenue=800.0,
        ebit=120.0,
        interest_expense=25.0,
        scope1_emissions=80000.0,
        scope2_emissions=40000.0,
        carbon_price_per_ton=0.0001,  # $100/tCO2e scaled to $M units (0.0001 $M = $100)
        pass_through_rate=0.40,  # 40% passed to customers
        covenant_interest_floor=3.0,
    )

    # 3. Evaluate Sustainability-Linked Bond (SLB)
    slb = SustainabilityLinkedBond(
        isin="XS9988776655",
        notional=100000000.0,  # $100M
        base_coupon_rate=0.045,  # 4.5%
        target_reduction_pct=0.25,  # 25% target reduction
        baseline_emissions=120000.0,
        step_up_bps=50.0,  # +50 bps penalty step-up
        target_year=2026,
    )
    # Audited emissions reported at 100,000 tCO2e (only 16.7% reduction, missing 25% target)
    slb_res = SustainabilityEngine.evaluate_slb_covenant(slb, reported_emissions=100000.0)

    # Display Results
    table = Table(title="Climate Transition Risk & Covenant Audit", show_header=True)
    table.add_column("Indicator", style="cyan")
    table.add_column("Value", style="bold green", justify="right")
    table.add_column("Assessment", style="dim")

    table.add_row(
        "Portfolio WACI",
        f"{waci_res.waci:.1f} tCO2e/$M",
        "Paris-Aligned" if waci_res.carbon_intensity_clean else "High Carbon Intensity",
    )
    table.add_row(
        "Pre-Shock EBIT Margin",
        f"{stress_res.ebit_margin_before_pct * 100:.1f}%",
        "Baseline operating margin",
    )
    table.add_row(
        "Post-Shock EBIT Margin",
        f"{stress_res.ebit_margin_after_pct * 100:.1f}%",
        f"-{stress_res.ebit_reduction_pct * 100:.1f}% operating contraction",
    )
    table.add_row(
        "Post-Shock Interest Coverage",
        f"{stress_res.interest_coverage_after:.2f}x",
        "Covenant Breached" if stress_res.is_covenant_at_risk else "Safe",
    )
    table.add_row(
        "SLB Target Achieved", f"{slb_res.spt_achieved}", "Target Missed: Step-up triggered"
    )
    table.add_row(
        "Active SLB Coupon Rate",
        f"{slb_res.active_coupon_rate * 100:.2f}%",
        f"+${slb_res.annual_interest_penalty:,.0f} annual interest penalty",
    )

    console.print(table)


if __name__ == "__main__":
    main()
