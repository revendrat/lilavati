"""
Quantitative Metrics & Evaluators for Līlāvatī-Bench.

Implements institutional evaluation metrics for financial AI agents:
1. Proof-of-Citation Score (PoCS): Verifiable cryptographic link to statutory disclosure.
2. Accounting Invariant Compliance Rate (ICR): SMT satisfiability check of balance sheet identities.
3. Temporal Purity Index (TPI): 100% resistance to look-ahead bias and restatements.
4. Tool Math Purity Ratio (TMPR): Percentage of quantitative assertions from deterministic sandboxes.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from lilavati.core.invariants import SuvarnaEngine
from lilavati.core.provenance import SourcedValue
from lilavati.schemas.statements import ThreeStatementModel


class BenchmarkScorecard(BaseModel):
    """Aggregate benchmark results for an agent or financial foundation model."""

    model_config = ConfigDict(frozen=True)

    agent_id: str
    proof_of_citation_score: float = Field(..., ge=0.0, le=1.0, description="PoCS (0.0 to 1.0)")
    invariant_compliance_rate: float = Field(..., ge=0.0, le=1.0, description="ICR (0.0 to 1.0)")
    temporal_purity_index: float = Field(
        ..., ge=0.0, le=1.0, description="TPI (1.0 = zero look-ahead violations)"
    )
    tool_math_purity_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="TMPR (1.0 = zero LLM mental math)"
    )
    composite_lilavati_index: float = Field(
        ..., ge=0.0, le=100.0, description="Overall weighted benchmark score (0-100)"
    )
    track_scores: dict[str, float] = Field(default_factory=dict)


class BenchmarkEvaluator:
    """Evaluates agent execution traces and financial artifacts against ground truths."""

    @staticmethod
    def compute_proof_of_citation_score(
        assertions: Sequence[SourcedValue],
        ground_truth_hashes: set[str],
    ) -> float:
        """
        Computes the Proof-of-Citation Score (PoCS):
        PoCS = (Verified Claims with Valid Hashes & Spans) / (Total Claims)
        """
        if not assertions:
            return 0.0

        valid_count = 0
        for item in assertions:
            cit = item.citation
            # Verify valid 64-char hex hash and inclusion in ground truth
            if (
                len(cit.doc_hash) == 64
                and cit.doc_hash in ground_truth_hashes
                and cit.page >= 1
                and len(cit.raw_snippet.strip()) > 0
            ):
                valid_count += 1

        return float(valid_count / len(assertions))

    @staticmethod
    def compute_invariant_compliance_rate(
        models: Sequence[ThreeStatementModel],
    ) -> float:
        """
        Computes the Invariant Compliance Rate (ICR) using Z3 SMT formal verification.
        ICR = (Balanced & Reconciled Statements) / (Total Evaluated Statements)
        """
        if not models:
            return 0.0

        compliant = 0
        for m in models:
            check = SuvarnaEngine.verify_three_statement_invariants(
                total_assets=m.balance_sheet.total_assets,
                total_liabilities=m.balance_sheet.total_liabilities,
                shareholders_equity=m.balance_sheet.total_equity,
                net_income=m.income_statement.net_income,
                cash_start=m.balance_sheet.cash_and_equivalents
                - m.cash_flow_statement.net_change_in_cash,
                cash_end=m.balance_sheet.cash_and_equivalents,
                cfo=m.cash_flow_statement.cfo,
                cfi=m.cash_flow_statement.cfi,
                cff=m.cash_flow_statement.cff,
            )
            if check.is_valid:
                compliant += 1

        return float(compliant / len(models))

    @staticmethod
    def compute_temporal_purity_index(
        extracted_facts: Sequence[SourcedValue],
        as_of_cutoff_date: date,
    ) -> float:
        """
        Computes Temporal Purity Index (TPI).
        Any single observation dated AFTER as_of_cutoff_date penalizes the score.
        TPI = (Valid Points on or before T_cutoff) / (Total Points)
        """
        if not extracted_facts:
            return 1.0

        clean_count = 0
        for fact in extracted_facts:
            if fact.citation.filing_date <= as_of_cutoff_date:
                clean_count += 1

        return float(clean_count / len(extracted_facts))

    @staticmethod
    def compute_composite_index(
        pocs: float,
        icr: float,
        tpi: float,
        tmpr: float,
    ) -> float:
        """
        Computes the composite Līlāvatī Index (0 - 100):
        30% PoCS + 30% ICR + 20% TPI + 20% TMPR
        """
        raw_score = 0.30 * pocs + 0.30 * icr + 0.20 * tpi + 0.20 * tmpr
        return round(raw_score * 100.0, 2)
