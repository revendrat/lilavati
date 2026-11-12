"""
Ready-to-Use Financial Verification Gates for Agentic Graphs.

Developers can insert these nodes into a FinancialStateGraph to enforce
formal SMT equilibrium, credit covenant limits, cryptographic provenance, and temporal purity.
"""

from __future__ import annotations

from lilavati.core.invariants import SuvarnaEngine
from lilavati.framework.state import FinancialState
from lilavati.prompts.reflection import generate_smt_reflection_prompt


class SMTBalanceGate:
    """Formal Z3 SMT gate verifying that Assets == Liabilities + Equity."""

    def __init__(self, tolerance: float = 1e-4) -> None:
        self.tolerance = tolerance

    def __call__(self, state: FinancialState) -> FinancialState:
        facts = state.extracted_facts
        req_keys = ("total_assets", "total_liabilities", "total_equity")
        if not all(k in facts for k in req_keys):
            return state

        res = SuvarnaEngine.verify_balance_sheet_equation(
            total_assets=float(facts["total_assets"]),
            total_liabilities=float(facts["total_liabilities"]),
            shareholders_equity=float(facts["total_equity"]),
            tolerance=self.tolerance,
        )

        if not res.is_valid:
            state.is_valid = False
            for v in res.violations:
                state.fail_gate(v)

            # Auto-inject SMT reflection prompt into conversation history
            reflection = generate_smt_reflection_prompt(
                invariant_name="Assets = Liabilities + Equity",
                violations=res.violations,
                current_values={k: facts[k] for k in req_keys},
            )
            state.add_message(role="user", content=reflection)

        return state


class CovenantGate:
    """Formal Z3 SMT gate verifying debt leverage and interest coverage covenants."""

    def __init__(
        self,
        max_leverage: float = 3.5,
        min_interest_coverage: float = 3.0,
    ) -> None:
        self.max_leverage = max_leverage
        self.min_interest_coverage = min_interest_coverage

    def __call__(self, state: FinancialState) -> FinancialState:
        facts = state.extracted_facts
        if not all(k in facts for k in ("total_debt", "cash", "ebitda")):
            return state

        res = SuvarnaEngine.verify_debt_covenant(
            total_debt=float(facts["total_debt"]),
            cash=float(facts["cash"]),
            ebitda=float(facts["ebitda"]),
            max_leverage_covenant=self.max_leverage,
            min_interest_coverage_covenant=self.min_interest_coverage,
            interest_expense=float(facts.get("interest_expense", 0.0)),
        )

        if not res.is_valid:
            state.is_valid = False
            for v in res.violations:
                state.fail_gate(v)

        return state


class ProvenanceGate:
    """Verifies that all extracted financial claims carry valid 64-character SHA-256 hashes."""

    def __call__(self, state: FinancialState) -> FinancialState:
        for val in state.sourced_values:
            cit = val.citation
            if len(cit.doc_hash) != 64 or cit.page < 1 or not cit.raw_snippet.strip():
                state.fail_gate(
                    f"Provenance failure on claim '{val.value}': invalid citation hash or missing page."
                )

        return state


class TemporalPurityGate:
    """Verifies that no cited observations violate the point-in-time boundary (no look-ahead)."""

    def __call__(self, state: FinancialState) -> FinancialState:
        if state.as_of_date is None:
            return state

        cutoff = state.as_of_date
        for cit in state.citations:
            if cit.filing_date > cutoff:
                state.fail_gate(
                    f"Temporal purity breach: Citation date {cit.filing_date} is after as_of_date {cutoff}."
                )

        return state
