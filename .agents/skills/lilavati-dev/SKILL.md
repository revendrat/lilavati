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
      filing_date: str = Field(..., description="ISO 8601 date of publication")
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

## 2. Directory Layout & Where to Place Code

| Component | Target Directory | Description |
| :--- | :--- | :--- |
| **Core Primitives** | `src/lilavati/core/` | Invariants (Z3), provenance (`CitationRef`), bi-temporal DuckDB engine, DAG graph. |
| **Canonical Schemas** | `src/lilavati/schemas/` | Pydantic V2 models for statements, fixed income, options, econometrics, and execution. |
| **FastMCP Servers** | `src/lilavati/mcp_servers/` | Standalone FastMCP microservices (`fixed_income.py`, `econometrics.py`, etc.). |
| **Financial Skills** | `src/lilavati/skills/` | Composable playbooks (`SKILL.md` + Python scripts + schemas). |
| **Role-Bound Agents** | `src/lilavati/agents/` | Multi-agent orchestration loops (Bull, Bear, Credit, Auditor). |
| **Līlāvatī-Bench** | `src/lilavati/bench/` | Evaluation tracks, datasets, and scoring metrics (PoCS, ICR, TPI). |
| **Tests** | `tests/` | Pytest suites matching module hierarchy. |

---

## 3. Tooling & Verification Workflow for Agents

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

## 4. Example: Writing a Deterministic Financial Skill

When creating a new financial skill (e.g., in `src/lilavati/skills/beneish_m_score/`):

1. **`schemas.py`:** Define strict Pydantic inputs and outputs, requiring citations.
2. **`calculator.py`:** Write pure, typed Python/Polars calculation logic.
3. **`SKILL.md`:** Document the financial theory, mathematical formula, inputs, outputs, and edge cases.
4. **`test_skill.py`:** Test against a verified real-world filing (e.g., Enron 2000 10-K vs. non-manipulator firm).

---

## 5. Anti-Patterns to Avoid

❌ **DO NOT** use `float` for currency where precision matters; use `Decimal` or scaled integers if exact cents are required.  
❌ **DO NOT** use `pandas` where `polars` can be used for high-performance vectorized operations.  
❌ **DO NOT** suppress type errors with `# type: ignore` unless strictly necessary for external untyped libraries (like C-extensions in QuantLib).  
❌ **DO NOT** write unit tests that mock the entire calculation logic. Test real mathematical functions against known ground truths.  
❌ **DO NOT** hardcode SEC EDGAR URLs without user-agent headers compliant with SEC fair-access policies.

