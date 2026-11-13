"""
Unit tests for the SEC 10-K PDF Connector and Document Decomposition Engine.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lilavati.connectors.pdf_10k import PDF10KParser, SectionBoundaries


def test_pdf_10k_parser_local() -> None:
    sample_path = Path("data/sample_filings/aapl_10k_2026.pdf")
    if not sample_path.exists():
        pytest.skip("Sample 10-K PDF not present in offline test runner")

    parser = PDF10KParser(str(sample_path))
    assert len(parser.doc_hash) == 64
    assert parser.page_count > 50

    sections: SectionBoundaries = parser.locate_sections()
    assert sections.business_page is not None
    assert sections.income_statement_page is not None
    assert sections.balance_sheet_page is not None
    assert sections.cash_flows_page is not None

    filing = parser.extract_full_filing()
    assert filing.company_name == "Apple Inc."
    assert filing.model_current_year.income_statement.revenue > 400000.0
    assert filing.model_current_year.balance_sheet.total_assets > 350000.0
    assert filing.model_current_year.cash_flow_statement.cfo > 100000.0

    # Verify formal SMT verification holds
    assert filing.is_smt_verified is True

    # Verify provenance citations
    assert "curr_revenue" in filing.citations
    assert "curr_total_assets" in filing.citations
    assert filing.citations["curr_revenue"].page == sections.income_statement_page
    assert filing.citations["curr_revenue"].doc_hash == parser.doc_hash
    assert len(filing.citations["curr_revenue"].raw_snippet) > 5
