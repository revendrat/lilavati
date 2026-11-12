"""
High-Level Developer Agent Abstraction for Project Līlāvatī.

Enables developers to instantiate autonomous financial agents with custom roles,
prompts, foundation models, and FastMCP tools, ready to run standalone or as graph nodes.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

from lilavati.framework.state import FinancialState
from lilavati.llm.client import BaseLLMClient, UniversalLLMClient
from lilavati.llm.providers import INSTITUTIONAL_MODEL_PRESETS, ModelSpec
from lilavati.prompts.system import get_agent_system_prompt
from lilavati.runtime.agent import AgentConfig, AgentOutput, NeuroSymbolicAgent
from lilavati.tracing.tracer import Tracer


class FinancialAgent:
    """
    Developer-facing Financial Agent.

    Example:
        agent = FinancialAgent(
            name="equity_analyst",
            role="Equity Research Analyst",
            model="gemini-2.5-flash",
            tools=[my_custom_tool],
        )
        output = agent.run("Evaluate AAPL revenue growth")
    """

    def __init__(
        self,
        name: str,
        role: str,
        model: str | ModelSpec | None = None,
        system_prompt: str | None = None,
        tools: list[Callable[..., Any]] | None = None,
        tracer: Tracer | None = None,
        api_key: str | None = None,
        llm_client: BaseLLMClient | None = None,
    ) -> None:
        self.name = name
        self.role = role
        self.tracer = tracer or Tracer()

        # Resolve ModelSpec
        spec: ModelSpec
        if isinstance(model, ModelSpec):
            spec = model
        elif isinstance(model, str) and model in INSTITUTIONAL_MODEL_PRESETS:
            spec = INSTITUTIONAL_MODEL_PRESETS[model]
        elif isinstance(model, str):
            spec = ModelSpec(
                provider=INSTITUTIONAL_MODEL_PRESETS["mock-evaluator"].provider, model_name=model
            )
        else:
            spec = INSTITUTIONAL_MODEL_PRESETS["mock-evaluator"]

        prompt = system_prompt or get_agent_system_prompt(role_description=f"You are a {role}.")

        self.config = AgentConfig(
            agent_id=name,
            role_name=role,
            system_prompt=prompt,
            model_spec=spec,
        )

        client = llm_client or UniversalLLMClient(spec=spec, api_key=api_key)
        self._runtime_agent = NeuroSymbolicAgent(
            config=self.config,
            llm_client=client,
            tracer=self.tracer,
        )

        # Register tools
        if tools:
            for t in tools:
                self.add_tool(t)

    def add_tool(self, fn: Callable[..., Any], description: str | None = None) -> None:
        """Registers a Python function or FastMCP tool to the agent."""
        fn_name = fn.__name__
        fn_doc = description or fn.__doc__ or f"Execute {fn_name}"

        # Generate parameters schema from function signature
        sig = inspect.signature(fn)
        properties: dict[str, Any] = {}
        required: list[str] = []

        for p_name, param in sig.parameters.items():
            if p_name in ("self", "cls"):
                continue
            properties[p_name] = {"type": "string" if param.annotation is str else "number"}
            if param.default is inspect.Parameter.empty:
                required.append(p_name)

        schema = {
            "type": "object",
            "properties": properties,
            "required": required,
        }

        self._runtime_agent.register_tool(
            name=fn_name,
            description=fn_doc,
            parameters_schema=schema,
            fn=fn,
        )

    def run(self, prompt: str) -> AgentOutput:
        """Executes the agent standalone on a user query."""
        return self._runtime_agent.run(prompt)

    def as_node(self) -> Callable[[FinancialState], FinancialState]:
        """Converts the agent into a node callable within a FinancialStateGraph."""

        def _node_fn(state: FinancialState) -> FinancialState:
            last_message = state.messages[-1].content if state.messages else "Perform analysis"
            output = self._runtime_agent.run(last_message)
            state.add_message(role="assistant", content=output.response_text)
            if not output.smt_invariants_verified:
                state.fail_gate(
                    f"Agent '{self.name}' emitted outputs violating formal SMT invariants."
                )
            return state

        return _node_fn
