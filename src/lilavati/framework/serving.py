"""
Production API Serving & Deployment Layer for Project Līlāvatī Agents.

Provides turnkey FastAPI REST service creation and deployment for any compiled
FinancialStateGraph, enabling institutional teams to turn agentic graphs into
production microservices with automated OpenAPI documentation and validation.
"""

from __future__ import annotations

from typing import Any, cast

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from lilavati.framework.graph import CompiledFinancialGraph
from lilavati.framework.state import FinancialState


class HealthResponse(BaseModel):
    """Healthcheck response metadata."""

    status: str
    service: str
    version: str
    nodes: list[str]
    entry_point: str


def create_agent_api(
    graph: CompiledFinancialGraph[Any],
    title: str = "Līlāvatī Agent Microservice",
    description: str = "Audited & Verifiable Financial Agent REST API powered by Project Līlāvatī.",
    version: str = "0.1.0",
) -> FastAPI:
    """
    Constructs a production-ready FastAPI application wrapping a CompiledFinancialGraph.

    Args:
        graph: The compiled FinancialStateGraph instance to serve.
        title: Title of the API service (displayed in Swagger UI).
        description: Service description.
        version: API semantic version.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    state_cls = graph.state_schema

    @app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
    def health_check() -> HealthResponse:
        """Returns API health status, available graph nodes, and entry point."""
        return HealthResponse(
            status="healthy",
            service=title,
            version=version,
            nodes=list(graph.nodes.keys()),
            entry_point=graph.entry_point,
        )

    @app.get("/api/v1/schema", tags=["System"])
    def get_state_schema() -> dict[str, Any]:
        """Returns the JSON schema of the agent's underlying FinancialState."""
        return cast(dict[str, Any], state_cls.model_json_schema())

    @app.post("/api/v1/run", tags=["Agent Execution"])
    def run_agent(payload: dict[str, Any]) -> dict[str, Any]:
        """
        Executes the compiled financial graph from its entry point.

        Validates the incoming payload against the agent's state schema,
        executes all graph nodes and invariant gates, and returns the final
        audited state including all cryptographic citations and formal SMT proofs.
        """
        try:
            # Validate input payload against state schema
            state_instance = state_cls(**payload)
        except Exception as err:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid agent input state payload: {err}",
            ) from err

        try:
            # Execute graph
            result_state = graph.invoke(state_instance)
            if isinstance(result_state, FinancialState):
                return result_state.model_dump()
            return cast(dict[str, Any], dict(result_state))
        except Exception as err:
            raise HTTPException(
                status_code=500,
                detail=f"Agent graph execution error: {err}",
            ) from err

    return app


def serve_agent(
    graph: CompiledFinancialGraph[Any],
    host: str = "0.0.0.0",
    port: int = 8000,
    title: str = "Līlāvatī Agent Microservice",
    **kwargs: Any,
) -> None:
    """
    Starts a production Uvicorn ASGI server hosting the agent REST API.

    Args:
        graph: The compiled FinancialStateGraph instance to serve.
        host: Host IP binding.
        port: Port number.
        title: API service title.
        **kwargs: Additional options passed to uvicorn.run().
    """
    import uvicorn

    app = create_agent_api(graph=graph, title=title)
    uvicorn.run(app, host=host, port=port, **kwargs)
