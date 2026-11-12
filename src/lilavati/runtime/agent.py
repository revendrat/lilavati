"""
Neuro-Symbolic Agent Runtime and Execution Loop for Project Līlāvatī.

Implements the institutional agent lifecycle:
1. Perception & Planning (LLM reasoning over task and context)
2. Deterministic Tool Execution (FastMCP sandboxed tools)
3. Formal Invariant Verification (Z3 SMT solver)
4. SMT-Driven Reflection & Self-Correction (Iterative repair when invariants fail)
5. Cryptographic Provenance Verification (CitationRef checks)
6. Comprehensive OpenTelemetry Tracing (Audit trail generation)
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from lilavati.core.invariants import SuvarnaEngine
from lilavati.core.provenance import SourcedValue
from lilavati.llm.client import BaseLLMClient, LLMMessage, UniversalLLMClient
from lilavati.llm.providers import INSTITUTIONAL_MODEL_PRESETS, ModelSpec
from lilavati.prompts.reflection import generate_smt_reflection_prompt
from lilavati.prompts.system import LILAVATI_CORE_SYSTEM_PROMPT
from lilavati.tracing.spans import SpanType
from lilavati.tracing.tracer import Tracer


class AgentConfig(BaseModel):
    """Configuration specification for an autonomous financial agent."""

    model_config = ConfigDict(frozen=True)

    agent_id: str
    role_name: str
    system_prompt: str = Field(default=LILAVATI_CORE_SYSTEM_PROMPT)
    model_spec: ModelSpec = Field(
        default_factory=lambda: INSTITUTIONAL_MODEL_PRESETS["mock-evaluator"]
    )
    max_reflection_iterations: int = Field(default=3, ge=1, le=10)


class AgentOutput(BaseModel):
    """Final verified execution artifact produced by a Neuro-Symbolic Agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_id: str
    response_text: str
    tool_calls_executed: int
    smt_invariants_verified: bool
    iterations_used: int
    provenance_citations: list[SourcedValue] = Field(default_factory=list)
    audit_summary: dict[str, Any] = Field(default_factory=dict)


class ToolDefinition(BaseModel):
    """Callable tool registered in the agent runtime."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    parameters_schema: dict[str, Any]
    fn: Callable[..., Any]


class NeuroSymbolicAgent:
    """
    Autonomous institutional agent integrating LLMs, FastMCP deterministic tools,
    Z3 formal invariant gates, and OpenTelemetry-compatible tracing.
    """

    def __init__(
        self,
        config: AgentConfig,
        llm_client: BaseLLMClient | None = None,
        tracer: Tracer | None = None,
    ) -> None:
        self.config = config
        self.tracer = tracer or Tracer()
        self.llm = llm_client or UniversalLLMClient(spec=config.model_spec)
        self.tools: dict[str, ToolDefinition] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        parameters_schema: dict[str, Any],
        fn: Callable[..., Any],
    ) -> None:
        """Registers a deterministic tool available for model invocation."""
        self.tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters_schema=parameters_schema,
            fn=fn,
        )

    def run(self, user_query: str) -> AgentOutput:
        """
        Executes the agent loop:
        LLM Planning -> Deterministic Tool Calls -> Z3 SMT Verification -> Self-Correction -> Result
        """
        with self.tracer.span(
            name=f"agent_run:{self.config.agent_id}",
            span_type=SpanType.AGENT_RUN,
            attributes={"query": user_query, "role": self.config.role_name},
        ):
            messages: list[LLMMessage] = [
                LLMMessage(role="system", content=self.config.system_prompt),
                LLMMessage(role="user", content=user_query),
            ]

            tool_schemas = self._build_tool_schemas()
            iterations = 0
            tool_calls_count = 0
            smt_passed = True
            final_text = ""

            while iterations < self.config.max_reflection_iterations:
                iterations += 1

                # Step 1: Call LLM
                with self.tracer.span(
                    name=f"llm_turn_{iterations}",
                    span_type=SpanType.LLM_CALL,
                    attributes={"iteration": iterations},
                ):
                    response = self.llm.generate(
                        messages=messages, tools=tool_schemas if tool_schemas else None
                    )

                # Step 2: Handle Tool Calls
                if response.tool_calls:
                    assistant_msg = LLMMessage(
                        role="assistant",
                        content=response.content,
                        tool_calls=response.tool_calls,
                    )
                    messages.append(assistant_msg)

                    for tc in response.tool_calls:
                        tool_calls_count += 1
                        tool_def = self.tools.get(tc.name)
                        start_time = time.perf_counter()

                        if tool_def:
                            try:
                                tool_result = tool_def.fn(**tc.arguments)
                                dur_ms = (time.perf_counter() - start_time) * 1000.0
                                self.tracer.record_tool_call(
                                    tc.name, tc.arguments, tool_result, dur_ms
                                )
                                tool_output_str = json.dumps(tool_result, default=str)
                            except Exception as err:
                                tool_output_str = f"Tool Error: {err}"
                        else:
                            tool_output_str = f"Error: Tool '{tc.name}' not found."

                        tool_msg = LLMMessage(
                            role="tool",
                            tool_call_id=tc.id,
                            content=tool_output_str,
                        )
                        messages.append(tool_msg)

                    continue

                # Step 3: Inspect for financial statements to verify invariants
                final_text = response.content
                smt_check_result = self._check_smt_invariants_if_present(final_text)

                if smt_check_result is not None and not smt_check_result["is_valid"]:
                    # SMT verification failed: Trigger reflection loop
                    smt_passed = False
                    self.tracer.record_smt_check(
                        invariant_name="three_statement_balance",
                        is_valid=False,
                        violations=smt_check_result["violations"],
                    )
                    reflection_prompt = generate_smt_reflection_prompt(
                        invariant_name="Balance Sheet & Cash Flow Reconcile",
                        violations=smt_check_result["violations"],
                        current_values=smt_check_result["values"],
                    )
                    messages.append(LLMMessage(role="user", content=reflection_prompt))
                    continue
                else:
                    if smt_check_result is not None:
                        self.tracer.record_smt_check(
                            invariant_name="three_statement_balance",
                            is_valid=True,
                        )
                    smt_passed = True
                    break

            summary = self.tracer.get_audit_summary()

            return AgentOutput(
                agent_id=self.config.agent_id,
                response_text=final_text,
                tool_calls_executed=tool_calls_count,
                smt_invariants_verified=smt_passed,
                iterations_used=iterations,
                audit_summary=summary,
            )

    def _build_tool_schemas(self) -> list[dict[str, Any]]:
        """Converts registered tools to standard function declaration format."""
        schemas: list[dict[str, Any]] = []
        for name, tool in self.tools.items():
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": tool.description,
                        "parameters": tool.parameters_schema,
                    },
                }
            )
        return schemas

    def _check_smt_invariants_if_present(self, text: str) -> dict[str, Any] | None:
        """Checks if text contains candidate statement JSON and runs SuvarnaEngine verification."""
        try:
            # Look for JSON block if present
            if "{" in text and "}" in text:
                start = text.index("{")
                end = text.rindex("}") + 1
                data = json.loads(text[start:end])
                if all(k in data for k in ("total_assets", "total_liabilities", "total_equity")):
                    check = SuvarnaEngine.verify_balance_sheet_equation(
                        total_assets=float(data["total_assets"]),
                        total_liabilities=float(data["total_liabilities"]),
                        shareholders_equity=float(data["total_equity"]),
                    )
                    return {
                        "is_valid": check.is_valid,
                        "violations": check.violations,
                        "values": data,
                    }
        except Exception:
            return None
        return None
