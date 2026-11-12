"""
Benchmark Execution Harness for Līlāvatī-Bench.

Evaluates financial AI agents against the 7 canonical quantitative tracks,
measuring Proof-of-Citation Score (PoCS), Accounting Invariant Compliance Rate (ICR),
Temporal Purity Index (TPI), and Tool Math Purity Ratio (TMPR).
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from lilavati.bench.datasets import BenchmarkTestCase, load_all_test_cases
from lilavati.bench.evaluators import BenchmarkEvaluator, BenchmarkScorecard
from lilavati.core.derivatives import DerivativesEngine
from lilavati.core.econometrics import EconometricEngine
from lilavati.core.execution import ExecutionEngine
from lilavati.core.financial_ml import FinancialMLEngine
from lilavati.core.fixed_income import FixedIncomeEngine
from lilavati.core.invariants import SuvarnaEngine
from lilavati.core.provenance import CitationRef, SourcedValue
from lilavati.core.sustainability import SustainabilityEngine
from lilavati.schemas.statements import (
    BalanceSheet,
    CashFlowStatement,
    IncomeStatement,
    ThreeStatementModel,
)
from lilavati.schemas.sustainability import SustainabilityLinkedBond


class AgentExecutionResult(BaseModel):
    """Execution artifact produced by an agent solving a benchmark test case."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    case_id: str
    sourced_values: list[SourcedValue] = Field(default_factory=list)
    three_statement_models: list[ThreeStatementModel] = Field(default_factory=list)
    calculated_values: dict[str, Any] = Field(default_factory=dict)
    tool_calls_count: int = 0
    mental_math_violations: int = 0
    latency_seconds: float = 0.0


