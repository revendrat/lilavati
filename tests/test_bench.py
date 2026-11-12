"""
Unit and Integration Tests for Līlāvatī-Bench.
"""

from __future__ import annotations

import json
from datetime import date
from unittest.mock import patch

import pytest

from lilavati.bench.cli import format_markdown_scorecard, main
from lilavati.bench.datasets import (
    get_cases_by_track,
    load_all_test_cases,
)
from lilavati.bench.evaluators import BenchmarkEvaluator, BenchmarkScorecard
from lilavati.bench.runner import (
    BenchmarkRunner,
    ReferenceAgentSolver,
)
from lilavati.core.provenance import CitationRef, SourcedValue
from lilavati.schemas.statements import (
    BalanceSheet,
    CashFlowStatement,
    IncomeStatement,
    ThreeStatementModel,
)


def test_evaluator_proof_of_citation_score() -> None:
    doc_hash = "a" * 64
    ground_truth = {doc_hash}

    valid_cit = CitationRef(
        doc_hash=doc_hash,
        filing_type="10-K",
        period_end=date(2024, 1, 1),
        page=12,
        raw_snippet="Revenue was $100M",
        filing_date=date(2024, 1, 1),
    )
    invalid_hash_cit = CitationRef(
        doc_hash="b" * 64,  # Not in ground truth
        filing_type="10-K",
        period_end=date(2024, 1, 1),
        page=1,
        raw_snippet="Fake snippet",
        filing_date=date(2024, 1, 1),
    )

    assertions = [
        SourcedValue(value=100.0, citation=valid_cit),
        SourcedValue(value=50.0, citation=invalid_hash_cit),
    ]

    pocs = BenchmarkEvaluator.compute_proof_of_citation_score(assertions, ground_truth)
    assert pocs == pytest.approx(0.5)

    # Empty case
    assert BenchmarkEvaluator.compute_proof_of_citation_score([], ground_truth) == 0.0


def test_evaluator_invariant_compliance_rate() -> None:
    # Balanced model
    bs_good = BalanceSheet(
        cash_and_equivalents=100.0,
        net_ppe=400.0,
        total_assets=500.0,
        total_debt=100.0,
        total_liabilities=300.0,
        retained_earnings=100.0,
        common_equity=100.0,
        total_equity=200.0,
    )
    is_good = IncomeStatement(
        revenue=1000.0,
        cogs=600.0,
        gross_profit=400.0,
        sga_expense=200.0,
        operating_income=200.0,
        net_income=150.0,
    )
    cf_good = CashFlowStatement(
        cfo=150.0,
        cfi=-100.0,
        cff=-50.0,
        net_change_in_cash=0.0,
    )
    model_good = ThreeStatementModel(
        balance_sheet=bs_good,
        income_statement=is_good,
        cash_flow_statement=cf_good,
        is_balanced=True,
        cash_reconciled=True,
    )

    # Unbalanced model (Assets != Liab + Equity)
    bs_bad = BalanceSheet(
        cash_and_equivalents=100.0,
        net_ppe=500.0,
        total_assets=600.0,  # 600 != 300 + 200
        total_debt=100.0,
        total_liabilities=300.0,
        retained_earnings=100.0,
        common_equity=100.0,
        total_equity=200.0,
    )
    model_bad = ThreeStatementModel(
        balance_sheet=bs_bad,
        income_statement=is_good,
        cash_flow_statement=cf_good,
        is_balanced=False,
        cash_reconciled=True,
    )

    icr = BenchmarkEvaluator.compute_invariant_compliance_rate([model_good, model_bad])
    assert icr == pytest.approx(0.5)
    assert BenchmarkEvaluator.compute_invariant_compliance_rate([]) == 0.0


def test_evaluator_temporal_purity_index() -> None:
    cutoff = date(2024, 6, 30)

    clean_cit = CitationRef(
        doc_hash="a" * 64,
        filing_type="10-K",
        period_end=date(2024, 5, 1),
        page=1,
        raw_snippet="Clean",
        filing_date=date(2024, 5, 1),
    )
    leak_cit = CitationRef(
        doc_hash="a" * 64,
        filing_type="10-K",
        period_end=date(2024, 7, 1),
        page=1,
        raw_snippet="Future leak",
        filing_date=date(2024, 7, 1),
    )

    facts = [
        SourcedValue(value=10.0, citation=clean_cit),
        SourcedValue(value=20.0, citation=leak_cit),
    ]

    tpi = BenchmarkEvaluator.compute_temporal_purity_index(facts, cutoff)
    assert tpi == pytest.approx(0.5)
    assert BenchmarkEvaluator.compute_temporal_purity_index([], cutoff) == 1.0


def test_evaluator_composite_index() -> None:
    score = BenchmarkEvaluator.compute_composite_index(1.0, 1.0, 1.0, 1.0)
    assert score == 100.0

    score_half = BenchmarkEvaluator.compute_composite_index(0.5, 0.5, 0.5, 0.5)
    assert score_half == 50.0


def test_golden_datasets_structure() -> None:
    cases = load_all_test_cases()
    assert len(cases) == 7

    tracks = {c.track for c in cases}
    assert len(tracks) == 7
    assert "track1_three_statement" in tracks
    assert "track2_fixed_income" in tracks
    assert "track3_econometrics" in tracks
    assert "track4_financial_ml" in tracks
    assert "track5_derivatives" in tracks
    assert "track6_microstructure" in tracks
    assert "track7_sustainability" in tracks

    t1_cases = get_cases_by_track("track1_three_statement")
    assert len(t1_cases) == 1
    assert t1_cases[0].case_id == "LILAVATI-T1-001"


def test_reference_agent_solver_and_runner() -> None:
    cases = load_all_test_cases()
    runner = BenchmarkRunner(cases=cases)
    card: BenchmarkScorecard = runner.run_suite(
        agent_id="lilavati-reference-v1",
        solver_fn=ReferenceAgentSolver.solve,
    )

    assert card.agent_id == "lilavati-reference-v1"
    assert card.proof_of_citation_score == 1.0
    assert card.invariant_compliance_rate == 1.0
    assert card.temporal_purity_index == 1.0
    assert card.tool_math_purity_ratio == 1.0
    assert card.composite_lilavati_index == 100.0

    # Ensure all 7 tracks are scored
    assert len(card.track_scores) == 7
    for trk, score in card.track_scores.items():
        assert score >= 0.8, f"Track {trk} scored lower than expected: {score}"


def test_markdown_scorecard_formatter() -> None:
    runner = BenchmarkRunner()
    card = runner.run_suite("test-agent")
    md = format_markdown_scorecard(card.model_dump())
    assert "Līlāvatī-Bench Evaluation Scorecard" in md
    assert "Proof-of-Citation Score (PoCS)" in md
    assert "Composite Līlāvatī Index" in md


def test_bench_cli_execution(capsys: pytest.CaptureFixture[str]) -> None:
    # Test JSON output
    with patch("sys.argv", ["lilavati-bench", "run", "--model", "ref-agent", "--format", "json"]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["agent_id"] == "ref-agent"
        assert data["composite_lilavati_index"] == 100.0

    # Test list-cases subcommand
    with patch("sys.argv", ["lilavati-bench", "list-cases"]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
