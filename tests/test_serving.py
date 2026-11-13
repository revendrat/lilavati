"""
Unit tests for the Līlāvatī agent API serving layer.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from lilavati.framework import (
    END,
    FinancialState,
    FinancialStateGraph,
    create_agent_api,
)


class CreditAnalysisState(FinancialState):
    borrower_name: str = "Acme Industrial"
    ebitda: float = 50.0
    total_debt: float = 200.0
    leverage_ratio: float = 0.0
    is_covenant_compliant: bool = False
    verdict: str = "PENDING"


def test_create_agent_api_endpoints() -> None:
    # Build a simple financial graph
    builder = FinancialStateGraph(CreditAnalysisState)

    def calculate_leverage(state: CreditAnalysisState) -> CreditAnalysisState:
        state.leverage_ratio = state.total_debt / state.ebitda
        state.is_covenant_compliant = state.leverage_ratio <= 4.5
        state.verdict = "APPROVED" if state.is_covenant_compliant else "REJECTED_LEVERAGE_BREACH"
        return state

    builder.add_node("calculate_leverage", calculate_leverage)
    builder.set_entry_point("calculate_leverage")
    builder.add_edge("calculate_leverage", END)
    compiled_graph = builder.compile()

    # Create FastAPI app
    app = create_agent_api(compiled_graph, title="Credit Underwriting Agent API")
    client = TestClient(app)

    # 1. Healthcheck
    resp_health = client.get("/api/v1/health")
    assert resp_health.status_code == 200
    data_health = resp_health.json()
    assert data_health["status"] == "healthy"
    assert data_health["service"] == "Credit Underwriting Agent API"
    assert "calculate_leverage" in data_health["nodes"]

    # 2. Schema introspection
    resp_schema = client.get("/api/v1/schema")
    assert resp_schema.status_code == 200
    schema = resp_schema.json()
    assert "properties" in schema
    assert "leverage_ratio" in schema["properties"]

    # 3. Successful run (Compliant)
    payload_ok: dict[str, Any] = {
        "borrower_name": "Apex Holdings",
        "ebitda": 100.0,
        "total_debt": 300.0,
    }
    resp_run = client.post("/api/v1/run", json=payload_ok)
    assert resp_run.status_code == 200
    data_run = resp_run.json()
    assert data_run["leverage_ratio"] == 3.0
    assert data_run["is_covenant_compliant"] is True
    assert data_run["verdict"] == "APPROVED"

    # 4. Successful run (Breach)
    payload_breach: dict[str, Any] = {
        "borrower_name": "Distressed Corp",
        "ebitda": 20.0,
        "total_debt": 150.0,
    }
    resp_breach = client.post("/api/v1/run", json=payload_breach)
    assert resp_breach.status_code == 200
    data_breach = resp_breach.json()
    assert data_breach["leverage_ratio"] == 7.5
    assert data_breach["is_covenant_compliant"] is False
    assert data_breach["verdict"] == "REJECTED_LEVERAGE_BREACH"
