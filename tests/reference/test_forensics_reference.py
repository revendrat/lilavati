"""Reference tests for agents/forensics.py Altman Z-score.

Source: Altman (1968), "Financial Ratios, Discriminant Analysis and the Prediction of Corporate
Bankruptcy", J. Finance 23(4): Z = 1.2 X1 + 1.4 X2 + 3.3 X3 + 0.6 X4 + 0.999 X5 (ratios as
decimals); zones: < 1.81 distress, 1.81-2.99 grey, > 2.99 safe. Beneish tests: tests/test_beneish.py.
"""

import pytest

from lilavati.agents.forensics import ForensicEngine


def _z(**kw: float) -> tuple[float, str]:
    base = {"working_capital": 100.0, "total_assets": 1000.0, "retained_earnings": 200.0, "ebit": 100.0,
                "market_value_equity": 900.0, "total_liabilities": 600.0, "sales": 1200.0}
    base.update(kw)
    r = ForensicEngine.calculate_altman_z_score(**base)
    return r.z_score, r.distress_zone


def test_hand_computed_z() -> None:
    # X = (0.1, 0.2, 0.1, 1.5, 1.2) -> 0.12 + 0.28 + 0.33 + 0.90 + 1.1988 = 2.8288 (grey)
    z, zone = _z()
    assert z == pytest.approx(2.8288, abs=1e-12)
    assert zone == "Grey"


def test_zones() -> None:
    assert _z(market_value_equity=100.0)[1] == "Grey"  # Z = 2.0288
    assert _z(ebit=200.0, market_value_equity=1200.0)[1] == "Safe"


def test_distress_zone_value() -> None:
    # Market equity must be positive; a negligible value leaves X4 at 0 to within 1e-11.
    z, zone = _z(market_value_equity=1e-9, sales=500.0)
    # 0.12 + 0.28 + 0.33 + 0 + 0.4995 = 1.2295
    assert z == pytest.approx(1.2295, abs=1e-9) and zone == "Distress"


@pytest.mark.parametrize("field", ["total_assets", "total_liabilities"])
def test_zero_denominator_raises_value_error_naming_the_input(field: str) -> None:
    # A zero denominator used to surface as a bare ZeroDivisionError with no hint which input was bad.
    with pytest.raises(ValueError, match=field):
        _z(**{field: 0.0})


@pytest.mark.parametrize("field", ["working_capital", "total_assets", "retained_earnings", "ebit",
                                   "market_value_equity", "total_liabilities", "sales"])
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_input_raises_value_error_naming_the_input(field: str, bad: float) -> None:
    # A NaN used to give a NaN score classed "Safe": every zone comparison with NaN is false.
    with pytest.raises(ValueError, match=field):
        _z(**{field: bad})


@pytest.mark.parametrize("field", ["total_assets", "total_liabilities", "sales", "market_value_equity"])
def test_negative_input_raises_value_error_naming_the_input(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        _z(**{field: -1.0})


def test_zero_sales_and_zero_market_equity_are_rejected() -> None:
    with pytest.raises(ValueError, match="sales"):
        _z(sales=0.0)
    with pytest.raises(ValueError, match="market_value_equity"):
        _z(market_value_equity=0.0)


@pytest.mark.parametrize("field", ["working_capital", "retained_earnings", "ebit"])
def test_negative_working_capital_retained_earnings_and_ebit_are_allowed(field: str) -> None:
    z, zone = _z(**{field: -100.0})
    assert z < 2.8288 and zone in {"Distress", "Grey", "Safe"}
