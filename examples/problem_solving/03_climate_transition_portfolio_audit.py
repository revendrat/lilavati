"""
Problem 03: Sustainability-Linked Bond (SLB) Covenant & Carbon Transition Risk Audit.

Real-World Institutional Problem:
An institutional fixed income asset manager holds a $250M position in a Sustainability-Linked Bond (SLB)
issued by 'Nordic Industrials ASA'.
Under ICMA principles, the bond has a binding Sustainability Performance Target (SPT):
- Mandatory 30% reduction in Scope 1+2 emissions from baseline (200,000 tCO2e down to 140,000 tCO2e).
- Penalty coupon step-up of +25 bps if the SPT is missed.
Concurrently, the fund needs to stress-test the issuer under a $125/tCO2e shadow carbon price shock.

Agent Pipeline Built with Project Līlāvatī:
1. Ingests third-party verified emissions inventory from statutory reports with SHA-256 provenance.
2. Evaluates SLB covenant target achievement and computes active coupon and penalty cash outflows.
3. Stress-tests corporate operating margin (EBIT) and debt coverage under carbon tax scenarios.
4. Generates an audited TCFD-compliant Climate Risk Memorandum for the Investment Committee.
"""

from __future__ import annotations

from datetime import date

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lilavati.core.provenance import CitationRef, SourcedValue
from lilavati.core.sustainability import SustainabilityEngine
from lilavati.framework import (
    END,
    FinancialState,
    FinancialStateGraph,
)
from lilavati.schemas.sustainability import SustainabilityLinkedBond

console = Console()


class ClimateAuditState(FinancialState):
    issuer_name: str = "Nordic Industrials ASA"
    bond_notional: float = 250000000.0  # $250M
    base_coupon_pct: float = 4.00
    active_coupon_pct: float = 4.00
    annual_penalty_outflow: float = 0.0
    spt_achieved: bool = False
    ebit_margin_before_pct: float = 0.0
    ebit_margin_after_pct: float = 0.0
    interest_coverage_after_carbon_tax: float = 0.0
    is_covenant_at_risk: bool = False
    committee_action: str = "PENDING"


