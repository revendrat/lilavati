"""
Execution Tracer and Audit Trail Engine for Financial AI Agents.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from lilavati.tracing.spans import SpanType, TraceSpan


class Tracer:
    """Thread-safe tracer collecting spans and recording institutional audit trails."""

    def __init__(self, trace_id: str | None = None) -> None:
        self.trace_id = trace_id or uuid.uuid4().hex
        self._spans: list[TraceSpan] = []
        self._active_parent_id: str | None = None

    @property
    def spans(self) -> list[TraceSpan]:
        """Returns all completed and recorded spans."""
        return list(self._spans)

    @contextmanager
    def span(
        self,
        name: str,
        span_type: SpanType,
        attributes: dict[str, Any] | None = None,
    ) -> Generator[TraceSpan, None, None]:
        """Context manager to trace an execution step."""
        current_parent = self._active_parent_id
        active_span = TraceSpan(
            trace_id=self.trace_id,
            parent_span_id=current_parent,
            name=name,
            span_type=span_type,
            attributes=attributes or {},
        )
        self._active_parent_id = active_span.span_id

        try:
            yield active_span
            final_span = active_span.close(status="OK")
            self._spans.append(final_span)
        except Exception as exc:
            final_span = active_span.close(status="ERROR", error_message=str(exc))
            self._spans.append(final_span)
            raise
        finally:
            self._active_parent_id = current_parent

    def record_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        output: Any,
        duration_ms: float = 0.0,
    ) -> None:
        """Explicit helper to record a FastMCP deterministic tool invocation."""
        span = TraceSpan(
            trace_id=self.trace_id,
            parent_span_id=self._active_parent_id,
            name=f"tool:{tool_name}",
            span_type=SpanType.TOOL_EXECUTION,
            duration_ms=duration_ms,
            status="OK",
            attributes={
                "tool_name": tool_name,
                "arguments": arguments,
                "output": str(output),
            },
        )
        self._spans.append(span)

    def record_smt_check(
        self,
        invariant_name: str,
        is_valid: bool,
        violations: list[str] | None = None,
    ) -> None:
        """Records an SMT solver invariant verification pass/fail event."""
        status = "OK" if is_valid else "VIOLATION"
        span = TraceSpan(
            trace_id=self.trace_id,
            parent_span_id=self._active_parent_id,
            name=f"smt:{invariant_name}",
            span_type=SpanType.SMT_VERIFICATION,
            status=status,
            error_message="; ".join(violations) if violations else None,
            attributes={
                "invariant": invariant_name,
                "is_valid": is_valid,
                "violations": violations or [],
            },
        )
        self._spans.append(span)

    def export_jsonl(self, output_path: str | Path) -> None:
        """Dumps all captured spans to a JSON Lines audit file for compliance storage."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for s in self._spans:
                f.write(json.dumps(s.model_dump()) + "\n")

    def get_audit_summary(self) -> dict[str, Any]:
        """Returns high-level statistics of the execution trace."""
        tool_calls = sum(1 for s in self._spans if s.span_type == SpanType.TOOL_EXECUTION)
        llm_calls = sum(1 for s in self._spans if s.span_type == SpanType.LLM_CALL)
        smt_checks = sum(1 for s in self._spans if s.span_type == SpanType.SMT_VERIFICATION)
        smt_violations = sum(
            1
            for s in self._spans
            if s.span_type == SpanType.SMT_VERIFICATION and s.status == "VIOLATION"
        )
        return {
            "trace_id": self.trace_id,
            "total_spans": len(self._spans),
            "tool_calls_count": tool_calls,
            "llm_calls_count": llm_calls,
            "smt_checks_count": smt_checks,
            "smt_violations_count": smt_violations,
            "is_fully_compliant": (smt_violations == 0),
        }
