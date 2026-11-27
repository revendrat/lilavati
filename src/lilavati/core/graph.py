"""
Statement graph: a one-period three-statement projection driven by operating drivers.

From an opening balance sheet and a set of drivers, ``StatementGraph.compute`` projects the income
statement, the cash flow statement (indirect method) and the closing balance sheet. Nothing is plugged:
every closing balance is rolled forward from its opening balance, so the balance-sheet identity is a
check on the model's wiring (does the cash flow statement capture every balance-sheet change?), not an
identity that holds by construction. A wiring fault (a working-capital change left out of operating cash
flow, say) makes ``is_balanced`` and ``cash_reconciled`` False.
"""

from __future__ import annotations

import math

from lilavati.core.invariants import SuvarnaEngine
from lilavati.schemas.statements import (
    BalanceSheet,
    CashFlowStatement,
    IncomeStatement,
    ThreeStatementModel,
)

DAYS_IN_YEAR = 365.0
# Relative tolerance for the identity checks: float rounding only (sums of a dozen terms are exact to
# about 1e-15 of their size), far below any real wiring fault.
REL_TOLERANCE = 1e-12

_NON_NEGATIVE = ("revenue", "capex", "depreciation", "dso_days", "dpo_days", "opening_receivables",
                 "opening_payables")


def _validate(drivers: dict[str, float]) -> dict[str, float]:
    """Raise ``ValueError`` naming the first driver that is not finite or out of range; else return them."""
    for name, value in drivers.items():
        if not math.isfinite(value):
            raise ValueError(f"{name} must be a finite number, got {value}.")
    for name in _NON_NEGATIVE:
        if drivers[name] < 0:
            raise ValueError(f"{name} must be non-negative, got {drivers[name]}.")
    if not 0.0 <= drivers["tax_rate"] <= 1.0:
        raise ValueError(f"tax_rate must be a decimal in [0, 1], got {drivers['tax_rate']}.")
    return drivers


