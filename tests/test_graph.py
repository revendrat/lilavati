"""StatementGraph: a one-period projection with no plug, so its balance check can fail.

Expected values are hand-computed in the comments (one-year indirect-method roll-forward). The graph used
to add the balance-sheet gap to equity, so ``is_balanced`` held for any input (an opening cash of 1e9
against debt of 200 and equity of 400 "balanced" with a plug of 999,999,974), and operating cash flow left
out the working-capital changes whose balances it reported.
"""

import math

import pytest

from lilavati.core.graph import StatementGraph

# Opening balance sheet: assets 100 + 120 + 500 + 30 = 750; liabilities 60 + 200 + 40 = 300;
# equity 300 + 150 = 450; 300 + 450 = 750.
BASE = {"revenue": 1000.0, "gross_margin": 0.40, "sga_ratio": 0.15, "tax_rate": 0.25, "interest_rate": 0.05,
        "capex": 50.0, "depreciation": 40.0, "cash_start": 100.0, "initial_debt": 200.0, "initial_common_equity": 300.0,
        "initial_net_ppe": 500.0, "opening_receivables": 120.0, "opening_payables": 60.0,
        "opening_retained_earnings": 150.0, "dso_days": 36.5, "dpo_days": 36.5, "other_assets": 30.0,
        "other_liabilities": 40.0}


def _graph(**kw: float) -> StatementGraph:
    return StatementGraph(**{**BASE, **kw})


def test_hand_computed_one_year_projection() -> None:
    m = _graph().compute()
    i, c, b = m.income_statement, m.cash_flow_statement, m.balance_sheet
    # COGS 600, gross profit 400, SG&A 150, EBIT 250, interest 200 x 0.05 = 10, pre-tax 240, tax 60, NI 180.
    assert (i.cogs, i.gross_profit, i.sga_expense, i.operating_income) == pytest.approx((600, 400, 150, 250))
    assert (i.interest_expense, i.tax_expense, i.net_income) == pytest.approx((10, 60, 180))
    # Receivables 1000 / 365 x 36.5 = 100 (down 20), payables 600 / 365 x 36.5 = 60 (unchanged).
    assert (b.accounts_receivable, b.accounts_payable) == pytest.approx((100, 60))
    # CFO = 180 + 40 - (100 - 120) + (60 - 60) = 240; CFI = -50; cash 100 + 240 - 50 = 290.
    assert (c.cfo, c.cfi, c.cff, c.net_change_in_cash) == pytest.approx((240, -50, 0, 190))
    assert b.cash_and_equivalents == pytest.approx(290)
    # PP&E 500 + 50 - 40 = 510; retained earnings 150 + 180 = 330; equity 300 + 330 = 630.
    assert (b.net_ppe, b.retained_earnings, b.total_equity) == pytest.approx((510, 330, 630))
    # Assets 290 + 100 + 510 + 30 = 930; liabilities 60 + 200 + 40 = 300; 300 + 630 = 930.
    assert (b.total_assets, b.total_liabilities) == pytest.approx((930, 300))
    assert b.total_equity == pytest.approx(b.common_equity + b.retained_earnings, abs=1e-12)  # no plug
    assert m.is_balanced is True and m.cash_reconciled is True


def test_a_payables_increase_raises_operating_cash_flow() -> None:
    # Payables 600 / 365 x 73 = 120, up 60: CFO 180 + 40 + 20 + 60 = 300, cash 100 + 300 - 50 = 350,
    # assets 350 + 100 + 510 + 30 = 990 = liabilities (120 + 200 + 40 = 360) + equity 630.
    m = _graph(dpo_days=73.0).compute()
    assert m.cash_flow_statement.cfo == pytest.approx(300)
    assert m.balance_sheet.cash_and_equivalents == pytest.approx(350)
    assert (m.balance_sheet.total_assets, m.balance_sheet.total_liabilities) == pytest.approx((990, 360))
    assert m.is_balanced is True and m.cash_reconciled is True


def test_a_loss_earns_no_tax_credit_and_still_balances() -> None:
    # SG&A 450: EBIT -50, pre-tax -60, tax max(0, -15) = 0, NI -60; CFO -60 + 40 + 20 = 0, cash 50.
    m = _graph(sga_ratio=0.45).compute()
    assert (m.income_statement.tax_expense, m.income_statement.net_income) == pytest.approx((0, -60))
    assert m.balance_sheet.cash_and_equivalents == pytest.approx(50)
    assert m.is_balanced is True and m.cash_reconciled is True


class _ForgetsReceivables(StatementGraph):
    """A wiring fault: operating cash flow without the change in receivables."""

    def _operating_cash_flow(self, net_income: float, depreciation: float, change_receivables: float,
                             change_payables: float) -> float:
        return net_income + depreciation + change_payables


def test_the_balance_check_fails_when_the_wiring_is_wrong() -> None:
    # Receivables fell by 20, so leaving that out of CFO understates cash by 20: assets 910 vs 930.
    m = _ForgetsReceivables(**BASE).compute()
    gap = m.balance_sheet.total_assets - (m.balance_sheet.total_liabilities + m.balance_sheet.total_equity)
    assert gap == pytest.approx(-20)
    assert m.is_balanced is False and m.cash_reconciled is False


def test_an_opening_balance_sheet_that_does_not_balance_raises() -> None:
    with pytest.raises(ValueError, match="opening balance sheet does not balance"):
        _graph(cash_start=101.0).compute()
    graph = _graph()
    graph.set_driver("cash_start", 1e9)  # "balanced" with a plug of 999,999,974 before
    with pytest.raises(ValueError, match="does not balance"):
        graph.compute()


def test_driver_shock_rolls_forward() -> None:
    graph = _graph()
    graph.set_driver("revenue", 1500.0)
    graph.set_driver("capex", 120.0)
    m = graph.compute()
    # Receivables 1500 / 365 x 36.5 = 150; payables 900 / 365 x 36.5 = 90; PP&E 500 + 120 - 40 = 580.
    assert (m.balance_sheet.accounts_receivable, m.balance_sheet.accounts_payable) == pytest.approx((150, 90))
    assert m.balance_sheet.net_ppe == pytest.approx(580)
    assert m.cash_flow_statement.cfi == -120.0
    assert m.is_balanced is True and m.cash_reconciled is True


def test_with_drivers_copies_every_driver_and_leaves_the_original() -> None:
    graph = _graph(dpo_days=73.0)
    clone = graph.with_drivers(revenue=1050.0)
    assert clone.drivers == {**graph.drivers, "revenue": 1050.0}
    assert graph.drivers["revenue"] == 1000.0
    assert type(_ForgetsReceivables(**BASE).with_drivers(revenue=1.0)) is _ForgetsReceivables
    with pytest.raises(KeyError, match="dso"):
        graph.with_drivers(dso=40.0)


@pytest.mark.parametrize(("field", "bad"), [("revenue", math.nan), ("cash_start", math.inf),
                                            ("dso_days", -1.0), ("opening_payables", -5.0), ("tax_rate", 1.5)])
def test_invalid_inputs_raise_naming_the_input(field: str, bad: float) -> None:
    with pytest.raises(ValueError, match=field):
        _graph(**{field: bad})
    graph = _graph()
    with pytest.raises(ValueError, match=field):
        graph.set_driver(field, bad)
    assert graph.drivers == _graph().drivers  # a rejected change leaves the drivers as they were
