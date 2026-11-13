# Tutorial: Building, Testing, and Serving Your First Audited Financial Agent

Welcome to Project Līlāvatī! This tutorial guides you step-by-step through designing, implementing, formally verifying, testing, and serving a production-grade financial agent.

---

## 🎯 What You Will Build

In this tutorial, you will build an **Institutional Credit Underwriting & Covenant Monitoring Agent**. 

Unlike generic agent frameworks (LangChain, AutoGen, CrewAI) that let language models estimate financial ratios through stochastic token generation, your Līlāvatī agent will:
1. **Store Immutable State (`FinancialState`)**: Maintain typed inputs, outputs, messages, and cryptographic statutory citations.
2. **Execute Deterministic Math**: Calculate leverage ratios, interest coverage, and distance-to-default using certified Python engines.
3. **Formally Prove Invariants via Z3 SMT Solver**: Prove whether the borrower satisfies credit agreement covenants ($TotalDebt / EBITDA \le 4.0\text{x}$) and automatically calculate the exact required sponsor equity cure if breached.
4. **Pass Automated `pytest` Verification**: Verify happy-path and distressed scenarios with unit tests.
5. **Deploy as a Production REST API**: Convert the compiled agent graph into a high-performance FastAPI microservice with automated OpenAPI (`/docs`) in one line of code.

---

## 📦 Prerequisites & Installation

Create a virtual environment and install Līlāvatī:

```bash
# Clone the repository
git clone https://github.com/revendrat/lilavati.git
cd lilavati

# Install with development and serving dependencies using uv
uv sync
```

---

## Step 1: Define the Typed State Container

Every agent workflow in Līlāvatī revolves around an explicit, immutable state container inheriting from `FinancialState`. This guarantees that all messages, facts, and cryptographic citations (`CitationRef`) are tracked across nodes.

```python
from datetime import date
from lilavati.framework import FinancialState


class CreditUnderwritingState(FinancialState):
    """Typed execution state for the Credit Underwriting Agent."""

    borrower_name: str = "Apollo Industrial Corp"
    fiscal_year: int = 2026
    ebitda: float = 80.0  # In $ millions
    total_debt: float = 280.0  # In $ millions
    interest_expense: float = 18.0  # In $ millions
    equity_value: float = 400.0  # Market or enterprise equity value
    equity_volatility: float = 0.30  # 30% annualized volatility

    # Statutory Debt Covenants (from Credit Indenture)
    max_leverage_covenant: float = 4.00  # Max Debt / EBITDA <= 4.0x
    min_coverage_covenant: float = 3.50  # Min EBITDA / Interest >= 3.5x

    # Output Diagnostics & Formal Proof Results
    leverage_ratio: float = 0.0
    interest_coverage: float = 0.0
    covenant_satisfied: bool = False
    merton_default_probability: float = 0.0
    required_equity_cure_usd: float = 0.0
    underwriting_verdict: str = "PENDING"
```

---

## Step 2: Implement Execution Nodes

Nodes are standard Python functions `Callable[[S], S]` that take the current state, perform deterministic computations or tool calls, and return the updated state.

### Node 1: Ingestion & Cryptographic Provenance Anchoring
First, anchor the extracted borrower disclosures to a statutory source document hash:

```python
from lilavati.core.provenance import CitationRef


def ingest_and_provenance_node(state: CreditUnderwritingState) -> CreditUnderwritingState:
    """Node 1: Grounds extracted borrower disclosures with cryptographic SHA-256 provenance."""
    # SHA-256 hash of the borrower's primary credit agreement / 10-K filing
    doc_hash = "a7c8e9b01234567890abcdef1234567890abcdef1234567890abcdef12345678"

    # Record immutable citations linking metrics to exact pages and snippets
    state.record_citation(
        CitationRef(
            doc_hash=doc_hash,
            filing_type="Credit-Agreement",
            filing_date=date(2026, 3, 15),
            period_end=date(2025, 12, 31),
            page=24,
            raw_snippet=f"Adjusted Consolidated EBITDA: ${state.ebitda:.1f}M",
        )
    )
    state.record_citation(
        CitationRef(
            doc_hash=doc_hash,
            filing_type="Credit-Agreement",
            filing_date=date(2026, 3, 15),
            period_end=date(2025, 12, 31),
            page=28,
            raw_snippet=f"Total Outstanding Indebtedness: ${state.total_debt:.1f}M",
        )
    )
    state.record_fact("ebitda", state.ebitda)
    state.record_fact("total_debt", state.total_debt)
    return state
```

### Node 2: Deterministic Covenant Auditing via Z3 SMT Solver
Next, evaluate covenants deterministically and prove compliance via the `SuvarnaEngine` (Z3 SMT theorem prover):

