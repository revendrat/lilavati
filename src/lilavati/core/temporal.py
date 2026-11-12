"""
Bi-Temporal Financial Data Warehouse (DuckDB Engine).

Enforces strict point-in-time (PIT) separation between:
1. Valid Time (T_v): The accounting period an economic event or statement describes.
2. System / Transaction Time (T_s): The exact timestamp when a filing or restatement became public.

Guarantees 100% look-ahead bias resistance during historical agent backtesting.
"""

from __future__ import annotations

from datetime import date

import duckdb
from pydantic import BaseModel, ConfigDict, Field

from lilavati.core.provenance import CitationRef, SourcedValue


class BiTemporalRecord(BaseModel):
    """A bi-temporal financial data entry."""

    model_config = ConfigDict(frozen=True)

    ticker: str
    metric: str
    value: float
    unit: str
    valid_date: date = Field(..., description="End date of the fiscal period (Valid Time)")
    as_of_timestamp: date = Field(
        ..., description="Date when filing became publicly known (System Time)"
    )
    doc_hash: str
    accn: str
    xbrl_tag: str
    is_restatement: bool = False


class BiTemporalWarehouse:
    """Embedded DuckDB bi-temporal warehouse for point-in-time financial queries."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.con = duckdb.connect(database=db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initializes the bi-temporal statements schema."""
        self.con.execute(
            """
            CREATE TABLE IF NOT EXISTS financial_facts (
                ticker VARCHAR,
                metric VARCHAR,
                value DOUBLE,
                unit VARCHAR,
                valid_date DATE,
                as_of_timestamp DATE,
                doc_hash VARCHAR,
                accn VARCHAR,
                xbrl_tag VARCHAR,
                is_restatement BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_bitemporal
            ON financial_facts (ticker, metric, valid_date, as_of_timestamp);
            """
        )

    def store_fact(
        self,
        ticker: str,
        metric: str,
        sourced_value: SourcedValue,
        is_restatement: bool = False,
    ) -> None:
        """Stores a sourced financial fact with its bi-temporal coordinates."""
        cit = sourced_value.citation
        self.con.execute(
            """
            INSERT INTO financial_facts (
                ticker, metric, value, unit, valid_date, as_of_timestamp,
                doc_hash, accn, xbrl_tag, is_restatement
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ticker.upper(),
                metric,
                sourced_value.value,
                sourced_value.unit,
                cit.period_end,
                cit.filing_date,
                cit.doc_hash,
                cit.raw_snippet,
                cit.xbrl_tag or "",
                is_restatement,
            ],
        )

    def query_as_of(
        self,
        ticker: str,
        metric: str,
        valid_date: date,
        as_of_date: date,
    ) -> SourcedValue | None:
        """
        Executes a Point-in-Time (PIT) query.
        Returns the latest known value of the metric for the given valid_date
        that was publicly filed on or before as_of_date.
        """
        res = self.con.execute(
            """
            SELECT value, unit, valid_date, as_of_timestamp, doc_hash, accn, xbrl_tag
            FROM financial_facts
            WHERE ticker = ?
              AND metric = ?
              AND valid_date = ?
              AND as_of_timestamp <= ?
            ORDER BY as_of_timestamp DESC, created_at DESC
            LIMIT 1
            """,
            [ticker.upper(), metric, valid_date, as_of_date],
        ).fetchone()

        if not res:
            return None

        val, unit, v_date, s_date, d_hash, accn, x_tag = res
        cit = CitationRef(
            doc_hash=str(d_hash),
            filing_type="PIT-Filing",
            filing_date=s_date,
            period_end=v_date,
            page=1,
            table_id="bitemporal_duckdb",
            xbrl_tag=str(x_tag),
            raw_snippet=str(accn),
        )

        return SourcedValue(
            value=float(val),
            unit=str(unit),
            scale=1,
            citation=cit,
        )

    def close(self) -> None:
        """Closes the underlying DuckDB connection."""
        self.con.close()
