"""
Example 01: Dynamic Three-Statement Modeling with SMT Invariant Verification.

Demonstrates:
1. Configuring the reactive StatementGraph DAG.
2. Dynamically updating operational drivers (e.g. +10% revenue expansion).
3. Recomputing the three statements reactively.
4. Formally proving mathematical balance via SuvarnaEngine (Z3 SMT solver).
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lilavati.core.graph import StatementGraph
from lilavati.core.invariants import SuvarnaEngine

console = Console()


def main() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Project Līlāvatī: Dynamic Three-Statement Modeling & SMT Verification[/bold cyan]\n"
            "Formally proving balance sheet identities under operational stress.",
            title="Institutional Financial Modeling",
        )
    )

    # 1. Initialize StatementGraph with baseline drivers (in $M)
    graph = StatementGraph(
        revenue=391035.0,
        gross_margin=0.46,
        sga_ratio=0.15,
        tax_rate=0.21,
        interest_rate=0.04,
        capex=12000.0,
        depreciation=11500.0,
        cash_start=29943.0,
        initial_debt=100000.0,
        initial_common_equity=50000.0,
        initial_net_ppe=184950.0,
    )

    baseline_model = graph.compute()

    # 2. Apply a +10% Gross Revenue Expansion Shock
    console.print(
        "\n[bold yellow]Applying Driver Shock:[/bold yellow] +10% Gross Revenue Expansion..."
    )
    new_rev = baseline_model.income_statement.revenue * 1.10
    graph.set_driver("revenue", new_rev)
    shocked_model = graph.compute()

    # 3. Formal Invariant Verification via Z3 SMT Solver
    verification = SuvarnaEngine.verify_three_statement_invariants(
        total_assets=shocked_model.balance_sheet.total_assets,
        total_liabilities=shocked_model.balance_sheet.total_liabilities,
        shareholders_equity=shocked_model.balance_sheet.total_equity,
        net_income=shocked_model.income_statement.net_income,
        cash_start=graph.drivers["cash_start"],
        cash_end=shocked_model.balance_sheet.cash_and_equivalents,
        cfo=shocked_model.cash_flow_statement.cfo,
        cfi=shocked_model.cash_flow_statement.cfi,
        cff=shocked_model.cash_flow_statement.cff,
    )

    # 4. Display Results
    table = Table(title="Three-Statement Reactive Graph: Baseline vs Shocked", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline ($M)", justify="right")
    table.add_column("Post-Shock ($M)", justify="right", style="bold green")

    table.add_row(
        "Revenue",
        f"{baseline_model.income_statement.revenue:,.1f}",
        f"{shocked_model.income_statement.revenue:,.1f}",
    )
    table.add_row(
        "Operating Income (EBIT)",
        f"{baseline_model.income_statement.operating_income:,.1f}",
        f"{shocked_model.income_statement.operating_income:,.1f}",
    )
    table.add_row(
        "Net Income",
        f"{baseline_model.income_statement.net_income:,.1f}",
        f"{shocked_model.income_statement.net_income:,.1f}",
    )
    table.add_row(
        "Cash Flow from Operations (CFO)",
        f"{baseline_model.cash_flow_statement.cfo:,.1f}",
        f"{shocked_model.cash_flow_statement.cfo:,.1f}",
    )
    table.add_row(
        "Ending Cash Balance",
        f"{baseline_model.balance_sheet.cash_and_equivalents:,.1f}",
        f"{shocked_model.balance_sheet.cash_and_equivalents:,.1f}",
    )
    table.add_row(
        "Total Assets",
        f"{baseline_model.balance_sheet.total_assets:,.1f}",
        f"{shocked_model.balance_sheet.total_assets:,.1f}",
    )
    table.add_row(
        "Total Liabilities",
        f"{baseline_model.balance_sheet.total_liabilities:,.1f}",
        f"{shocked_model.balance_sheet.total_liabilities:,.1f}",
    )
    table.add_row(
        "Shareholders' Equity",
        f"{baseline_model.balance_sheet.total_equity:,.1f}",
        f"{shocked_model.balance_sheet.total_equity:,.1f}",
    )

    console.print(table)
    console.print(
        f"\n[bold]Z3 SMT Invariant Verification Status:[/bold] {verification.status} "
        f"(Balance Sheet Equilibrated & Cash Reconciled: [green]{verification.is_valid}[/green])"
    )


if __name__ == "__main__":
    main()
