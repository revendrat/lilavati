"""
Unit Tests for Agent Prompts, Multi-Provider LLM Client, Tracing, and Runtime.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from lilavati.llm.client import LLMMessage, UniversalLLMClient
from lilavati.llm.providers import INSTITUTIONAL_MODEL_PRESETS, ModelProvider, ModelSpec
from lilavati.prompts import (
    BULL_RESEARCHER_PROMPT,
    FORENSIC_BEAR_PROMPT,
    LILAVATI_CORE_SYSTEM_PROMPT,
    PORTFOLIO_MANAGER_PROMPT,
    SUSTAINABILITY_ANALYST_PROMPT,
    generate_citation_failure_prompt,
    generate_smt_reflection_prompt,
)
from lilavati.runtime.agent import AgentConfig, NeuroSymbolicAgent
from lilavati.tracing.spans import SpanType
from lilavati.tracing.tracer import Tracer


def test_prompts_generation() -> None:
    assert "ZERO LLM ARITHMETIC" in LILAVATI_CORE_SYSTEM_PROMPT
    assert "Bull Equity Research Analyst" in BULL_RESEARCHER_PROMPT
    assert "Forensic Accounting & Bear Auditor" in FORENSIC_BEAR_PROMPT
    assert "Sustainable Finance & Climate Risk Specialist" in SUSTAINABILITY_ANALYST_PROMPT
    assert "Chief Investment Officer" in PORTFOLIO_MANAGER_PROMPT

    smt_prompt = generate_smt_reflection_prompt(
        invariant_name="Assets = Liab + Equity",
        violations=["Discrepancy of 10.0"],
        current_values={"total_assets": 100.0, "total_liabilities": 60.0, "total_equity": 30.0},
    )
    assert "Discrepancy of 10.0" in smt_prompt
    assert "CRITICAL FORMAL INVARIANT FAILURE" in smt_prompt

    cit_prompt = generate_citation_failure_prompt(["Missing 10-K SHA-256 for Cash Item"])
    assert "Missing 10-K SHA-256" in cit_prompt


def test_mock_llm_client() -> None:
    spec = ModelSpec(provider=ModelProvider.MOCK, model_name="mock-test")
    client = UniversalLLMClient(spec=spec)

    resp = client.generate([LLMMessage(role="user", content="Test query")])
    assert "[Mock LLM Response]" in resp.content
    assert resp.usage.total_tokens > 0


class DummyStructuredModel(BaseModel):
    name: str
    target_price: float


def test_tracer_and_spans(tmp_path: Path) -> None:
    tracer = Tracer()
    with tracer.span("test_run", SpanType.AGENT_RUN, attributes={"symbol": "AAPL"}):
        tracer.record_tool_call(
            tool_name="compute_ebitda",
            arguments={"revenue": 100, "cogs": 50},
            output={"ebitda": 50},
            duration_ms=12.5,
        )
        tracer.record_smt_check(
            invariant_name="assets_equation",
            is_valid=True,
        )

    summary = tracer.get_audit_summary()
    assert summary["total_spans"] == 3
    assert summary["tool_calls_count"] == 1
    assert summary["smt_checks_count"] == 1
    assert summary["smt_violations_count"] == 0
    assert summary["is_fully_compliant"] is True

    # Test export to JSONL
    out_file = tmp_path / "test_trace.jsonl"
    tracer.export_jsonl(out_file)
    assert out_file.exists()
    lines = out_file.read_text().strip().split("\n")
    assert len(lines) == 3
    first_record = json.loads(lines[0])
    assert "trace_id" in first_record


def test_neuro_symbolic_agent_execution() -> None:
    config = AgentConfig(
        agent_id="test-agent",
        role_name="Forensic Analyst",
        model_spec=INSTITUTIONAL_MODEL_PRESETS["mock-evaluator"],
    )
    agent = NeuroSymbolicAgent(config=config)

    def dummy_tool(x: float) -> float:
        return x * 2.0

    agent.register_tool(
        name="double_value",
        description="Doubles the input value",
        parameters_schema={"type": "object", "properties": {"x": {"type": "number"}}},
        fn=dummy_tool,
    )

    output = agent.run("Evaluate valuation for company X")
    assert output.agent_id == "test-agent"
    assert output.smt_invariants_verified is True
    assert output.audit_summary["total_spans"] >= 1
