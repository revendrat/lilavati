"""
Example 05: research workflow on one 10-K, every input reported, cited and checked.

FinancialResearchAgent takes the latest 10-K filed on or before the as-of date and uses only that
filing's own XBRL facts (this year and the prior-year comparatives it reports): the three-statement
model with its checks, the rule-based committee (Beneish, Altman, identity checks), a scenario tree
calibrated from the filing, and a check that every citation resolves against the SEC data read.
Inputs not taken from the filing are listed. A screen on reported figures, not investment advice.

By default it runs offline on a verbatim SEC subset of Apple's FY2026 10-K (tests/fixtures). For any
company, live (needs your contact for SEC):

    LILAVATI_SEC_USER_AGENT="Your Name you@example.org" uv run python examples/05_deep_research_agent.py --live MSFT
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import httpx
from rich.console import Console
from rich.table import Table

from lilavati.agents.research import FinancialResearchAgent
from lilavati.agents.search import FinancialSearchAgent
from lilavati.connectors.edgar import EdgarClient

console = Console()
FIX = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def offline_agent() -> FinancialResearchAgent:
    """The agent reading Apple's FY2026 10-K from the verbatim fixtures instead of SEC."""
    subs = json.loads((FIX / "aapl_submissions_subset.json").read_text())
    facts = json.loads((FIX / "aapl_companyfacts_research_fy2026.json").read_text())

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/submissions/CIK0000320193.json"):
            return httpx.Response(200, json=subs)
        if request.url.path.endswith("/companyfacts/CIK0000320193.json"):
            return httpx.Response(200, json=facts)
        return httpx.Response(404)

    client = EdgarClient(user_agent="offline fixture", transport=httpx.MockTransport(handler))
    return FinancialResearchAgent(search_agent=FinancialSearchAgent(edgar_client=client))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--live", metavar="TICKER", help="fetch from SEC (needs LILAVATI_SEC_USER_AGENT)")
    parser.add_argument("--as-of", type=date.fromisoformat, default=None, help="as-of date (default: today)")
    args = parser.parse_args()

    if args.live:
        agent, symbol, as_of = FinancialResearchAgent(), args.live.upper(), args.as_of or date.today()
    else:
        agent, symbol, as_of = offline_agent(), "AAPL", args.as_of or date(2026, 11, 3)
    try:
        d = agent.conduct_deep_research(symbol=symbol, as_of_date=as_of)
    except ValueError as err:  # SEC unreachable, no filing by the date, or an input not reported
        console.print(f"[red]No dossier:[/red] {err}")
        raise SystemExit(2) from None

    table = Table(title=f"{d.company_name} ({d.symbol}), as of {d.as_of_date}", show_header=True)
    table.add_column("Item", style="cyan")
    table.add_column("Value", justify="right", style="bold")
    table.add_column("Basis", style="dim")
    table.add_row("Filing", f"{d.filing.form} {d.filing.accession}", f"filed {d.filing.filing_date}")
    table.add_row("Revenue (USD m)", f"{d.inputs_usd_millions['revenue']:,.0f}",
                  f"prior year {d.inputs_usd_millions['revenue_prior']:,.0f}")
    table.add_row("Beneish M-score", f"{d.forensic_accounting_summary['beneish_m_score']:.2f}",
                  "above -1.78 flags possible manipulation")
    table.add_row("Altman Z-score", f"{d.forensic_accounting_summary['altman_z_score']:.2f}",
                  d.forensic_accounting_summary["altman_zone"])
    for c in [*d.statement_checks, *d.committee_memo.checks]:
        table.add_row(c.name, "holds" if c.holds else f"FAILS by {c.difference:,.0f}", "on reported figures")
    table.add_row("Citations resolved", f"{d.citations_count}" if d.citations_verified else "NO",
                  "against the SEC data read")
    table.add_row("Committee (rule-based)", d.recommendation, "Beneish, Altman, identities, growth target")
    table.add_row("Carbon intensity", "not computed" if d.climate_risk_summary is None
                  else f"{d.climate_risk_summary['waci']:.1f} tCO2e/$M", "needs emissions and their source")
    console.print(table)

    scenarios = Table(title="Scenario tree (assumed multipliers; graph calibrated from the filing)")
    for col in ("Scenario", "Probability", "Revenue (USD m)", "Net income (USD m)", "Ending cash (USD m)", "Balances"):
        scenarios.add_column(col, justify="right" if col != "Scenario" else "left")
    for b in d.scenario_analysis.scenario_branches:
        scenarios.add_row(b.branch_name, f"{b.probability_weight:.0%}", f"{b.projected_revenue:,.0f}",
                          f"{b.projected_net_income:,.0f}", f"{b.projected_ending_cash:,.0f}",
                          "yes" if b.smt_invariant_verified else "NO")
    console.print(scenarios)
    console.print("[dim]The scenario graph opens at the filing's balance sheet and rolls every line forward "
                  "(no plug), so its balance check tests the roll-forward, not the scenario multipliers "
                  "(statement graph not yet checked against a reference).[/dim]")

    console.print(f"\n[bold]Thesis:[/bold] {d.executive_thesis}\n")
    console.print("[bold]Inputs not taken from the filing:[/bold]")
    for item in d.assumed_inputs:
        console.print(f"  - {item}")


if __name__ == "__main__":
    main()
