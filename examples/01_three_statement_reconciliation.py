"""
Example 01: a one-year three-statement projection with a driver shock, and its balance check.

Demonstrates:
1. Configuring StatementGraph from an opening balance sheet and operating drivers.
2. Applying a driver shock (+10% revenue) and recomputing the three statements.
3. The closing balance check: every balance is rolled forward from its opening value (no plug), so the
   check tests whether the cash flow statement captures every balance-sheet change.
4. That the check can fail: a graph that leaves the change in receivables out of operating cash flow.

All inputs are illustrative round numbers (USD millions), not a real company's figures.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lilavati.core.graph import StatementGraph

console = Console()

# Illustrative opening balance sheet: assets 300 + 600 + 2,500 + 400 = 3,800;
# liabilities 450 + 1,500 + 350 = 2,300; equity 1,000 + 500 = 1,500.
INPUTS = {
    "revenue": 5000.0, "gross_margin": 0.40, "sga_ratio": 0.18, "tax_rate": 0.21, "interest_rate": 0.05,
    "capex": 400.0, "depreciation": 300.0,
    "cash_start": 300.0, "opening_receivables": 600.0, "initial_net_ppe": 2500.0, "other_assets": 400.0,
    "opening_payables": 450.0, "initial_debt": 1500.0, "other_liabilities": 350.0,
    "initial_common_equity": 1000.0, "opening_retained_earnings": 500.0,
    "dso_days": 45.0, "dpo_days": 55.0,
}


class ForgetsReceivables(StatementGraph):
    """A deliberate wiring fault: operating cash flow without the change in receivables."""

    def _operating_cash_flow(self, net_income: float, depreciation: float, change_receivables: float,
                             change_payables: float) -> float:
        return net_income + depreciation + change_payables


def main() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Project Līlāvatī: three-statement projection and its balance check[/bold cyan]\n"
            "Illustrative inputs (USD millions); a +10% revenue shock.",
            title="Statement graph",
        )
    )

    graph = StatementGraph(**INPUTS)
    baseline = graph.compute()

    console.print("\n[bold yellow]Driver shock:[/bold yellow] revenue +10%")
    shocked = graph.with_drivers(revenue=INPUTS["revenue"] * 1.10).compute()

    table = Table(title="Statement graph: baseline vs shocked", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline ($M)", justify="right")
    table.add_column("Post-shock ($M)", justify="right", style="bold green")
    rows = [
        ("Revenue", lambda m: m.income_statement.revenue),
        ("Operating income (EBIT)", lambda m: m.income_statement.operating_income),
        ("Net income", lambda m: m.income_statement.net_income),
        ("Cash flow from operations (CFO)", lambda m: m.cash_flow_statement.cfo),
        ("Receivables", lambda m: m.balance_sheet.accounts_receivable),
        ("Payables", lambda m: m.balance_sheet.accounts_payable),
        ("Ending cash", lambda m: m.balance_sheet.cash_and_equivalents),
        ("Total assets", lambda m: m.balance_sheet.total_assets),
        ("Total liabilities", lambda m: m.balance_sheet.total_liabilities),
        ("Shareholders' equity", lambda m: m.balance_sheet.total_equity),
    ]
    for label, get in rows:
        table.add_row(label, f"{get(baseline):,.1f}", f"{get(shocked):,.1f}")
    console.print(table)
    console.print(
        f"\n[bold]Closing balance check (Z3, on the computed numbers):[/bold] baseline "
        f"{baseline.is_balanced and baseline.cash_reconciled}, shocked {shocked.is_balanced and shocked.cash_reconciled}"
    )

    faulty = ForgetsReceivables(**INPUTS).with_drivers(revenue=INPUTS["revenue"] * 1.10).compute()
    b = faulty.balance_sheet
    console.print(
        f"[bold]Same shock, CFO without the change in receivables:[/bold] balanced {faulty.is_balanced}; "
        f"assets {b.total_assets:,.1f} vs liabilities + equity {b.total_liabilities + b.total_equity:,.1f}"
    )


if __name__ == "__main__":
    main()
