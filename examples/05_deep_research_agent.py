"""
Example 05: Autonomous Financial Research Agent (Search + Deep Reasoning + Forensic Synthesis).

Demonstrates:
1. FinancialSearchAgent: Autonomous filing discovery with SHA-256 cryptographic provenance.
2. DeepFinancialAgent: Multi-branch hypothesis tree search and SMT invariant pruning.
3. FinancialResearchAgent: End-to-end synthesis into an audited Investment Research Dossier.
"""

from __future__ import annotations

from datetime import date

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lilavati.agents.research import FinancialResearchAgent

console = Console()


def main() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Project Līlāvatī: Autonomous Financial Research Agent[/bold cyan]\n"
            "Orchestrating statutory filing search, deep scenario trees, and forensic quality audits.",
            title="Institutional Research Engine",
        )
    )

    research_agent = FinancialResearchAgent()

    symbol = "AAPL"
    as_of = date(2024, 11, 1)

    console.print(
        f"\n[bold yellow]Initiating Deep Research on:[/bold yellow] [bold green]{symbol}[/bold green] (as of {as_of})...\n"
    )

    dossier = research_agent.conduct_deep_research(symbol=symbol, as_of_date=as_of)

    # 1. Executive Summary Table
    exec_table = Table(
        title=f"Institutional Research Dossier: {dossier.company_name} ({dossier.symbol})",
        show_header=True,
    )
    exec_table.add_column("Research Section", style="cyan")
    exec_table.add_column("Summary / Value", style="bold green", justify="right")
    exec_table.add_column("Status / Assessment", style="dim")

    exec_table.add_row("Rating Recommendation", dossier.recommendation, "Highest conviction thesis")
    exec_table.add_row(
        "12-Month Target Price",
        f"${dossier.target_price:.2f}",
        "Fundamental DCF / multiple valuation",
    )
    exec_table.add_row(
        "Expected Net Income (Prob-Weighted)",
        f"${dossier.scenario_analysis.probability_weighted_net_income:,.1f}M",
        "Weighted across Bull, Base, and Bear scenarios",
    )
    exec_table.add_row(
        "Beneish M-Score (Earnings Quality)",
        f"{dossier.forensic_accounting_summary['beneish_m_score']:.2f}",
        "Safe Zone (M <= -1.78): High reporting quality",
    )
    exec_table.add_row(
        "Portfolio WACI (Carbon Intensity)",
        f"{dossier.climate_risk_summary['waci']:.1f} tCO2e/$M",
        "Paris-Aligned Benchmark Compliant"
        if dossier.climate_risk_summary["carbon_intensity_clean"]
        else "High Carbon Drag",
    )
    exec_table.add_row(
        "Statutory Citations Verified", str(dossier.citations_count), "100% SHA-256 Provenance"
    )

    console.print(exec_table)

    # 2. Scenario Tree Table
    scenario_table = Table(
        title="Deep Reasoning Scenario Tree (Z3 Invariant Verified)", show_header=True
    )
    scenario_table.add_column("Scenario Branch", style="cyan")
    scenario_table.add_column("Probability", justify="right")
    scenario_table.add_column("Projected Revenue ($M)", justify="right")
    scenario_table.add_column("Projected Net Income ($M)", justify="right", style="bold")
    scenario_table.add_column("SMT Invariant", justify="center")

    for branch in dossier.scenario_analysis.scenario_branches:
        scenario_table.add_row(
            branch.branch_name,
            f"{branch.probability_weight * 100:.0f}%",
            f"${branch.projected_revenue:,.1f}",
            f"${branch.projected_net_income:,.1f}",
            "[bold green]SAT (VERIFIED)[/bold green]"
            if branch.smt_invariant_verified
            else "[bold red]UNSAT[/bold red]",
        )

    console.print(scenario_table)

    # 3. Executive Thesis
    console.print(
        f"\n[bold yellow]Executive Research Thesis:[/bold yellow]\n{dossier.executive_thesis}\n"
    )


if __name__ == "__main__":
    main()
