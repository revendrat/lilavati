"""
Tutorial: How to Build, Test, and Serve an Audited Financial Agent with Project Līlāvatī.

This tutorial guides you step-by-step through:
1. Defining a typed state container (`FinancialState`).
2. Writing deterministic execution nodes and attaching Z3 SMT formal verification gates.
3. Assembling the DAG state machine using `FinancialStateGraph`.
4. Executing and testing the agent with automated invariant verification.
5. Converting the agent into a production-grade FastAPI REST microservice with OpenAPI docs.
"""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lilavati.core.fixed_income import FixedIncomeEngine
from lilavati.core.invariants import SuvarnaEngine
from lilavati.core.provenance import CitationRef
from lilavati.framework import (
    END,
    FinancialState,
    FinancialStateGraph,
    create_agent_api,
)

console = Console()


# ==============================================================================
# STEP 1: Define Typed State Container
# ==============================================================================
class CreditUnderwritingState(FinancialState):
    """
    Typed state container passed between graph execution nodes.
    Inherits from FinancialState to support messages, citations, facts, and gates.
    """

    borrower_name: str = "Apollo Industrial Corp"
    fiscal_year: int = 2026
    ebitda: float = 80.0  # $M
    total_debt: float = 280.0  # $M
    interest_expense: float = 18.0  # $M
    equity_value: float = 400.0  # $M
    equity_volatility: float = 0.30  # 30% annualized vol

    # Statutory Covenants
    max_leverage_covenant: float = 4.00  # Max Debt / EBITDA <= 4.0x
    min_coverage_covenant: float = 3.50  # Min EBITDA / Interest >= 3.5x

    # Output Diagnostics
    leverage_ratio: float = 0.0
    interest_coverage: float = 0.0
    covenant_satisfied: bool = False
    merton_default_probability: float = 0.0
    required_equity_cure_usd: float = 0.0
    underwriting_verdict: str = "PENDING"


# ==============================================================================
# STEP 2: Implement Execution Nodes with Formal Math & Invariants
# ==============================================================================
def ingest_and_provenance_node(state: CreditUnderwritingState) -> CreditUnderwritingState:
    """Node 1: Grounds extracted borrower disclosures with cryptographic SHA-256 provenance."""
    # Simulated statutory loan credit agreement / 10-K SHA-256 hash
    doc_hash = "a7c8e9b01234567890abcdef1234567890abcdef1234567890abcdef12345678"

    # Record immutable citations
    state.record_citation(
        CitationRef(
            doc_hash=doc_hash,
            filing_type="Credit-Agreement",
            filing_date=date(2026, 3, 15),
            period_end=date(2025, 12, 31),
            page=24,
            raw_snippet=f"Adjusted Consolidated EBITDA: ${state.ebitda:.1f}M",
        )
    )
    state.record_citation(
        CitationRef(
            doc_hash=doc_hash,
            filing_type="Credit-Agreement",
            filing_date=date(2026, 3, 15),
            period_end=date(2025, 12, 31),
            page=28,
            raw_snippet=f"Total Outstanding Indebtedness: ${state.total_debt:.1f}M",
        )
    )
    state.record_fact("ebitda", state.ebitda)
    state.record_fact("total_debt", state.total_debt)
    return state


def covenant_audit_node(state: CreditUnderwritingState) -> CreditUnderwritingState:
    """Node 2: Deterministically evaluates debt covenants and verifies via Z3 SMT solver."""
    state.leverage_ratio = state.total_debt / state.ebitda
    state.interest_coverage = state.ebitda / state.interest_expense

    # Use Suvarna Z3 SMT engine to formally verify debt covenant satisfiability
    suvarna = SuvarnaEngine()
    cov_result = suvarna.verify_debt_covenant(
        total_debt=state.total_debt,
        cash=0.0,
        ebitda=state.ebitda,
        max_leverage_covenant=state.max_leverage_covenant,
        min_interest_coverage_covenant=state.min_coverage_covenant,
        interest_expense=state.interest_expense,
    )

    state.covenant_satisfied = cov_result.is_valid

    # If in breach, calculate exact required sponsor equity cure
    if not cov_result.is_valid:
        max_allowable_debt = state.max_leverage_covenant * state.ebitda
        state.required_equity_cure_usd = state.total_debt - max_allowable_debt
    else:
        state.required_equity_cure_usd = 0.0

    return state


def structural_credit_risk_node(state: CreditUnderwritingState) -> CreditUnderwritingState:
    """Node 3: Calculates Merton structural default probability using quantitative options pricing."""
    risk_free_rate = 0.045  # 4.5% Treasury yield
    time_horizon = 1.0  # 1 year

    # Solve Merton structural model
    merton_res = FixedIncomeEngine.solve_merton_model(
        equity_value=state.equity_value,
        equity_volatility=state.equity_volatility,
        debt_face_value=state.total_debt,
        risk_free_rate=risk_free_rate,
        maturity_years=time_horizon,
    )

    state.merton_default_probability = merton_res.default_probability

    # Synthesize underwriting decision
    if state.covenant_satisfied and state.merton_default_probability < 0.05:
        state.underwriting_verdict = "APPROVED: Robust solvency & covenants verified."
    elif not state.covenant_satisfied:
        state.underwriting_verdict = (
            f"REJECTED_COVENANT_BREACH: Leverage ({state.leverage_ratio:.2f}x) exceeds limit "
            f"({state.max_leverage_covenant:.2f}x). Requires ${state.required_equity_cure_usd:.1f}M equity cure."
        )
    else:
        state.underwriting_verdict = "FLAGGED_FOR_REVIEW: Elevating credit risk."

    return state


