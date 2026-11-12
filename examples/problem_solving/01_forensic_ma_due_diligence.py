"""
Problem 01: Forensic M&A Due Diligence & Accounting Manipulation Detection.

Real-World Institutional Problem:
A private equity / corporate M&A team is evaluating an acquisition of 'Apex Cloud Inc.'
The target claims 35% top-line growth and seeks a $3.0B acquisition price.
However, management has been aggressively pulling forward revenues through unbilled receivables (channel stuffing).

Agent Pipeline Built with Project Līlāvatī:
1. Extracts financial statements across periods (t and t-1).
2. Computes the 8-variable Beneish M-Score and Altman Z-Score deterministically.
3. Formally proves balance sheet equilibrium using SuvarnaEngine (Z3 SMT solver).
4. Issues a binding, audited Investment Committee Due Diligence Memorandum.
"""

from __future__ import annotations

from datetime import date

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lilavati.agents.forensics import ForensicEngine
from lilavati.core.provenance import CitationRef, SourcedValue
from lilavati.framework import (
    END,
    FinancialState,
    FinancialStateGraph,
    SMTBalanceGate,
)

console = Console()


# 1. Define Pipeline State for M&A Due Diligence
class MADueDiligenceState(FinancialState):
    target_company: str = "Apex Cloud Inc."
    acquisition_valuation_ask: float = 3000.0  # $M
    beneish_m_score: float | None = None
    altman_z_score: float | None = None
    is_manipulator: bool = False
    is_distressed: bool = False
    recommendation: str = "PENDING"
    risk_factors: list[str] = []


