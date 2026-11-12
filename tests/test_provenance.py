from datetime import date

import pytest
from pydantic import ValidationError

from lilavati.core.provenance import CitationRef, SourcedValue


def test_citation_ref_creation() -> None:
    sample_doc = b"Apple Inc. Form 10-K FY 2024. Total net sales: $391,035 million."
    citation = CitationRef.create_from_content(
        raw_document_bytes=sample_doc,
        filing_type="10-K",
        filing_date=date(2024, 11, 1),
        period_end=date(2024, 9, 28),
        page=48,
        table_id="consolidated_statements_of_operations",
        xbrl_tag="us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        raw_snippet="$391,035",
    )

    assert len(citation.doc_hash) == 64
    assert citation.page == 48
    assert citation.raw_snippet == "$391,035"


def test_sourced_value_normalization() -> None:
    sample_doc = b"Fictional test filing bytes"
    citation = CitationRef.create_from_content(
        raw_document_bytes=sample_doc,
        filing_type="10-Q",
        filing_date=date(2024, 8, 15),
        period_end=date(2024, 6, 30),
        page=12,
        raw_snippet="2,450",
    )

    sourced = SourcedValue(
        value=2450.0,
        unit="USD",
        scale=1_000_000,
        citation=citation,
    )

    assert sourced.normalized_value == 2_450_000_000.0


def test_missing_citation_fails() -> None:
    with pytest.raises(ValidationError):
        # Attempting to create SourcedValue without citation must raise validation error
        SourcedValue(value=100.0)  # type: ignore