class StatementGraph:
    """
    One-period three-statement projection with driver shocks (``set_driver``, ``with_drivers``).

    All amounts in one currency unit (e.g. USD millions); ratios and rates as decimals (0.40, not 40);
    ``dso_days`` and ``dpo_days`` in days of a 365-day year.

    Opening balance sheet (must balance, or ``ValueError``):
    assets = ``cash_start`` + ``opening_receivables`` + ``initial_net_ppe`` + ``other_assets``;
    liabilities = ``opening_payables`` + ``initial_debt`` + ``other_liabilities``;
    equity = ``initial_common_equity`` (all equity other than retained earnings: paid-in capital,
    other comprehensive income, treasury stock, non-controlling interests) + ``opening_retained_earnings``.

    The period:

    - Income statement: COGS = revenue × (1 − gross margin); SG&A = revenue × ``sga_ratio``; interest =
      opening debt × ``interest_rate``; tax = max(0, pre-tax income × ``tax_rate``), so a loss earns no
      tax credit.
    - Closing receivables = revenue / 365 × DSO; closing payables = COGS / 365 × DPO.
    - Cash flow: CFO = net income + depreciation − Δreceivables + Δpayables; CFI = −capex; CFF = 0.
    - Closing balances: net PP&E = opening + capex − depreciation; retained earnings = opening + net
      income; cash = opening + CFO + CFI + CFF.

    Not modelled (held at their opening values): debt (no issuance or repayment), dividends and
    buybacks, inventory, other assets and other liabilities.
    """

    def __init__(
        self,
        revenue: float,
        gross_margin: float,
        sga_ratio: float,
        tax_rate: float,
        interest_rate: float,
        capex: float,
        depreciation: float,
        cash_start: float,
        initial_debt: float,
        initial_common_equity: float,
        initial_net_ppe: float,
        *,
        opening_receivables: float,
        opening_payables: float,
        opening_retained_earnings: float,
        dso_days: float,
        dpo_days: float,
        other_assets: float = 0.0,
        other_liabilities: float = 0.0,
    ) -> None:
        self.drivers: dict[str, float] = {
            "revenue": revenue,
            "gross_margin": gross_margin,
            "sga_ratio": sga_ratio,
            "tax_rate": tax_rate,
            "interest_rate": interest_rate,
            "capex": capex,
            "depreciation": depreciation,
            "cash_start": cash_start,
            "total_debt": initial_debt,
            "common_equity": initial_common_equity,
            "net_ppe_start": initial_net_ppe,
            "opening_receivables": opening_receivables,
            "opening_payables": opening_payables,
            "opening_retained_earnings": opening_retained_earnings,
            "other_assets": other_assets,
            "other_liabilities": other_liabilities,
            "dso_days": dso_days,
            "dpo_days": dpo_days,
        }
        _validate(self.drivers)

    def set_driver(self, driver_name: str, new_value: float) -> None:
        """Change one driver in place. Opening-balance drivers must still balance (checked by ``compute``)."""
        self.drivers = _validate({**self.drivers, **self._known({driver_name: new_value})})

    def with_drivers(self, **changes: float) -> StatementGraph:
        """A copy with every driver carried over and ``changes`` applied (keys as in ``drivers``)."""
        clone = object.__new__(type(self))
        clone.drivers = _validate({**self.drivers, **self._known(changes)})
        return clone

    def _known(self, changes: dict[str, float]) -> dict[str, float]:
        unknown = [k for k in changes if k not in self.drivers]
        if unknown:
            raise KeyError(f"Unknown driver(s) {unknown}. Valid drivers: {list(self.drivers.keys())}")
        return changes

    def opening_balance_gap(self) -> float:
        """Opening assets − (liabilities + equity), in input units; zero for a consistent opening balance sheet."""
        d = self.drivers
        assets = d["cash_start"] + d["opening_receivables"] + d["net_ppe_start"] + d["other_assets"]
        liabilities = d["opening_payables"] + d["total_debt"] + d["other_liabilities"]
        equity = d["common_equity"] + d["opening_retained_earnings"]
        return assets - (liabilities + equity)

    def _operating_cash_flow(
        self, net_income: float, depreciation: float, change_receivables: float, change_payables: float
    ) -> float:
        """Indirect method: net income + depreciation − Δreceivables + Δpayables."""
        return net_income + depreciation - change_receivables + change_payables

    def compute(self) -> ThreeStatementModel:
        """
        Project one period and check the closing balance sheet.

        ``is_balanced``: the closing assets equal liabilities plus equity, each side summed from its own
        rolled-forward lines (checked with ``SuvarnaEngine``, which also checks the cash roll-forward).
        ``cash_reconciled``: closing cash from the cash flow statement equals the cash the balance sheet
        implies (liabilities + equity − non-cash assets). In a projection the two are one test seen from
        two sides: a wiring fault fails both. Tolerance: float rounding (``REL_TOLERANCE`` of the
        balance-sheet size). Raises ``ValueError`` if the opening balance sheet does not balance.
        """
        d = self.drivers
        size = max(1.0, *(abs(v) for v in d.values()))
        tol = REL_TOLERANCE * size
        gap = self.opening_balance_gap()
        if abs(gap) > tol:
            raise ValueError(
                f"The opening balance sheet does not balance: assets exceed liabilities plus equity by {gap}. "
                "Check cash_start, opening_receivables, initial_net_ppe and other_assets against "
                "opening_payables, initial_debt, other_liabilities, initial_common_equity and "
                "opening_retained_earnings."
            )

        rev = d["revenue"]
        deprec = d["depreciation"]
        capex = d["capex"]
        debt = d["total_debt"]

        # 1. Income statement
        cogs = rev * (1.0 - d["gross_margin"])
        gross_profit = rev - cogs
        sga = rev * d["sga_ratio"]
        ebit = gross_profit - sga
        interest_exp = debt * d["interest_rate"]
        ebt = ebit - interest_exp
        tax_exp = max(0.0, ebt * d["tax_rate"])
        net_income = ebt - tax_exp

        # 2. Working capital
        ar_end = rev / DAYS_IN_YEAR * d["dso_days"]
        ap_end = cogs / DAYS_IN_YEAR * d["dpo_days"]
        change_ar = ar_end - d["opening_receivables"]
        change_ap = ap_end - d["opening_payables"]

        # 3. Cash flow statement
        cfo = self._operating_cash_flow(net_income, deprec, change_ar, change_ap)
        cfi = -capex
        cff = 0.0
        net_change_cash = cfo + cfi + cff
        cash_end = d["cash_start"] + net_change_cash

        # 4. Closing balance sheet, every line rolled forward from its opening balance
        net_ppe_end = d["net_ppe_start"] + capex - deprec
        retained_earnings = d["opening_retained_earnings"] + net_income
        total_assets = cash_end + ar_end + net_ppe_end + d["other_assets"]
        total_liabilities = ap_end + debt + d["other_liabilities"]
        total_equity = d["common_equity"] + retained_earnings
        cash_implied = total_liabilities + total_equity - (ar_end + net_ppe_end + d["other_assets"])

        inv_check = SuvarnaEngine.verify_three_statement_invariants(
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            shareholders_equity=total_equity,
            net_income=net_income,
            cash_start=d["cash_start"],
            cash_end=cash_end,
            cfo=cfo,
            cfi=cfi,
            cff=cff,
            tolerance=tol,
        )

        return ThreeStatementModel(
            income_statement=IncomeStatement(
                revenue=rev,
                cogs=cogs,
                gross_profit=gross_profit,
                sga_expense=sga,
                operating_income=ebit,
                interest_expense=interest_exp,
                tax_expense=tax_exp,
                net_income=net_income,
            ),
            cash_flow_statement=CashFlowStatement(
                cfo=cfo,
                cfi=cfi,
                cff=cff,
                net_change_in_cash=net_change_cash,
            ),
            balance_sheet=BalanceSheet(
                cash_and_equivalents=cash_end,
                accounts_receivable=ar_end,
                net_ppe=net_ppe_end,
                total_assets=total_assets,
                accounts_payable=ap_end,
                total_debt=debt,
                total_liabilities=total_liabilities,
                retained_earnings=retained_earnings,
                common_equity=d["common_equity"],
                total_equity=total_equity,
            ),
            is_balanced=inv_check.is_valid,
            cash_reconciled=abs(cash_end - cash_implied) <= tol,
        )
