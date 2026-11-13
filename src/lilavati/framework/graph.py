"""
Financial State Graph Orchestrator for Project Līlāvatī.

Enables developers to build, compose, and deploy multi-agent financial state machines,
similar to LangGraph and Google ADK, but natively equipped with zero-math enforcement,
SMT verification gates, cryptographic citations, and OpenTelemetry audit tracing.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any, Generic, TypeVar, cast

from lilavati.framework.state import FinancialState
from lilavati.tracing.spans import SpanType
from lilavati.tracing.tracer import Tracer

S = TypeVar("S", bound=FinancialState)
END = "__END__"


class ConditionalEdge(Generic[S]):
    """Conditional transition routing between graph nodes based on state inspection."""

    def __init__(
        self,
        router: Callable[[S], str],
        path_map: dict[str, str] | None = None,
    ) -> None:
        self.router = router
        self.path_map = path_map or {}

    def get_destination(self, state: S) -> str:
        decision = self.router(state)
        if self.path_map and decision in self.path_map:
            return self.path_map[decision]
        return decision


class CompiledFinancialGraph(Generic[S]):
    """A compiled executable financial agent state machine."""

    def __init__(
        self,
        nodes: dict[str, Callable[[S], S]],
        edges: dict[str, str],
        conditional_edges: dict[str, ConditionalEdge[S]],
        entry_point: str,
        state_schema: type[S] | None = None,
        tracer: Tracer | None = None,
        max_steps: int = 25,
    ) -> None:
        self.nodes = nodes
        self.edges = edges
        self.conditional_edges = conditional_edges
        self.entry_point = entry_point
        self.state_schema: type[S] = (
            state_schema if state_schema is not None else cast(type[S], FinancialState)
        )
        self.tracer = tracer or Tracer()
        self.max_steps = max_steps

    def invoke(self, initial_state: S | dict[str, Any]) -> S:
        """Executes the financial state graph from the entry point until reaching END."""
        # Convert dictionary to FinancialState if needed
        state: S
        if isinstance(initial_state, dict):
            state = self.state_schema(**initial_state)
        else:
            state = copy.deepcopy(initial_state)

        current_node_name = self.entry_point
        step = 0

        with self.tracer.span(
            name=f"graph_run:{self.entry_point}",
            span_type=SpanType.AGENT_RUN,
            attributes={"entry_point": self.entry_point},
        ):
            while current_node_name != END and step < self.max_steps:
                step += 1
                if current_node_name not in self.nodes:
                    raise KeyError(f"Graph node '{current_node_name}' not found.")

                node_fn = self.nodes[current_node_name]

                # Trace individual node execution
                with self.tracer.span(
                    name=f"node:{current_node_name}",
                    span_type=SpanType.AGENT_RUN,
                    attributes={"step": step, "node": current_node_name},
                ):
                    state = node_fn(state)

                # Determine next destination
                if current_node_name in self.conditional_edges:
                    cond_edge = self.conditional_edges[current_node_name]
                    current_node_name = cond_edge.get_destination(state)
                elif current_node_name in self.edges:
                    current_node_name = self.edges[current_node_name]
                else:
                    # Default: terminal if no outgoing edge
                    current_node_name = END

        if step >= self.max_steps:
            state.fail_gate(
                f"Graph execution terminated: reached maximum cycle steps ({self.max_steps})."
            )

        return state


class FinancialStateGraph(Generic[S]):
    """
    Builder for financial agent state graphs.

    Usage:
        builder = FinancialStateGraph(FinancialState)
        builder.add_node("analyst", my_analyst_agent)
        builder.add_node("smt_gate", SMTBalanceGate())
        builder.add_conditional_edges("smt_gate", lambda s: "analyst" if not s.is_valid else END)
        builder.set_entry_point("analyst")
        app = builder.compile()
        result = app.invoke(initial_state)
    """

    def __init__(self, state_schema: type[S] | None = None) -> None:
        self.state_schema: type[S] = (
            state_schema if state_schema is not None else cast(type[S], FinancialState)
        )
        self.nodes: dict[str, Callable[[S], S]] = {}
        self.edges: dict[str, str] = {}
        self.conditional_edges: dict[str, ConditionalEdge[S]] = {}
        self.entry_point: str | None = None

    def add_node(self, name: str, node_fn: Callable[[S], S]) -> None:
        """Registers a node in the graph."""
        if name in self.nodes:
            raise ValueError(f"Node '{name}' already registered in graph.")
        self.nodes[name] = node_fn

    def add_edge(self, start_node: str, end_node: str) -> None:
        """Adds a static directed transition between two nodes."""
        self.edges[start_node] = end_node

    def add_conditional_edges(
        self,
        start_node: str,
        router: Callable[[S], str],
        path_map: dict[str, str] | None = None,
    ) -> None:
        """Adds a dynamic transition routed by evaluating the state."""
        self.conditional_edges[start_node] = ConditionalEdge(router=router, path_map=path_map)

    def set_entry_point(self, node_name: str) -> None:
        """Sets the initial starting node for graph execution."""
        self.entry_point = node_name

    def compile(
        self,
        tracer: Tracer | None = None,
        max_steps: int = 25,
    ) -> CompiledFinancialGraph[S]:
        """Compiles the builder into an executable CompiledFinancialGraph."""
        if self.entry_point is None:
            raise ValueError("Cannot compile FinancialStateGraph: no entry point defined.")
        if self.entry_point not in self.nodes:
            raise ValueError(f"Entry point '{self.entry_point}' is not registered as a node.")

        return CompiledFinancialGraph(
            nodes=self.nodes,
            edges=self.edges,
            conditional_edges=self.conditional_edges,
            entry_point=self.entry_point,
            state_schema=self.state_schema,
            tracer=tracer,
            max_steps=max_steps,
        )