```python
from lilavati.core.invariants import SuvarnaEngine


def covenant_audit_node(state: CreditUnderwritingState) -> CreditUnderwritingState:
    """Node 2: Deterministically evaluates debt covenants and verifies via Z3 SMT solver."""
    state.leverage_ratio = state.total_debt / state.ebitda
    state.interest_coverage = state.ebitda / state.interest_expense

    # Formally prove debt covenant satisfiability using Z3 SMT solver
    suvarna = SuvarnaEngine()
    cov_result = suvarna.verify_debt_covenant(
        total_debt=state.total_debt,
        cash=0.0,
        ebitda=state.ebitda,
        max_leverage_covenant=state.max_leverage_covenant,
        min_interest_coverage_covenant=state.min_coverage_covenant,
        interest_expense=state.interest_expense,
    )

    state.covenant_satisfied = cov_result.is_valid

    # If in breach, calculate exact required sponsor equity cure
    if not cov_result.is_valid:
        max_allowable_debt = state.max_leverage_covenant * state.ebitda
        state.required_equity_cure_usd = state.total_debt - max_allowable_debt
    else:
        state.required_equity_cure_usd = 0.0

    return state
```

### Node 3: Structural Credit Risk Modeling (Merton Model)
Calculate distance-to-default and physical default probability using options pricing theory:

```python
from lilavati.core.fixed_income import FixedIncomeEngine


def structural_credit_risk_node(state: CreditUnderwritingState) -> CreditUnderwritingState:
    """Node 3: Calculates Merton structural default probability using quantitative options pricing."""
    risk_free_rate = 0.045  # 4.5% Treasury yield
    time_horizon = 1.0  # 1-year tenor

    # Solve Merton non-linear simultaneous equations
    merton_res = FixedIncomeEngine.solve_merton_model(
        equity_value=state.equity_value,
        equity_volatility=state.equity_volatility,
        debt_face_value=state.total_debt,
        risk_free_rate=risk_free_rate,
        maturity_years=time_horizon,
    )

    state.merton_default_probability = merton_res.default_probability

    # Synthesize underwriting decision
    if state.covenant_satisfied and state.merton_default_probability < 0.05:
        state.underwriting_verdict = "APPROVED: Robust solvency & covenants verified."
    elif not state.covenant_satisfied:
        state.underwriting_verdict = (
            f"REJECTED_COVENANT_BREACH: Leverage ({state.leverage_ratio:.2f}x) exceeds limit "
            f"({state.max_leverage_covenant:.2f}x). Requires ${state.required_equity_cure_usd:.1f}M equity cure."
        )
    else:
        state.underwriting_verdict = "FLAGGED_FOR_REVIEW: Elevating credit risk."

    return state
```

---

## Step 3: Assemble & Compile the Graph

Compose the nodes into a Directed Acyclic Graph (DAG) using `FinancialStateGraph`:

```python
from lilavati.framework import END, FinancialStateGraph


def build_underwriting_agent() -> FinancialStateGraph[CreditUnderwritingState]:
    """Constructs and compiles the FinancialStateGraph."""
    builder = FinancialStateGraph(CreditUnderwritingState)

    # Register nodes
    builder.add_node("ingest", ingest_and_provenance_node)
    builder.add_node("covenant_audit", covenant_audit_node)
    builder.add_node("credit_risk", structural_credit_risk_node)

    # Define execution edges
    builder.set_entry_point("ingest")
    builder.add_edge("ingest", "covenant_audit")
    builder.add_edge("covenant_audit", "credit_risk")
    builder.add_edge("credit_risk", END)

    return builder
```

---

## Step 4: Execute the Agent Locally

Compile the graph into a `CompiledFinancialGraph` and invoke it with an initial state:

```python
# 1. Compile the graph
agent_graph = build_underwriting_agent().compile()

# 2. Test with a credit-worthy borrower
borrower_a = CreditUnderwritingState(
    borrower_name="Apex Logistics Inc",
    ebitda=100.0,
    total_debt=320.0,  # 3.20x leverage <= 4.0x
    interest_expense=15.0,
    equity_value=600.0,
)
result_a = agent_graph.invoke(borrower_a)

print(f"Borrower: {result_a.borrower_name}")
print(f"Leverage: {result_a.leverage_ratio:.2f}x")
print(f"Covenant Status: {'SAT (Passed)' if result_a.covenant_satisfied else 'UNSAT'}")
print(f"Verdict: {result_a.underwriting_verdict}")
# Output: APPROVED: Robust solvency & covenants verified.

# 3. Test with a distressed borrower
borrower_b = CreditUnderwritingState(
    borrower_name="Stressed Retail Corp",
    ebitda=50.0,
    total_debt=275.0,  # 5.50x leverage > 4.0x
    interest_expense=18.0,
    equity_value=120.0,
)
result_b = agent_graph.invoke(borrower_b)

print(f"Borrower: {result_b.borrower_name}")
print(f"Leverage: {result_b.leverage_ratio:.2f}x")
print(f"Required Equity Cure: ${result_b.required_equity_cure_usd:.1f}M")
print(f"Verdict: {result_b.underwriting_verdict}")
# Output: REJECTED_COVENANT_BREACH: Leverage (5.50x) exceeds limit (4.00x). Requires $75.0M equity cure.
```

