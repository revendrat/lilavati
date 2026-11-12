"""
Institutional Tracing Spans and Audit Trail Data Models for Project Līlāvatī.

Follows OpenTelemetry (OTel) semantic conventions for financial agent execution,
capturing LLM generation, FastMCP tool calls, SMT formal verification, and citation hashes.
"""

from __future__ import annotations

import time
import uuid
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SpanType(StrEnum):
    """Categorization of agent execution steps."""

    AGENT_RUN = "agent.run"
    LLM_CALL = "llm.call"
    TOOL_EXECUTION = "tool.execution"
    SMT_VERIFICATION = "smt.verification"
    CITATION_CHECK = "citation.check"
    CRITIC_GATE = "critic.gate"


class TraceSpan(BaseModel):
    """An immutable audit record for an execution step within an agent run."""

    model_config = ConfigDict(frozen=True)

    span_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    trace_id: str
    parent_span_id: str | None = None
    name: str
    span_type: SpanType
    start_time: float = Field(default_factory=time.time)
    end_time: float | None = None
    duration_ms: float | None = None
    status: str = "OK"  # OK, ERROR, VIOLATION
    error_message: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)

    def close(
        self,
        status: str = "OK",
        error_message: str | None = None,
        extra_attributes: dict[str, Any] | None = None,
    ) -> TraceSpan:
        """Returns a finalized copy of the span with end time and duration calculated."""
        now = time.time()
        dur = (now - self.start_time) * 1000.0
        attrs = dict(self.attributes)
        if extra_attributes:
            attrs.update(extra_attributes)

        return TraceSpan(
            span_id=self.span_id,
            trace_id=self.trace_id,
            parent_span_id=self.parent_span_id,
            name=self.name,
            span_type=self.span_type,
            start_time=self.start_time,
            end_time=now,
            duration_ms=round(dur, 2),
            status=status,
            error_message=error_message,
            attributes=attrs,
        )