def main() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Problem 01: Forensic M&A Due Diligence Agent[/bold cyan]\n"
            "Uncovering accounting manipulation, channel stuffing, and insolvency risk before acquisition.",
            title="Project Līlāvatī Institutional Solutions",
        )
    )

    # 2. Build the Agentic Graph
    graph_builder = FinancialStateGraph(MADueDiligenceState)

    # --- Node 1: Ingestion & Provenance Recording ---
    def ingest_filings_node(state: MADueDiligenceState) -> MADueDiligenceState:
        # Ground-truth financial disclosures with SHA-256 statutory provenance
        statutory_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        cit = CitationRef(
            doc_hash=statutory_hash,
            filing_type="10-K",
            filing_date=date(2024, 2, 28),
            period_end=date(2023, 12, 31),
            page=48,
            raw_snippet="Total Assets: $850.0M, Accounts Receivable: $280.0M, Revenue: $500.0M",
        )
        state.record_citation(cit)
        state.sourced_values.append(SourcedValue(value=850.0, citation=cit))

        # Store financial facts for period t (Current) and period t-1 (Prior)
        state.record_fact("total_assets", 850.0)
        state.record_fact("total_liabilities", 500.0)
        state.record_fact("total_equity", 350.0)
        state.record_fact("revenue", 500.0)
        state.record_fact(
            "receivables", 280.0
        )  # Aggressive surge: 56% of revenue in uncollected receivables!

        state.add_message(
            "user", "Audit target financials for earnings manipulation and revenue quality."
        )
        return state

    # --- Node 2: Deterministic Forensic Calculation Agent ---
    def forensic_audit_node(state: MADueDiligenceState) -> MADueDiligenceState:
        # Calculate full 8-variable Beneish M-Score using primary financials:
        # Notice severe receivables jump: $140M -> $280M (+100%) vs Sales $370M -> $500M (+35%)
        # And divergence between Net Income ($65M) and CFO ($15M)
        m_res = ForensicEngine.calculate_beneish_m_score(
            revenue_t=500.0,
            revenue_t_minus_1=370.0,
            cogs_t=250.0,
            cogs_t_minus_1=170.0,
            receivables_t=280.0,
            receivables_t_minus_1=140.0,
            current_assets_t=450.0,
            current_assets_t_minus_1=310.0,
            ppe_t=300.0,
            ppe_t_minus_1=280.0,
            total_assets_t=850.0,
            total_assets_t_minus_1=650.0,
            depreciation_t=30.0,
            depreciation_t_minus_1=25.0,
            sga_t=120.0,
            sga_t_minus_1=85.0,
            long_term_debt_t=350.0,
            long_term_debt_t_minus_1=250.0,
            current_liabilities_t=150.0,
            current_liabilities_t_minus_1=110.0,
            net_income_t=65.0,
            cfo_t=15.0,
        )

        # Run Altman Z-Score
        z_res = ForensicEngine.calculate_altman_z_score(
            working_capital=300.0,
            total_assets=850.0,
            retained_earnings=90.0,
            ebit=90.0,
            market_value_equity=1200.0,
            total_liabilities=500.0,
            sales=500.0,
        )

        state.beneish_m_score = m_res.m_score
        state.altman_z_score = z_res.z_score
        state.is_manipulator = m_res.is_likely_manipulator
        state.is_distressed = z_res.distress_zone == "Distress"

        if m_res.is_likely_manipulator:
            state.risk_factors.append(
                f"Beneish M-Score ({m_res.m_score:.2f}) > -1.78: Severe earnings manipulation warning."
            )
            state.risk_factors.append(
                f"Days Sales in Receivables Index (DSRI = {m_res.dsri:.2f}): Receivables expanded 48% faster than sales."
            )
            state.risk_factors.append(
                f"High Accruals (TATA = {m_res.tata:.3f}): Operating income unbacked by actual cash collections."
            )

        return state

    # --- Node 3: Formal SMT Balance Gate ---
    smt_gate = SMTBalanceGate()

    # --- Node 4: M&A Investment Decision Node ---
    def decision_node(state: MADueDiligenceState) -> MADueDiligenceState:
        if state.is_manipulator or state.is_distressed or not state.is_valid:
            state.recommendation = "REJECT ACQUISITION (EARNINGS MANIPULATION & ACCRUAL ANOMALY)"
        else:
            state.recommendation = "APPROVE DUE DILIGENCE"
        return state

    # 3. Assemble Graph Topology
    graph_builder.add_node("ingest", ingest_filings_node)
    graph_builder.add_node("forensics", forensic_audit_node)
    graph_builder.add_node("verify_smt", smt_gate)
    graph_builder.add_node("decision", decision_node)

    graph_builder.add_edge("ingest", "forensics")
    graph_builder.add_edge("forensics", "verify_smt")
    graph_builder.add_edge("verify_smt", "decision")
    graph_builder.add_edge("decision", END)
    graph_builder.set_entry_point("ingest")

    # 4. Compile and Run Agentic Pipeline
    app = graph_builder.compile()
    final_state = app.invoke(MADueDiligenceState())

    # 5. Display Institutional Output
    table = Table(title=f"M&A Forensic Audit Memo: {final_state.target_company}", show_header=True)
    table.add_column("Metric / Check", style="cyan")
    table.add_column("Calculated Value", justify="right", style="bold")
    table.add_column("Threshold / Norm", justify="right", style="dim")
    table.add_column("Evaluation", justify="center")

    table.add_row(
        "Beneish M-Score",
        f"{final_state.beneish_m_score:.2f}",
        "< -1.78",
        "[bold red]MANIPULATOR[/bold red]"
        if final_state.is_manipulator
        else "[green]NORMAL[/green]",
    )
    table.add_row(
        "Altman Z-Score",
        f"{final_state.altman_z_score:.2f}",
        "> 2.99",
        "[bold yellow]GREY / MODERATE[/bold yellow]",
    )
    table.add_row(
        "Z3 SMT Balance Proof",
        "Assets == L + E",
        "Tol: 1e-4",
        "[bold green]SAT (PASSED)[/bold green]"
        if final_state.is_valid
        else "[bold red]UNSAT[/bold red]",
    )
    table.add_row(
        "Final Recommendation",
        f"[bold red]{final_state.recommendation}[/bold red]",
        "Target $3.0B",
        "[bold red]BLOCKED[/bold red]",
    )

    console.print(table)

    console.print("\n[bold red]Primary Forensic Risk Flags Identified by Agent:[/bold red]")
    for r in final_state.risk_factors:
        console.print(f"  • {r}")


if __name__ == "__main__":
    main()
