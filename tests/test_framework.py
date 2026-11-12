"""
Unit Tests for the Līlāvatī Developer Framework SDK.
"""

from __future__ import annotations

from datetime import date

from lilavati.core.provenance import CitationRef, SourcedValue
from lilavati.framework.agent import FinancialAgent
from lilavati.framework.gates import (
    CovenantGate,
    ProvenanceGate,
    SMTBalanceGate,
    TemporalPurityGate,
)
from lilavati.framework.graph import END, FinancialStateGraph
from lilavati.framework.state import FinancialState


def test_financial_state_lifecycle() -> None:
    state = FinancialState()
    state.add_message("user", "Analyze AAPL")
    state.record_fact("revenue", 1000.0)
    assert len(state.messages) == 1
    assert state.extracted_facts["revenue"] == 1000.0
    assert state.is_valid is True

    state.fail_gate("Contradiction detected")
    assert state.is_valid is False
    assert len(state.gate_violations) == 1


def test_financial_agent_standalone() -> None:
    def simple_ebitda(revenue: float, margin: float) -> float:
        return revenue * margin

    agent = FinancialAgent(
        name="test_analyst",
        role="Equity Analyst",
        model="mock-evaluator",
        tools=[simple_ebitda],
    )
    output = agent.run("Evaluate EBITDA on $100M rev with 20% margin")
    assert output.agent_id == "test_analyst"
    assert output.smt_invariants_verified is True


def test_financial_state_graph_execution() -> None:
    # Build a 3-node graph: extractor -> SMT gate -> router
    builder = FinancialStateGraph(FinancialState)

    def extract_node(state: FinancialState) -> FinancialState:
        # Simulate extraction of balanced numbers
        state.record_fact("total_assets", 1000.0)
        state.record_fact("total_liabilities", 600.0)
        state.record_fact("total_equity", 400.0)
        return state

    gate = SMTBalanceGate()

    builder.add_node("extract", extract_node)
    builder.add_node("verify", gate)
    builder.add_edge("extract", "verify")
    builder.add_conditional_edges(
        "verify",
        router=lambda s: "finish" if s.is_valid else "handle_error",
        path_map={"finish": END, "handle_error": END},
    )
    builder.set_entry_point("extract")

    app = builder.compile()
    initial_state = FinancialState()
    result = app.invoke(initial_state)

    assert result.is_valid is True
    assert result.extracted_facts["total_assets"] == 1000.0


def test_smt_balance_gate_failure() -> None:
    gate = SMTBalanceGate()
    state = FinancialState()
    # Unbalanced: 1000 != 600 + 300
    state.record_fact("total_assets", 1000.0)
    state.record_fact("total_liabilities", 600.0)
    state.record_fact("total_equity", 300.0)

    res = gate(state)
    assert res.is_valid is False
    assert any("Balance sheet mismatch" in v for v in res.gate_violations)
    # Ensure reflection prompt was injected
    assert len(res.messages) >= 1
    assert "CRITICAL FORMAL INVARIANT FAILURE" in res.messages[-1].content


def test_covenant_gate() -> None:
    gate = CovenantGate(max_leverage=3.0)
    state = FinancialState()
    # Net debt = 500 - 50 = 450, EBITDA = 100 -> Leverage = 4.5x > 3.0x max!
    state.record_fact("total_debt", 500.0)
    state.record_fact("cash", 50.0)
    state.record_fact("ebitda", 100.0)

    res = gate(state)
    assert res.is_valid is False
    assert any("Covenant breach" in v for v in res.gate_violations)


def test_provenance_and_temporal_gates() -> None:
    # 1. Temporal Gate
    temp_gate = TemporalPurityGate()
    state = FinancialState(as_of_date=date(2024, 6, 30))

    leak_cit = CitationRef(
        doc_hash="a" * 64,
        filing_type="10-K",
        filing_date=date(2024, 7, 1),  # Leaks after cutoff
        period_end=date(2024, 6, 30),
        page=1,
        raw_snippet="Future",
    )
    state.record_citation(leak_cit)
    res_temp = temp_gate(state)
    assert res_temp.is_valid is False
    assert any("Temporal purity breach" in v for v in res_temp.gate_violations)

    # 2. Provenance Gate
    prov_gate = ProvenanceGate()
    state_prov = FinancialState()
    bad_cit = CitationRef(
        doc_hash="c" * 64,
        filing_type="10-K",
        filing_date=date(2024, 1, 1),
        period_end=date(2024, 1, 1),
        page=1,
        raw_snippet="   ",  # Missing/empty snippet
    )
    state_prov.sourced_values.append(SourcedValue(value=100.0, citation=bad_cit))
    res_prov = prov_gate(state_prov)
    assert res_prov.is_valid is False
