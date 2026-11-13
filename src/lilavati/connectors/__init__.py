"""
Connectors for external financial disclosures, market feeds, and macro series.
"""

from lilavati.connectors.edgar import EdgarClient, SourcedThreeStatementModel
from lilavati.connectors.india_filings import IndiaFilingsClient
from lilavati.connectors.market_data import MarketDataClient
from lilavati.connectors.pdf_10k import ExtractedFiling10K, PDF10KParser, SectionBoundaries

__all__ = [
    "EdgarClient",
    "ExtractedFiling10K",
    "IndiaFilingsClient",
    "MarketDataClient",
    "PDF10KParser",
    "SectionBoundaries",
    "SourcedThreeStatementModel",
]