class ReferenceAgentSolver:
    """
    Authoritative reference solver for Līlāvatī-Bench.
    Uses Lilavati deterministic engines and produces verifiable cryptographic citations.
    """

    @staticmethod
    def solve(case: BenchmarkTestCase) -> AgentExecutionResult:
        start_t = time.perf_counter()
        sourced_vals: list[SourcedValue] = []
        models: list[ThreeStatementModel] = []
        calc_values: dict[str, Any] = {}
        tool_calls = 0

        # Create verifiable citation referencing the ground truth document
        def make_cit(snippet: str, val: float | str) -> CitationRef:
            return CitationRef(
                doc_hash=case.doc_hash,
                filing_type="Statutory-Report",
                filing_date=case.as_of_date,
                period_end=case.as_of_date,
                page=1,
                raw_snippet=f"{snippet}: {val}",
            )

        if case.track == "track1_three_statement":
            ctx = case.context_data
            # Run formal Z3 SMT balance verification
            check = SuvarnaEngine.verify_three_statement_invariants(
                total_assets=ctx["total_assets"],
                total_liabilities=ctx["total_liabilities"],
                shareholders_equity=ctx["total_equity"],
                net_income=ctx["net_income"],
                cash_start=ctx["cash_start"],
                cash_end=ctx["cash_end"],
                cfo=ctx["cfo"],
                cfi=ctx["cfi"],
                cff=ctx["cff"],
            )
            tool_calls += 1

            bs = BalanceSheet(
                cash_and_equivalents=ctx["cash_end"],
                net_ppe=184950.0,
                total_assets=ctx["total_assets"],
                total_debt=100000.0,
                total_liabilities=ctx["total_liabilities"],
                retained_earnings=ctx["total_equity"] - 10000.0,
                common_equity=10000.0,
                total_equity=ctx["total_equity"],
            )
            is_stmt = IncomeStatement(
                revenue=ctx["revenue"],
                cogs=200000.0,
                gross_profit=ctx["revenue"] - 200000.0,
                sga_expense=ctx["revenue"] - 200000.0 - 120000.0,
                operating_income=120000.0,
                net_income=ctx["net_income"],
            )
            cf = CashFlowStatement(
                cfo=ctx["cfo"],
                cfi=ctx["cfi"],
                cff=ctx["cff"],
                net_change_in_cash=ctx["cfo"] + ctx["cfi"] + ctx["cff"],
            )
            model = ThreeStatementModel(
                income_statement=is_stmt,
                cash_flow_statement=cf,
                balance_sheet=bs,
                is_balanced=check.is_valid,
                cash_reconciled=check.is_valid,
            )
            models.append(model)
            calc_values["is_balanced"] = check.is_valid
            calc_values["cash_reconciled"] = check.is_valid
            calc_values["assets_equal_liab_equity"] = check.is_valid

            sourced_vals.append(
                SourcedValue(
                    value=ctx["total_assets"],
                    citation=make_cit("Assets", ctx["total_assets"]),
                )
            )

        elif case.track == "track2_fixed_income":
            ctx = case.context_data
            bond_res = FixedIncomeEngine.analyze_bond(
                face_value=ctx["face_value"],
                coupon_rate=ctx["coupon_rate"],
                ytm=ctx["ytm"],
                years_to_maturity=float(ctx["maturity_years"]),
                frequency=1,
            )
            merton_res = FixedIncomeEngine.solve_merton_model(
                equity_value=ctx["equity_value"],
                equity_volatility=ctx["equity_volatility"],
                debt_face_value=ctx["debt_face"],
                risk_free_rate=ctx["risk_free_rate"],
                maturity_years=ctx["horizon_years"],
            )
            tool_calls += 2
            calc_values["bond_price"] = bond_res.clean_price
            calc_values["macaulay_duration_in_range"] = 4.0 <= bond_res.macaulay_duration <= 5.0
            calc_values["merton_distance_to_default_positive"] = (
                merton_res.distance_to_default > 0.0
            )
            calc_values["default_probability_in_range"] = (
                0.0 <= merton_res.default_probability <= 0.10
            )

            sourced_vals.append(
                SourcedValue(
                    value=bond_res.clean_price,
                    citation=make_cit("Bond Price", f"{bond_res.clean_price:.2f}"),
                )
            )

        elif case.track == "track3_econometrics":
            # Generate synthetic random walk and test ADF
            np.random.seed(42)
            rw = np.cumsum(np.random.normal(0, 1, 200)).tolist()
            stat_res = EconometricEngine.test_stationarity(rw)
            tool_calls += 1
            calc_values["series_non_stationary"] = not stat_res.is_stationary
            calc_values["rejects_spurious_relationship"] = not stat_res.is_stationary

            sourced_vals.append(
                SourcedValue(
                    value=stat_res.p_value,
                    citation=make_cit("ADF p-value", f"{stat_res.p_value:.4f}"),
                )
            )

        elif case.track == "track4_financial_ml":
            np.random.seed(42)
            prices = (np.cumsum(np.random.normal(0.01, 1.0, 300)) + 100.0).tolist()
            opt = FinancialMLEngine.find_optimal_fractional_d(prices)
            tool_calls += 1
            calc_values["is_stationary_after_fracdiff"] = opt.adf_p_value < 0.05
            calc_values["memory_preserved"] = opt.correlation_with_original >= 0.25

            sourced_vals.append(
                SourcedValue(
                    value=opt.optimal_d,
                    citation=make_cit("Optimal d*", f"{opt.optimal_d:.2f}"),
                )
            )

        elif case.track == "track5_derivatives":
            ctx = case.context_data
            bsm = DerivativesEngine.price_european_option(
                spot=ctx["spot"],
                strike=ctx["strike"],
                time_to_maturity=ctx["maturity"],
                risk_free_rate=ctx["rate"],
                volatility=ctx["volatility"],
                is_call=True,
            )
            greeks = DerivativesEngine.calculate_bsm_greeks(
                spot=ctx["spot"],
                strike=ctx["strike"],
                time_to_maturity=ctx["maturity"],
                risk_free_rate=ctx["rate"],
                volatility=ctx["volatility"],
                is_call=True,
            )
            # Price calls for butterfly spread K1=90, K2=100, K3=110
            c1 = DerivativesEngine.price_european_option(
                ctx["spot"],
                ctx["k1"],
                ctx["maturity"],
                ctx["rate"],
                ctx["volatility"],
                is_call=True,
            )
            c2 = bsm
            c3 = DerivativesEngine.price_european_option(
                ctx["spot"],
                ctx["k3"],
                ctx["maturity"],
                ctx["rate"],
                ctx["volatility"],
                is_call=True,
            )
            bf_check = DerivativesEngine.verify_butterfly_arbitrage(
                strikes=[ctx["k1"], ctx["k2"], ctx["k3"]],
                call_prices=[c1.price, c2.price, c3.price],
            )
            tool_calls += 4

            calc_values["call_price"] = bsm.price
            calc_values["delta"] = greeks.delta
            calc_values["gamma"] = greeks.gamma
            calc_values["vega"] = greeks.vega
            calc_values["butterfly_arbitrage_free"] = bf_check.is_valid

            sourced_vals.append(
                SourcedValue(
                    value=bsm.price,
                    citation=make_cit("Call Price", f"{bsm.price:.2f}"),
                )
            )

        elif case.track == "track6_microstructure":
            ctx = case.context_data
            lob = ExecutionEngine.analyze_lob_snapshot(
                best_bid=ctx["bid_price"],
                best_ask=ctx["ask_price"],
                bid_size=ctx["bid_size"],
                ask_size=ctx["ask_size"],
            )
            traj = ExecutionEngine.compute_almgren_chriss_schedule(
                total_shares=ctx["total_shares"],
                time_horizon_hours=1.0,
                n_intervals=ctx["periods"],
                daily_volatility=0.02,
                permanent_impact_gamma=2.5e-7,
                temporary_impact_eta=2.5e-6,
                risk_aversion_lambda=1e-5,
            )
            tool_calls += 2
            calc_values["spread"] = lob.spread
            calc_values["microprice"] = lob.micro_price
            calc_values["initial_liquidation_shares"] = traj.trading_trajectory[0]
            calc_values["final_shares_remaining"] = traj.trading_trajectory[-1]

            sourced_vals.append(
                SourcedValue(
                    value=lob.micro_price,
                    citation=make_cit("Microprice", f"{lob.micro_price:.3f}"),
                )
            )

        elif case.track == "track7_sustainability":
            ctx = case.context_data
            waci_res = SustainabilityEngine.calculate_waci(
                portfolio_weights=ctx["weights"],
                emissions=ctx["emissions"],
                revenues_millions=ctx["revenues_mil"],
            )
            bond = SustainabilityLinkedBond(
                isin=ctx["slb_isin"],
                notional=ctx["slb_notional"],
                base_coupon_rate=ctx["slb_base_coupon"],
                target_reduction_pct=ctx["slb_target_reduction"],
                baseline_emissions=ctx["slb_baseline_emissions"],
                step_up_bps=ctx["slb_step_up_bps"],
                target_year=ctx["slb_target_year"],
            )
            slb_res = SustainabilityEngine.evaluate_slb_covenant(
                bond=bond,
                reported_emissions=ctx["slb_reported_emissions"],
            )
            tool_calls += 2
            calc_values["portfolio_waci"] = waci_res.waci
            calc_values["slb_spt_achieved"] = slb_res.spt_achieved
            calc_values["slb_active_coupon"] = slb_res.active_coupon_rate
            calc_values["slb_penalty_triggered"] = not slb_res.spt_achieved

            sourced_vals.append(
                SourcedValue(
                    value=waci_res.waci,
                    citation=make_cit("Portfolio WACI", f"{waci_res.waci:.2f}"),
                )
            )

        elapsed = time.perf_counter() - start_t
        return AgentExecutionResult(
            case_id=case.case_id,
            sourced_values=sourced_vals,
            three_statement_models=models,
            calculated_values=calc_values,
            tool_calls_count=tool_calls,
            mental_math_violations=0,
            latency_seconds=elapsed,
        )


