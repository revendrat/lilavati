from datetime import date

from lilavati.connectors.india_filings import (
    IndASCompanyDisclosure,
    IndiaFilingsClient,
)


def test_ind_as_disclosure_parsing() -> None:
    # Modeled on standalone Ind AS financials (figures in ₹ Crores, scale = 10,000,000)
    # Total Assets = 80,000 Cr; Equity = 60,000 Cr; Liabilities = 20,000 Cr
    disclosure = IndASCompanyDisclosure(
        company_name="Infosys Limited",
        symbol="INFY",
        cin="L85110KA1981PLC013115",
        fiscal_year=2024,
        reporting_date=date(2024, 3, 31),
        filing_date=date(2024, 4, 18),
        currency="INR",
        scale=10_000_000,  # 1 Crore = 10 Million INR
        facts={
            "RevenueFromOperations": 153670.0,
            "EmployeeBenefitsExpense": 78240.0,
            "FinanceCosts": 340.0,
            "DepreciationAndAmortisationExpense": 4210.0,
            "ProfitBeforeTax": 34500.0,
            "TaxExpense": 8260.0,
            "ProfitForThePeriod": 26240.0,
            "TotalAssets": 125000.0,
            "TotalEquity": 85000.0,
            "TotalLiabilities": 40000.0,
            "EquityShareCapital": 2070.0,
            "OtherEquity": 82930.0,
            "NetCashFromOperatingActivities": 28400.0,
            "NetCashFromInvestingActivities": -4200.0,
            "NetCashFromFinancingActivities": -24100.0,
            "CashAndCashEquivalents": 14500.0,
        },
    )

    model, sourced_map = IndiaFilingsClient.parse_ind_as_disclosure(disclosure)

    # 1. Income Statement Checks
    # 153,670 Cr * 10,000,000 = 1,536,700,000,000 INR
    assert model.income_statement.revenue == 153670.0 * 10_000_000
    assert model.income_statement.net_income == 26240.0 * 10_000_000
    assert model.income_statement.interest_expense == 340.0 * 10_000_000

    # 2. Balance Sheet & Z3 SMT Invariant Verification
    # Assets (125,000 Cr) == Liabilities (40,000 Cr) + Equity (85,000 Cr)
    assert model.is_balanced is True
    assert model.balance_sheet.total_assets == (40000.0 + 85000.0) * 10_000_000

    # 3. Provenance & Citation Checks
    assert "RevenueFromOperations" in sourced_map
    assert sourced_map["RevenueFromOperations"].unit == "INR"
    assert len(sourced_map["RevenueFromOperations"].citation.doc_hash) == 64
    assert (
        sourced_map["RevenueFromOperations"].citation.xbrl_tag == "mca-ind-as:RevenueFromOperations"
    )