def main() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Problem 03: SLB Covenant & Carbon Transition Risk Agent[/bold cyan]\n"
            "Evaluating Sustainability Performance Targets, step-up penalties, and shadow carbon tax shocks.",
            title="Project Līlāvatī Institutional Solutions",
        )
    )

    builder = FinancialStateGraph(ClimateAuditState)

    # --- Node 1: Ingest Statutory Carbon Disclosures ---
    def ingest_carbon_data(state: ClimateAuditState) -> ClimateAuditState:
        cit = CitationRef(
            doc_hash="b" * 64,
            filing_type="Sustainability-Report",
            filing_date=date(2024, 4, 15),
            period_end=date(2023, 12, 31),
            page=18,
            raw_snippet="Nordic Industrials Scope 1: 110,000 tCO2e, Scope 2: 55,000 tCO2e, Revenue: $1,200M",
        )
        state.record_citation(cit)
        state.sourced_values.append(SourcedValue(value=165000.0, citation=cit))

        # Baseline was 200,000 tCO2e. Target was 30% reduction (140,000 tCO2e).
        # Actual emissions reported: 110,000 + 55,000 = 165,000 tCO2e (only 17.5% reduction!)
        state.record_fact("baseline_emissions", 200000.0)
        state.record_fact("reported_emissions", 165000.0)
        state.record_fact("scope1", 110000.0)
        state.record_fact("scope2", 55000.0)
        state.record_fact("revenue_mil", 1200.0)
        state.record_fact("ebit_mil", 180.0)
        state.record_fact("interest_expense_mil", 35.0)

        return state

    # --- Node 2: SLB Covenant Evaluation ---
    def evaluate_slb_node(state: ClimateAuditState) -> ClimateAuditState:
        facts = state.extracted_facts
        bond = SustainabilityLinkedBond(
            isin="XS9988112233",
            notional=state.bond_notional,
            base_coupon_rate=state.base_coupon_pct / 100.0,
            target_reduction_pct=0.30,  # 30% target
            baseline_emissions=float(facts["baseline_emissions"]),
            step_up_bps=25.0,  # +25 bps penalty
            target_year=2024,
        )

        covenant_res = SustainabilityEngine.evaluate_slb_covenant(
            bond=bond,
            reported_emissions=float(facts["reported_emissions"]),
        )

        state.spt_achieved = covenant_res.spt_achieved
        state.active_coupon_pct = covenant_res.active_coupon_rate * 100.0
        state.annual_penalty_outflow = covenant_res.annual_interest_penalty

        return state

    # --- Node 3: Shadow Carbon Tax Stress Testing ---
    def carbon_tax_stress_node(state: ClimateAuditState) -> ClimateAuditState:
        facts = state.extracted_facts

        # Stress test $125 / tCO2e shadow carbon tax
        # $125 / ton in $M units is 0.000125 ($M per ton)
        stress_res = SustainabilityEngine.stress_test_carbon_tax(
            revenue=float(facts["revenue_mil"]),
            ebit=float(facts["ebit_mil"]),
            interest_expense=float(facts["interest_expense_mil"]),
            scope1_emissions=float(facts["scope1"]),
            scope2_emissions=float(facts["scope2"]),
            carbon_price_per_ton=0.000125,
            pass_through_rate=0.30,  # Only 30% pass-through ability
            covenant_interest_floor=3.0,
        )

        state.ebit_margin_before_pct = stress_res.ebit_margin_before_pct * 100.0
        state.ebit_margin_after_pct = stress_res.ebit_margin_after_pct * 100.0
        state.interest_coverage_after_carbon_tax = stress_res.interest_coverage_after
        state.is_covenant_at_risk = stress_res.is_covenant_at_risk

        if not state.spt_achieved:
            state.committee_action = (
                f"STEP-UP ACTIVE: Coupon increases from {state.base_coupon_pct:.2f}% to {state.active_coupon_pct:.2f}%. "
                f"Issuer faces +${state.annual_penalty_outflow:,.0f}/yr penalty cash outflow. "
                f"Under $125/ton carbon tax, interest coverage deteriorates to {state.interest_coverage_after_carbon_tax:.2f}x. "
                "RECOMMENDATION: Demand enhanced transition capex disclosures or hedge credit duration."
            )

        return state

    builder.add_node("ingest", ingest_carbon_data)
    builder.add_node("slb_covenant", evaluate_slb_node)
    builder.add_node("carbon_tax_stress", carbon_tax_stress_node)

    builder.add_edge("ingest", "slb_covenant")
    builder.add_edge("slb_covenant", "carbon_tax_stress")
    builder.add_edge("carbon_tax_stress", END)
    builder.set_entry_point("ingest")

    app = builder.compile()
    final_state = app.invoke(ClimateAuditState())

    # Output Results
    table = Table(
        title=f"Climate & SLB Audit Memorandum: {final_state.issuer_name}", show_header=True
    )
    table.add_column("Audit Parameter", style="cyan")
    table.add_column("Evaluated Metric", justify="right", style="bold")
    table.add_column("Regulatory Target", justify="right", style="dim")
    table.add_column("Status", justify="center")

    table.add_row(
        "Sustainability Performance Target (SPT)",
        "-17.5% reduction",
        "-30.0% reduction",
        "[bold red]MISSED TARGET[/bold red]",
    )
    table.add_row(
        "Active SLB Coupon Rate",
        f"{final_state.active_coupon_pct:.2f}%",
        f"{final_state.base_coupon_pct:.2f}% base",
        "[bold red]+25 BPS STEP-UP[/bold red]",
    )
    table.add_row(
        "Annual Interest Penalty Outflow",
        f"${final_state.annual_penalty_outflow:,.0f}",
        "$0",
        "[bold red]CASH OUTFLOW DRAG[/bold red]",
    )
    table.add_row(
        "Operating Margin under $125/t Carbon Tax",
        f"{final_state.ebit_margin_after_pct:.1f}%",
        f"{final_state.ebit_margin_before_pct:.1f}% base",
        "[bold yellow]120 BPS CONTRACTION[/bold yellow]",
    )
    table.add_row(
        "Post-Carbon Tax Interest Coverage",
        f"{final_state.interest_coverage_after_carbon_tax:.2f}x",
        "≥ 3.00x floor",
        "[bold green]COMPLIANT (SAFE)[/bold green]"
        if not final_state.is_covenant_at_risk
        else "[bold red]BREACH[/bold red]",
    )

    console.print(table)
    console.print(
        f"\n[bold yellow]Portfolio Action Notice:[/bold yellow]\n{final_state.committee_action}"
    )


if __name__ == "__main__":
    main()