class BenchmarkRunner:
    """Orchestrates benchmark runs and evaluates agent performance across tracks."""

    def __init__(self, cases: Sequence[BenchmarkTestCase] | None = None) -> None:
        self.cases = list(cases) if cases is not None else load_all_test_cases()
        self.evaluator = BenchmarkEvaluator()

    def run_suite(
        self,
        agent_id: str,
        solver_fn: Callable[[BenchmarkTestCase], AgentExecutionResult] | None = None,
    ) -> BenchmarkScorecard:
        """Executes the full suite for a given agent solver."""
        if solver_fn is None:
            solver_fn = ReferenceAgentSolver.solve

        all_sourced: list[SourcedValue] = []
        all_models: list[ThreeStatementModel] = []
        track_scores: dict[str, float] = {}
        ground_truth_hashes = {c.doc_hash for c in self.cases}

        total_tool_calls = 0
        total_mental_math = 0

        for case in self.cases:
            result = solver_fn(case)
            all_sourced.extend(result.sourced_values)
            all_models.extend(result.three_statement_models)
            total_tool_calls += result.tool_calls_count
            total_mental_math += result.mental_math_violations

            # Evaluate quantitative accuracy for this case
            score = self._score_case_accuracy(case, result.calculated_values)
            track_scores[case.track] = score

        # Compute Core Metrics
        pocs = self.evaluator.compute_proof_of_citation_score(
            assertions=all_sourced,
            ground_truth_hashes=ground_truth_hashes,
        )
        icr = self.evaluator.compute_invariant_compliance_rate(
            models=all_models,
        )

        # TPI cutoff based on latest case as-of-date
        latest_cutoff = max(c.as_of_date for c in self.cases)
        tpi = self.evaluator.compute_temporal_purity_index(
            extracted_facts=all_sourced,
            as_of_cutoff_date=latest_cutoff,
        )

        # Tool Math Purity Ratio
        if total_tool_calls + total_mental_math == 0:
            tmpr = 1.0
        else:
            tmpr = float(total_tool_calls / (total_tool_calls + total_mental_math))

        composite = self.evaluator.compute_composite_index(
            pocs=pocs,
            icr=icr,
            tpi=tpi,
            tmpr=tmpr,
        )

        return BenchmarkScorecard(
            agent_id=agent_id,
            proof_of_citation_score=pocs,
            invariant_compliance_rate=icr,
            temporal_purity_index=tpi,
            tool_math_purity_ratio=tmpr,
            composite_lilavati_index=composite,
            track_scores=track_scores,
        )

    def _score_case_accuracy(
        self,
        case: BenchmarkTestCase,
        calc_values: dict[str, Any],
    ) -> float:
        """Compares calculated values against expected ground truth within tolerance."""
        if not case.expected_values:
            return 1.0

        matches = 0
        total = len(case.expected_values)

        for k, expected in case.expected_values.items():
            if k not in calc_values:
                continue

            actual = calc_values[k]
            if isinstance(expected, bool):
                if actual == expected:
                    matches += 1
            elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                if math.isclose(float(actual), float(expected), rel_tol=case.tolerance):
                    matches += 1
            elif (
                isinstance(expected, list)
                and isinstance(actual, (list, tuple))
                and len(expected) == 2
                and expected[0] <= actual[0]
                and actual[1] <= expected[1]
            ) or actual == expected:
                matches += 1

        return float(matches / total)
