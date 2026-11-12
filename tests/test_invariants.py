from lilavati.core.invariants import SuvarnaEngine


def test_three_statement_invariants_valid() -> None:
    # A balanced model
    result = SuvarnaEngine.verify_three_statement_invariants(
        total_assets=1000.0,
        total_liabilities=600.0,
        shareholders_equity=400.0,
        net_income=120.0,
        cash_start=150.0,
        cash_end=230.0,
        cfo=180.0,
        cfi=-70.0,
        cff=-30.0,
    )

    assert result.is_valid is True
    assert result.status == "SAT"
    assert len(result.violations) == 0


def test_three_statement_invariants_broken_balance_sheet() -> None:
    # Assets != Liabilities + Equity (Assets: 1000, L+E: 950)
    result = SuvarnaEngine.verify_three_statement_invariants(
        total_assets=1000.0,
        total_liabilities=600.0,
        shareholders_equity=350.0,
        net_income=120.0,
        cash_start=150.0,
        cash_end=230.0,
        cfo=180.0,
        cfi=-70.0,
        cff=-30.0,
    )

    assert result.is_valid is False
    assert result.status == "UNSAT"
    assert any("Balance sheet mismatch" in v for v in result.violations)


def test_three_statement_invariants_broken_cash_flow() -> None:
    # Cash end mismatch
    result = SuvarnaEngine.verify_three_statement_invariants(
        total_assets=1000.0,
        total_liabilities=600.0,
        shareholders_equity=400.0,
        net_income=120.0,
        cash_start=150.0,
        cash_end=300.0,  # Expected 150 + 180 - 70 - 30 = 230
        cfo=180.0,
        cfi=-70.0,
        cff=-30.0,
    )

    assert result.is_valid is False
    assert result.status == "UNSAT"
    assert any("Cash flow mismatch" in v for v in result.violations)


def test_debt_covenant_check_pass() -> None:
    result = SuvarnaEngine.verify_debt_covenant(
        total_debt=500.0,
        cash=100.0,  # Net debt = 400
        ebitda=200.0,  # Leverage = 2.0x
        max_leverage_covenant=3.5,
        min_interest_coverage_covenant=2.5,
        interest_expense=40.0,  # Coverage = 5.0x
    )

    assert result.is_valid is True
    assert result.status == "SAT"
    assert result.model_values["current_leverage"] == 2.0
    assert result.model_values["headroom_leverage"] == 1.5


def test_debt_covenant_breach() -> None:
    result = SuvarnaEngine.verify_debt_covenant(
        total_debt=800.0,
        cash=50.0,  # Net debt = 750
        ebitda=150.0,  # Leverage = 5.0x
        max_leverage_covenant=4.0,  # Limit is 4.0x -> Breach!
        min_interest_coverage_covenant=3.0,
        interest_expense=60.0,  # Coverage = 2.5x < 3.0x -> Breach!
    )

    assert result.is_valid is False
    assert result.status == "UNSAT"
    assert len(result.violations) == 2
    assert any("Net Leverage" in v for v in result.violations)
    assert any("Interest Coverage" in v for v in result.violations)
