"""
FastMCP Server for SEC EDGAR Corporate Filings & Structured XBRL Disclosures.

Exposes tools to fetch, parse, and formally verify company three-statement filings
with cryptographic CitationRefs.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from lilavati.connectors.edgar import EdgarClient

mcp = FastMCP(
    name="lilavati-corporate-filings",
)


@mcp.tool()
def get_company_filing_statements(
    ticker_or_cik: str,
    fiscal_year: int,
) -> dict[str, Any]:
    """
    Fetches structured XBRL 10-K filings from SEC EDGAR for a company and fiscal year.
    Returns reconciled Three-Statement model where all line items carry cryptographic CitationRefs.
    """
    client = EdgarClient()
    sourced_model = client.extract_three_statement_model(
        ticker_or_cik=ticker_or_cik,
        fiscal_year=fiscal_year,
    )
    return sourced_model.model_dump()


@mcp.tool()
def extract_single_line_item(
    ticker_or_cik: str,
    metric_name: str,
    fiscal_year: int,
) -> dict[str, Any]:
    """
    Extracts a specific audited metric (e.g. 'Assets', 'Revenues', 'NetIncomeLoss')
    from SEC EDGAR with verbatim citation and accession number.
    """
    client = EdgarClient()
    facts = client.fetch_company_facts(ticker_or_cik)
    item = client.extract_line_item(
        facts=facts,
        candidate_tags=[metric_name],
        fiscal_year=fiscal_year,
    )
    if not item:
        return {"error": f"Metric '{metric_name}' not found for {ticker_or_cik} FY{fiscal_year}."}
    return item.model_dump()


if __name__ == "__main__":
    mcp.run()
