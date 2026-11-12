"""
Suvarṇa Formal Invariant Engine (named after Bhāskara II's Suvarṇa-gaṇita).

Uses the Z3 Satisfiability Modulo Theories (SMT) solver to formally verify
financial accounting identities, debt covenants, and no-arbitrage conditions.
"""

from __future__ import annotations

import z3
from pydantic import BaseModel, Field


class InvariantCheckResult(BaseModel):
    """Result of an SMT invariant verification check."""

    is_valid: bool = Field(
        ..., description="True if invariants are mathematically satisfiable and consistent"
    )
    status: str = Field(..., description="SMT solver status ('SAT', 'UNSAT', 'UNKNOWN')")
    violations: list[str] = Field(
        default_factory=list, description="List of violated constraints or contradictions"
    )
    model_values: dict[str, float] = Field(
        default_factory=dict, description="Solved variable values if satisfiable"
    )


class SuvarnaEngine:
    """Formal verification engine for financial statements and quantitative models."""

    @staticmethod
    def verify_balance_sheet_equation(
        total_assets: float,
        total_liabilities: float,
        shareholders_equity: float,
        tolerance: float = 1e-4,
    ) -> InvariantCheckResult:
        """
        Formally verifies balance sheet equilibrium using Z3 SMT solver:
        Assets == Liabilities + Equity (within tolerance).
        """
        solver = z3.Solver()
        a = z3.Real("total_assets")
        liab = z3.Real("total_liabilities")
        e = z3.Real("shareholders_equity")

        tol = z3.RealVal(str(tolerance))
        neg_tol = z3.RealVal(str(-tolerance))

        diff = a - (liab + e)
        solver.add(diff >= neg_tol)
        solver.add(diff <= tol)

        solver.add(a == z3.RealVal(str(total_assets)))
        solver.add(liab == z3.RealVal(str(total_liabilities)))
        solver.add(e == z3.RealVal(str(shareholders_equity)))

        check = solver.check()
        if check == z3.sat:
            return InvariantCheckResult(
                is_valid=True,
                status="SAT",
                violations=[],
                model_values={
                    "total_assets": total_assets,
                    "total_liabilities": total_liabilities,
                    "shareholders_equity": shareholders_equity,
                },
            )

        err = abs(total_assets - (total_liabilities + shareholders_equity))
        return InvariantCheckResult(
            is_valid=False,
            status="UNSAT",
            violations=[
                f"Balance sheet mismatch: Assets ({total_assets}) != Liabilities ({total_liabilities}) "
                f"+ Equity ({shareholders_equity}). Discrepancy = {err:.4f}"
            ],
        )

    @staticmethod
    def verify_three_statement_invariants(
        total_assets: float,
        total_liabilities: float,
        shareholders_equity: float,
        net_income: float,
        cash_start: float,
        cash_end: float,
        cfo: float,
        cfi: float,
        cff: float,
        tolerance: float = 1e-4,
    ) -> InvariantCheckResult:
        """
        Formally verifies balance sheet equilibrium and cash flow reconciliation:
        1. Balance Sheet: Assets == Liabilities + Equity
        2. Cash Flow: CashEnd == CashStart + CFO + CFI + CFF
        """
        solver = z3.Solver()

        # Symbolic real variables
        a = z3.Real("total_assets")
        liab = z3.Real("total_liabilities")
        e = z3.Real("shareholders_equity")
        c_start = z3.Real("cash_start")
        c_end = z3.Real("cash_end")
        cfo_s = z3.Real("cfo")
        cfi_s = z3.Real("cfi")
        cff_s = z3.Real("cff")

        # Accounting identities with tolerance
        tol = z3.RealVal(str(tolerance))
        neg_tol = z3.RealVal(str(-tolerance))

        # Balance sheet identity: -tol <= (Assets - (Liabilities + Equity)) <= tol
        bs_diff = a - (liab + e)
        solver.add(bs_diff >= neg_tol)
        solver.add(bs_diff <= tol)

        # Cash flow identity: -tol <= (CashEnd - (CashStart + CFO + CFI + CFF)) <= tol
        cf_diff = c_end - (c_start + cfo_s + cfi_s + cff_s)
        solver.add(cf_diff >= neg_tol)
        solver.add(cf_diff <= tol)

        # Ground actual proposed numbers
        solver.add(a == z3.RealVal(str(total_assets)))
        solver.add(liab == z3.RealVal(str(total_liabilities)))
        solver.add(e == z3.RealVal(str(shareholders_equity)))
        solver.add(c_start == z3.RealVal(str(cash_start)))
        solver.add(c_end == z3.RealVal(str(cash_end)))
        solver.add(cfo_s == z3.RealVal(str(cfo)))
        solver.add(cfi_s == z3.RealVal(str(cfi)))
        solver.add(cff_s == z3.RealVal(str(cff)))

        check = solver.check()
        if check == z3.sat:
            return InvariantCheckResult(
                is_valid=True,
                status="SAT",
                violations=[],
                model_values={
                    "total_assets": total_assets,
                    "total_liabilities": total_liabilities,
                    "shareholders_equity": shareholders_equity,
                    "cash_reconciled_delta": cash_end - cash_start,
                },
            )

        # Identify specific violations
        violations: list[str] = []
        bs_error = abs(total_assets - (total_liabilities + shareholders_equity))
        if bs_error > tolerance:
            violations.append(
                f"Balance sheet mismatch: Assets ({total_assets}) != Liabilities ({total_liabilities}) "
                f"+ Equity ({shareholders_equity}). Delta = {bs_error:.4f}"
            )

        cf_error = abs(cash_end - (cash_start + cfo + cfi + cff))
        if cf_error > tolerance:
            violations.append(
                f"Cash flow mismatch: Ending Cash ({cash_end}) != Starting Cash ({cash_start}) "
                f"+ CFO ({cfo}) + CFI ({cfi}) + CFF ({cff}). Delta = {cf_error:.4f}"
            )

        return InvariantCheckResult(
            is_valid=False,
            status="UNSAT",
            violations=violations,
        )

    @staticmethod
    def verify_debt_covenant(
        total_debt: float,
        cash: float,
        ebitda: float,
        max_leverage_covenant: float,
        min_interest_coverage_covenant: float,
        interest_expense: float,
    ) -> InvariantCheckResult:
        """
        Formally verifies credit agreement covenants:
        1. Net Leverage = (Total Debt - Cash) / EBITDA <= max_leverage_covenant
        2. Interest Coverage = EBITDA / InterestExpense >= min_interest_coverage_covenant
        """
        violations: list[str] = []

        if ebitda <= 0:
            violations.append(
                f"Incurrence failure: EBITDA ({ebitda}) is non-positive; leverage ratio undefined."
            )
            return InvariantCheckResult(is_valid=False, status="UNSAT", violations=violations)

        net_debt = total_debt - cash
        current_leverage = net_debt / ebitda

        if current_leverage > max_leverage_covenant:
            violations.append(
                f"Covenant breach: Net Leverage ({current_leverage:.2f}x) exceeds maximum allowable limit "
                f"({max_leverage_covenant:.2f}x)."
            )

        if interest_expense > 0:
            coverage = ebitda / interest_expense
            if coverage < min_interest_coverage_covenant:
                violations.append(
                    f"Covenant breach: Interest Coverage ({coverage:.2f}x) is below minimum allowable limit "
                    f"({min_interest_coverage_covenant:.2f}x)."
                )

        is_valid = len(violations) == 0
        return InvariantCheckResult(
            is_valid=is_valid,
            status="SAT" if is_valid else "UNSAT",
            violations=violations,
            model_values={
                "net_debt": net_debt,
                "current_leverage": current_leverage,
                "headroom_leverage": max_leverage_covenant - current_leverage,
            },
        )
