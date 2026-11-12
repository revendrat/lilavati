---
name: lilavati-dev
description: Institutional developer guidelines, mathematical rigor standards, and code generation rules for AI coding agents working on Project Līlāvatī.
---

# Līlāvatī AI Developer Skill (`lilavati-dev`)

This skill is designed for **AI coding assistants and autonomous developer agents** (Claude Code, Cursor, Codex, Antigravity, etc.) contributing to **Project Līlāvatī** (`lilavati`).

When working on this repository, you are not writing a generic web application or simple script. You are contributing to an **institutional financial runtime** where precision, provenance, and zero-arithmetic guarantees are paramount.

---

## 1. Non-Negotiable Rules for Coding Agents

### Rule 1: Zero LLM Arithmetic
* **NEVER** write code where an LLM is expected to compute financial math (DCF, CAGR, bond yields, beta, ratios) directly within its prompt or generated text.
* **ALWAYS** write deterministic calculation functions (in Polars, DuckDB, NumPy, SciPy, or QuantLib) and expose them as FastMCP tools or skills.
* The LLM's only role in quantitative tasks is **parameter extraction and tool dispatching**.

### Rule 2: Cryptographic Provenance (`CitationRef`)
* Any schema that represents extracted financial disclosures must include `CitationRef`:
  ```python
  from pydantic import BaseModel, Field


  class CitationRef(BaseModel):
      doc_hash: str = Field(..., description="SHA-256 hash of the source document")
      filing_date: date = Field(..., description="Date of publication")
      period_end: date = Field(..., description="Fiscal period end date (Valid Time)")
      page: int = Field(..., ge=1, description="1-based page number")
      table_id: str | None = Field(None, description="Identifier of the extracted table")
      xbrl_tag: str | None = Field(None, description="Standard or extension XBRL taxonomy tag")
      raw_snippet: str = Field(..., description="Verbatim raw text or cell value")
  ```

### Rule 3: Bi-Temporal Point-in-Time (PIT) Queries
* When writing data retrieval functions, always parameterize queries with both:
  1. `period_end` (Valid Time: the financial period being reported)
  2. `as_of_timestamp` (System Time: the moment the data became publicly known)
* Never allow an agent to query data filed *after* the `as_of_timestamp`.

### Rule 4: Formal Verification via SMT (`z3-solver`)
* Balance sheets, debt waterwalls, and option surfaces must be verified against formal constraints.
* For three-statement models, verify:
  $$\text{Assets} = \text{Liabilities} + \text{ShareholdersEquity}$$
  $$\Delta \text{Cash} = \text{CashFromOperations} + \text{CashFromInvesting} + \text{CashFromFinancing}$$
* Use `z3` to verify that constraints are satisfiable (`sat`). If `unsat`, extract the unsatisfiable core to guide agent self-correction.

### Rule 5: Marcos López de Prado Financial ML Standards
* **Never** use naive integer differencing ($d=1$) on price series without testing fractional differentiation ($d^*$).
* **Never** use standard k-fold cross-validation on time series. Always use **Purged & Embargoed Cross-Validation**.
* **Never** use naive next-day price signs for labels. Use the **Triple-Barrier Method** (take-profit, stop-loss, max holding horizon).

---

## 2. Directory Layout & Available Core Engines