---

## Step 5: Write Automated Unit Tests with `pytest`

Institutional finance demands automated test coverage. Create a test file `tests/test_credit_agent.py`:

```python
from lilavati.framework import FinancialStateGraph


def test_credit_underwriting_agent_covenant_pass() -> None:
    graph = build_underwriting_agent().compile()

    state = CreditUnderwritingState(
        borrower_name="Test Company",
        ebitda=50.0,
        total_debt=150.0,  # 3.0x leverage
        interest_expense=10.0,  # 5.0x coverage
    )
    result = graph.invoke(state)

    assert result.leverage_ratio == 3.0
    assert result.covenant_satisfied is True
    assert result.required_equity_cure_usd == 0.0
    assert "APPROVED" in result.underwriting_verdict
    assert len(result.citations) >= 2


def test_credit_underwriting_agent_covenant_breach() -> None:
    graph = build_underwriting_agent().compile()

    state = CreditUnderwritingState(
        borrower_name="Breached Company",
        ebitda=50.0,
        total_debt=250.0,  # 5.0x leverage > 4.0x limit
        interest_expense=10.0,
    )
    result = graph.invoke(state)

    assert result.leverage_ratio == 5.0
    assert result.covenant_satisfied is False
    assert result.required_equity_cure_usd == 50.0  # 250 - (4.0 * 50) = 50
    assert "REJECTED_COVENANT_BREACH" in result.underwriting_verdict
```

Run the tests:
```bash
uv run pytest tests/test_credit_agent.py
```

---

## Step 6: Convert the Agent into a Production REST API

Līlāvatī provides built-in ASGI serving via `create_agent_api` and `serve_agent`. You can convert your compiled graph into a fully typed FastAPI REST microservice in **one line of code**:

```python
from lilavati.framework import create_agent_api, serve_agent

# 1. Compile your agent graph
agent_graph = build_underwriting_agent().compile()

# 2. Create the FastAPI ASGI application
app = create_agent_api(
    graph=agent_graph,
    title="Institutional Credit Underwriting API",
    description="Automated credit covenant and structural distress underwriting service.",
    version="1.0.0",
)

# 3. Serve in production with Uvicorn (binds to http://0.0.0.0:8000)
if __name__ == "__main__":
    serve_agent(agent_graph, host="0.0.0.0", port=8000)
```

### Auto-Generated Endpoints:
When launched, your service exposes:
* **`POST /api/v1/run`**: Accepts any valid JSON state payload, validates schema, executes graph nodes and SMT gates, and returns the audited state.
* **`GET /api/v1/health`**: Returns system health, version, registered graph nodes, and entry point.
* **`GET /api/v1/schema`**: Returns the full JSON schema of the state container.
* **`GET /docs`**: Interactive Swagger UI documentation.

### Querying the API via `curl`:
```bash
curl -X POST "http://localhost:8000/api/v1/run" \
     -H "Content-Type: application/json" \
     -d '{
       "borrower_name": "Acme Holdings",
       "ebitda": 120.0,
       "total_debt": 360.0,
       "interest_expense": 20.0,
       "equity_value": 750.0
     }'
```

**JSON Response:**
```json
{
  "borrower_name": "Acme Holdings",
  "fiscal_year": 2026,
  "ebitda": 120.0,
  "total_debt": 360.0,
  "leverage_ratio": 3.0,
  "interest_coverage": 6.0,
  "covenant_satisfied": true,
  "merton_default_probability": 0.0001,
  "required_equity_cure_usd": 0.0,
  "underwriting_verdict": "APPROVED: Robust solvency & covenants verified.",
  "is_valid": true,
  "citations": [
    {
      "doc_hash": "a7c8e9b01234567890abcdef1234567890abcdef1234567890abcdef12345678",
      "filing_type": "Credit-Agreement",
      "page": 24,
      "raw_snippet": "Adjusted Consolidated EBITDA: $120.0M"
    }
  ]
}
```

---

## 🚀 Running the Full Tutorial Example

A complete, executable script of this tutorial is included in the repository:

```bash
uv run python examples/06_build_custom_agent_and_api.py
```

---

## 🧭 Summary & Key Architectural Takeaways

| Feature | Generic LLM Agent Frameworks | Project Līlāvatī Agent |
| :--- | :--- | :--- |
| **Arithmetic** | Stochastic token generation (mental math hallucinations) | Deterministic Python & C++ engines (Zero LLM Math) |
| **Covenant Logic** | Soft prompt instructions ("check if debt/ebitda < 4") | Theorem-proven formal SMT solver (`SuvarnaEngine`) |
| **Auditing & Provenance** | None or unverified URLs | Cryptographic `CitationRef` with SHA-256 hashes |
| **Deployment** | Manual boilerplate integration | One-line FastAPI microservice creation (`create_agent_api`) |
