"""
Financial State Abstractions for the Līlāvatī Agentic Framework.

Provides mutable and immutable state representations for multi-agent financial graphs,
preserving conversation messages, extracted facts, provenance citations, and formal audit logs.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from lilavati.core.provenance import CitationRef, SourcedValue
from lilavati.llm.client import LLMMessage


class FinancialState(BaseModel):
    """
    Base financial state passed across nodes and agents in a FinancialStateGraph.
    Developers subclass this to define domain-specific pipeline states.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    messages: list[LLMMessage] = Field(
        default_factory=list, description="Conversation & turn history"
    )
    citations: list[CitationRef] = Field(
        default_factory=list, description="Verified cryptographic source citations"
    )
    sourced_values: list[SourcedValue] = Field(
        default_factory=list, description="Quantitative values with citations"
    )
    extracted_facts: dict[str, Any] = Field(
        default_factory=dict, description="Extracted numerical & tabular data"
    )
    as_of_date: date | None = Field(default=None, description="Point-in-time boundary cutoff")
    is_valid: bool = Field(default=True, description="True if all formal invariant gates pass")
    gate_violations: list[str] = Field(
        default_factory=list, description="List of SMT or compliance violations"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom developer metadata")

    def add_message(self, role: str, content: str) -> None:
        """Appends a new turn message to the state history."""
        self.messages.append(LLMMessage(role=role, content=content))

    def record_citation(self, citation: CitationRef) -> None:
        """Records a verified cryptographic citation."""
        self.citations.append(citation)

    def record_fact(self, key: str, value: Any) -> None:
        """Stores a structured financial fact."""
        self.extracted_facts[key] = value

    def fail_gate(self, violation: str) -> None:
        """Flags the state as failing formal or compliance checks."""
        self.is_valid = False
        self.gate_violations.append(violation)