# ==============================================================================
# STEP 3: Assemble & Compile Graph
# ==============================================================================
def build_underwriting_agent() -> FinancialStateGraph[CreditUnderwritingState]:
    """Constructs and compiles the FinancialStateGraph."""
    builder = FinancialStateGraph(CreditUnderwritingState)

    builder.add_node("ingest", ingest_and_provenance_node)
    builder.add_node("covenant_audit", covenant_audit_node)
    builder.add_node("credit_risk", structural_credit_risk_node)

    builder.set_entry_point("ingest")
    builder.add_edge("ingest", "covenant_audit")
    builder.add_edge("covenant_audit", "credit_risk")
    builder.add_edge("credit_risk", END)

    return builder


# ==============================================================================
# STEP 4: Local Execution & Testing
# ==============================================================================
def run_tutorial() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Tutorial: Building Custom Audited Financial Agents[/bold cyan]\n"
            "[white]Learn how to compose, test, and serve production agents with Project Līlāvatī.[/white]",
            title="Project Līlāvatī Developer Guide",
        )
    )

    # 1. Compile Agent Graph
    console.print("\n[yellow]1. Compiling FinancialStateGraph...[/yellow]")
    agent_graph = build_underwriting_agent().compile()
    console.print(
        "  [green]✓ Graph compiled successfully with 3 nodes and SMT invariant gates.[/green]"
    )

    # 2. Execute Locally with Compliant Borrower
    console.print("\n[yellow]2. Executing Agent Locally (Borrower A: Compliant)...[/yellow]")
    borrower_a = CreditUnderwritingState(
        borrower_name="Apex Logistics Inc",
        ebitda=100.0,
        total_debt=320.0,  # 3.20x leverage <= 4.0x
        interest_expense=15.0,
        equity_value=600.0,
    )
    result_a = agent_graph.invoke(borrower_a)

    console.print(f"  [green]✓ Leverage Ratio:[/green] {result_a.leverage_ratio:.2f}x")
    console.print(f"  [green]✓ Covenant Satisfied:[/green] {result_a.covenant_satisfied}")
    console.print(
        f"  [green]✓ Merton Default Prob:[/green] {result_a.merton_default_probability:.2%}"
    )
    console.print(f"  [bold green]✓ Decision:[/bold green] {result_a.underwriting_verdict}")

    # 3. Execute Locally with Distressed Borrower (Covenant Breach)
    console.print("\n[yellow]3. Executing Agent Locally (Borrower B: Distressed)...[/yellow]")
    borrower_b = CreditUnderwritingState(
        borrower_name="Stressed Retail Corp",
        ebitda=50.0,
        total_debt=275.0,  # 5.50x leverage > 4.0x
        interest_expense=18.0,
        equity_value=120.0,
    )
    result_b = agent_graph.invoke(borrower_b)

    console.print(f"  [red]✗ Leverage Ratio:[/red] {result_b.leverage_ratio:.2f}x (Max: 4.00x)")
    console.print(f"  [red]✗ Required Equity Cure:[/red] ${result_b.required_equity_cure_usd:.1f}M")
    console.print(f"  [bold red]✗ Decision:[/bold red] {result_b.underwriting_verdict}")

    # ==========================================================================
    # STEP 5: Convert into a Production REST API with One Line of Code
    # ==========================================================================
    console.print("\n[yellow]4. Converting Compiled Graph into a Production REST API...[/yellow]")
    app = create_agent_api(
        graph=agent_graph,
        title="Institutional Credit Underwriting API",
        description="Automated credit covenant and structural distress underwriting service.",
        version="1.0.0",
    )
    console.print(
        "  [green]✓ FastAPI ASGI application generated automatically with OpenAPI docs.[/green]"
    )

    # Test the API using FastAPI TestClient
    client = TestClient(app)
    resp = client.post(
        "/api/v1/run",
        json={
            "borrower_name": "API Commercial Client",
            "ebitda": 120.0,
            "total_debt": 360.0,
            "interest_expense": 20.0,
            "equity_value": 750.0,
        },
    )

    assert resp.status_code == 200
    api_result = resp.json()
    console.print(
        f"  [green]✓ API HTTP 200 Response:[/green] Leverage: {api_result['leverage_ratio']:.2f}x | "
        f"Verdict: '{api_result['underwriting_verdict']}'"
    )

    # Render Summary Table
    table = Table(title="Agent Execution Summary", show_header=True, header_style="bold cyan")
    table.add_column("Borrower", style="white")
    table.add_column("Leverage", justify="right")
    table.add_column("Covenant Status", justify="center")
    table.add_column("Merton Default Prob", justify="right")
    table.add_column("Underwriting Verdict", style="green")

    table.add_row(
        result_a.borrower_name,
        f"{result_a.leverage_ratio:.2f}x",
        "[green]SAT (Passed)[/green]",
        f"{result_a.merton_default_probability:.2%}",
        result_a.underwriting_verdict,
    )
    table.add_row(
        result_b.borrower_name,
        f"{result_b.leverage_ratio:.2f}x",
        "[red]UNSAT (Breached)[/red]",
        f"{result_b.merton_default_probability:.2%}",
        result_b.underwriting_verdict,
    )
    console.print("\n", table)

    console.print(
        Panel(
            "[bold white]To run this API as a live web server in production:[/bold white]\n\n"
            "[green]from lilavati.framework import serve_agent[/green]\n"
            "[green]serve_agent(agent_graph, host='0.0.0.0', port=8000)[/green]\n\n"
            "[cyan]Interactive Swagger documentation will be available at: http://localhost:8000/docs[/cyan]",
            title="Production Deployment",
        )
    )


if __name__ == "__main__":
    run_tutorial()
