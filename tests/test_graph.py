from lilavati.core.graph import StatementGraph


def test_statement_graph_baseline() -> None:
    graph = StatementGraph(
        revenue=1000.0,
        gross_margin=0.40,
        sga_ratio=0.15,
        tax_rate=0.25,
        interest_rate=0.05,
        capex=50.0,
        depreciation=40.0,
        cash_start=100.0,
        initial_debt=200.0,
        initial_common_equity=400.0,
        initial_net_ppe=500.0,
    )

    model = graph.compute()

    assert model.is_balanced is True
    assert model.cash_reconciled is True
    assert model.income_statement.gross_profit == 400.0
    assert model.income_statement.operating_income == 250.0
    assert (
        model.balance_sheet.total_assets
        == model.balance_sheet.total_liabilities + model.balance_sheet.total_equity
    )


def test_statement_graph_driver_shock() -> None:
    graph = StatementGraph(
        revenue=1000.0,
        gross_margin=0.40,
        sga_ratio=0.15,
        tax_rate=0.25,
        interest_rate=0.05,
        capex=50.0,
        depreciation=40.0,
        cash_start=100.0,
        initial_debt=200.0,
        initial_common_equity=400.0,
        initial_net_ppe=500.0,
    )

    # Shock revenue to 1500 and capex to 120
    graph.set_driver("revenue", 1500.0)
    graph.set_driver("capex", 120.0)

    shocked_model = graph.compute()

    assert shocked_model.is_balanced is True
    assert shocked_model.cash_reconciled is True
    assert shocked_model.income_statement.revenue == 1500.0
    assert shocked_model.cash_flow_statement.cfi == -120.0
