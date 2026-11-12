"""
Cryptographic Provenance Engine for Financial Disclosures.

Ensures that every quantitative claim extracted from regulatory filings (10-K, 10-Q, Ind AS)
carries an immutable, verifiable reference back to the source document, page, table, and character span.
"""

from __future__ import annotations

import hashlib
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class CitationRef(BaseModel):
    """Cryptographic provenance record linking a extracted financial value to its primary source."""

    model_config = ConfigDict(frozen=True)

    doc_hash: str = Field(
        ...,
        description="SHA-256 hash of the normalized source document (HTML/PDF/XBRL)",
        min_length=64,
        max_length=64,
    )
    filing_type: str = Field(
        ...,
        description="Type of regulatory filing (e.g., '10-K', '10-Q', 'Ind-AS-Annual', '8-K')",
    )
    filing_date: date = Field(
        ...,
        description="Official publication/filing date of the disclosure",
    )
    period_end: date = Field(
        ...,
        description="Fiscal period end date described by this report (Valid Time)",
    )
    page: int = Field(
        ...,
        ge=1,
        description="1-based page number where the claim appears",
    )
    table_id: str | None = Field(
        default=None,
        description="Unique identifier or index of the table within the document",
    )
    xbrl_tag: str | None = Field(
        default=None,
        description="Canonical or extension XBRL taxonomy tag (e.g., 'us-gaap:Revenues')",
    )
    raw_snippet: str = Field(
        ...,
        description="Verbatim text, cell excerpt, or numerical token from the original disclosure",
    )

    @classmethod
    def create_from_content(
        cls,
        raw_document_bytes: bytes,
        filing_type: str,
        filing_date: date,
        period_end: date,
        page: int,
        raw_snippet: str,
        table_id: str | None = None,
        xbrl_tag: str | None = None,
    ) -> CitationRef:
        """Helper to compute SHA-256 hash automatically from raw document bytes."""
        hasher = hashlib.sha256()
        hasher.update(raw_document_bytes)
        doc_hash = hasher.hexdigest()

        return cls(
            doc_hash=doc_hash,
            filing_type=filing_type,
            filing_date=filing_date,
            period_end=period_end,
            page=page,
            table_id=table_id,
            xbrl_tag=xbrl_tag,
            raw_snippet=raw_snippet.strip(),
        )


class SourcedValue(BaseModel):
    """A financial numerical value strictly bound to its cryptographic CitationRef."""

    model_config = ConfigDict(frozen=True)

    value: float = Field(..., description="The numerical magnitude")
    unit: str = Field(
        default="USD", description="Currency or unit (e.g., 'USD', 'INR', 'ratio', 'bps')"
    )
    scale: int = Field(
        default=1, description="Multiplier (e.g., 1_000_000 for figures reported in millions)"
    )
    citation: CitationRef = Field(..., description="Mandatory cryptographic citation")

    @property
    def normalized_value(self) -> float:
        """Returns the value scaled to base units (e.g., millions * 1e6)."""
        return self.value * self.scale
