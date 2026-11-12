from datetime import date

from lilavati.core.provenance import CitationRef, SourcedValue
from lilavati.core.temporal import BiTemporalWarehouse


def test_bitemporal_lookahead_isolation() -> None:
    warehouse = BiTemporalWarehouse(db_path=":memory:")

    # Initial filing filed on Nov 01, 2024 for Q3 ending Sept 30, 2024
    initial_citation = CitationRef(
        doc_hash="a" * 64,
        filing_type="10-Q",
        filing_date=date(2024, 11, 1),
        period_end=date(2024, 9, 30),
        page=15,
        table_id="income_statement",
        xbrl_tag="us-gaap:Revenues",
        raw_snippet="$100M reported in 10-Q",
    )
    initial_fact = SourcedValue(value=100.0, unit="USD", scale=1_000_000, citation=initial_citation)
    warehouse.store_fact("ACME", "revenue", initial_fact, is_restatement=False)

    # Restatement filed on Nov 20, 2024 for the same period (Revenue lowered to $95M)
    restatement_citation = CitationRef(
        doc_hash="b" * 64,
        filing_type="10-Q/A",
        filing_date=date(2024, 11, 20),
        period_end=date(2024, 9, 30),
        page=4,
        table_id="restatement_note",
        xbrl_tag="us-gaap:Revenues",
        raw_snippet="$95M restated in 10-Q/A",
    )
    restatement_fact = SourcedValue(
        value=95.0, unit="USD", scale=1_000_000, citation=restatement_citation
    )
    warehouse.store_fact("ACME", "revenue", restatement_fact, is_restatement=True)

    # 1. As of Oct 15, 2024 (before initial filing): Must return None!
    res_before_filing = warehouse.query_as_of(
        "ACME", "revenue", valid_date=date(2024, 9, 30), as_of_date=date(2024, 10, 15)
    )
    assert res_before_filing is None

    # 2. As of Nov 10, 2024 (after initial filing, before restatement): Must return $100M!
    res_between = warehouse.query_as_of(
        "ACME", "revenue", valid_date=date(2024, 9, 30), as_of_date=date(2024, 11, 10)
    )
    assert res_between is not None
    assert res_between.value == 100.0
    assert res_between.citation.doc_hash == "a" * 64

    # 3. As of Nov 25, 2024 (after restatement): Must return $95M!
    res_after_restatement = warehouse.query_as_of(
        "ACME", "revenue", valid_date=date(2024, 9, 30), as_of_date=date(2024, 11, 25)
    )
    assert res_after_restatement is not None
    assert res_after_restatement.value == 95.0
    assert res_after_restatement.citation.doc_hash == "b" * 64

    warehouse.close()