| Component | Module Path | Implemented Capabilities |
| :--- | :--- | :--- |
| **Provenance** | `src/lilavati/core/provenance.py` | `CitationRef`, `SourcedValue`, SHA-256 document hashing. |
| **Invariants (Z3)** | `src/lilavati/core/invariants.py` | `SuvarnaEngine`: 3-statement balance check, cash flow delta, debt covenants. |
| **Econometrics** | `src/lilavati/core/econometrics.py` | `EconometricEngine`: ADF stationarity, Johansen cointegration, OU half-life, GARCH(1,1). |
| **Financial ML** | `src/lilavati/core/financial_ml.py` | `FinancialMLEngine`: Fractional differentiation ($d^*$), Triple-Barrier labeling. |
| **Fixed Income** | `src/lilavati/core/fixed_income.py` | `FixedIncomeEngine`: Bond pricing, Nelson-Siegel curves, Merton default model. |
| **Statement DAG** | `src/lilavati/core/graph.py` | `StatementGraph`: Reactive 3-statement DAG with driver shocks and Z3 verification. |
| **Sustainability** | `src/lilavati/core/sustainability.py` | `SustainabilityEngine`: WACI, carbon tax transition stress testing, SLB step-up covenants. |
| **Bi-Temporal DB** | `src/lilavati/core/temporal.py` | `BiTemporalWarehouse`: DuckDB dual-time queries eliminating look-ahead bias. |
| **SEC EDGAR** | `src/lilavati/connectors/edgar.py` | `EdgarClient`: SEC XBRL facts extraction into `ThreeStatementModel` with citations. |
| **Market Data** | `src/lilavati/connectors/market_data.py` | `MarketDataClient`: Polars-vectorized OHLCV returns and Treasury yield term structures. |
| **India Ind AS** | `src/lilavati/connectors/india_filings.py` | `IndiaFilingsClient`: MCA / BSE / NSE Ind AS XBRL crosswalk and ETRE engine. |
| **Derivatives & Greeks** | `src/lilavati/core/derivatives.py` | `DerivativesEngine`: BSM European, CRR American, 1st & 2nd order Greeks, SABR calibration, butterfly arbitrage. |
| **Execution & Portfolio** | `src/lilavati/core/execution.py` | `ExecutionEngine`: LOB microstructure (OFI, microprice), Almgren-Chriss liquidation, Black-Litterman, HRP. |
| **Forensics & Committee** | `src/lilavati/agents/committee.py` | `AdversarialCommittee` & `ForensicEngine`: Beneish M-Score, Altman Z-Score, multi-role investment memo. |
| **Search Agent** | `src/lilavati/agents/search.py` | `FinancialSearchAgent`: Autonomous discovery across SEC EDGAR, Ind AS, and FRED with SHA-256 provenance. |
| **Deep Agent** | `src/lilavati/agents/deep.py` | `DeepFinancialAgent`: Hypothesis tree exploration (Bull/Base/Bear) with Z3 SMT invariant branch pruning. |
| **Research Agent** | `src/lilavati/agents/research.py` | `FinancialResearchAgent`: End-to-end investment research dossier with forensic and climate auditing. |
| **Prompts Catalog** | `src/lilavati/prompts/` | Institutional system instructions, Bull/Bear/Sustainability prompts, and SMT reflection generators. |
| **LLM Adapter** | `src/lilavati/llm/` | `UniversalLLMClient` multi-provider connectivity (Gemini, Claude, OpenAI, vLLM, Ollama) with FastMCP tool binding. |
| **Tracing & Telemetry** | `src/lilavati/tracing/` | `Tracer` & `TraceSpan`: OpenTelemetry-compatible spans, JSONL audit trails, and compliance summaries. |
| **Agent Runtime** | `src/lilavati/runtime/` | `NeuroSymbolicAgent`: Autonomous loop with FastMCP sandboxed tools and Z3 SMT self-correction reflection. |
| **Benchmark Suite** | `src/lilavati/bench/` | `Līlāvatī-Bench`: 7 quantitative tracks, PoCS, ICR, TPI, TMPR evaluators, and `lilavati-bench` CLI. |

---

## 3. FastMCP Microservices Registry

Every engine is exposed as a standalone FastMCP server in `src/lilavati/mcp_servers/`:

1. **`econometrics_server.py`:** `analyze_stationarity`, `analyze_cointegration`, `fit_garch_volatility`.
2. **`financial_ml_server.py`:** `find_optimal_fractional_diff`, `apply_triple_barrier_labels`.
3. **`fixed_income_server.py`:** `analyze_bond`, `fit_yield_curve`, `evaluate_credit_risk_merton`.
4. **`sustainability_server.py`:** `calculate_portfolio_carbon_intensity`, `stress_test_carbon_tax_impact`, `evaluate_sustainability_linked_bond_covenant`.
5. **`corporate_filings_server.py`:** `get_company_filing_statements`, `extract_single_line_item`.
6. **`derivatives_server.py`:** `price_european_option`, `price_american_option`, `calculate_option_greeks`, `calibrate_sabr_volatility_model`, `check_butterfly_arbitrage`.
7. **`portfolio_exec_server.py`:** `analyze_order_book_microstructure`, `compute_almgren_chriss_liquidation_schedule`, `optimize_portfolio_black_litterman`, `optimize_portfolio_hierarchical_risk_parity`.
8. **`committee_server.py`:** `evaluate_investment_committee_memo`, `compute_forensic_beneish_m_score`.

---

## 4. Tooling & Verification Workflow for Agents

When implementing features or fixing bugs, execute the following validation cycle:

```bash
# 1. Run tests for the modified module
uv run pytest tests/path_to_test.py -v

# 2. Check formatting and linting
uv run ruff check . --fix
uv run ruff format .

# 3. Verify strict type checking
uv run mypy src/
```

---

## 5. Anti-Patterns to Avoid

❌ **DO NOT** use `float` for currency where exact cents are required; use `Decimal` or scaled integers.  
❌ **DO NOT** use `pandas` where `polars` can be used for high-performance vectorized operations.  
❌ **DO NOT** suppress type errors with `# type: ignore` unless strictly necessary for untyped C-extensions.  
❌ **DO NOT** write unit tests that mock the entire calculation logic. Test real mathematical functions against known ground truths.  
❌ **DO NOT** hardcode SEC EDGAR URLs without user-agent headers compliant with SEC fair-access policies.
