# Project Līlāvatī: Development Roadmap & Task Validation Protocol

> *"As a drop of water on a lotus leaf shines like a pearl... so does true knowledge when firmly established in rigor."*
> — **Bhāskarācārya**, *Līlāvatī*

This document defines the official engineering roadmap, granular task list, and validation protocol for **Project Līlāvatī**. It serves as our shared source of truth during development.

---

## 🚦 Task Validation & Approval Protocol ("Definition of Done")

Every roadmap task must pass a strict 5-stage quality gate before being marked as **Completed (`[x]`)**:

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│ 1. Spec & Types │ ──► │ 2. Deterministic │ ──► │ 3. Automated Unit  │
│ (Pydantic V2)   │     │    Execution     │     │    Tests (pytest)  │
└─────────────────┘     └──────────────────┘     └─────────┬──────────┘
                                                           │
┌─────────────────┐     ┌──────────────────┐               │
│ 5. Commit, Push │ ◄── │ 4. Strict Linter │ ◄─────────────┘
│    & Sign-off   │     │    & Type Check  │
└─────────────────┘     └──────────────────┘
```

1. **Stage 1: Specification & Schemas:**
   * Canonical Pydantic V2 data contracts defined with frozen immutability.
   * `CitationRef` provenance mandatory for extracted data.
2. **Stage 2: Deterministic Execution (Zero LLM Arithmetic):**
   * Calculations implemented in Polars, DuckDB, SciPy, Statsmodels, or QuantLib.
   * Zero stochastic LLM math in prompts or response text.
3. **Stage 3: Automated Mathematical Verification (`pytest`):**
   * Unit tests comparing output against audited reference values (textbooks, FRED, SEC filings).
   * Edge-case boundary tests (zero divisions, negative rates, extreme volatility).
   * SMT invariant satisfiability checking via `SuvarnaEngine` (Z3).
4. **Stage 4: Code Quality Gates:**
   * Linting: `uv run ruff check .` (zero warnings).
   * Formatting: `uv run ruff format .`.
   * Type Safety: `uv run mypy src/ --strict` (zero type errors).
5. **Stage 5: Collaborative Sign-off & Git Push:**
   * Milestone summarized with test coverage and verification output.
   * Atomic Conventional Commit (`feat(...)`, `fix(...)`, `bench(...)`) pushed to `origin/main`.
   * Approved by project lead.

---

## 🗺️ Phased Roadmap & To-Do List

### Phase 0: Foundations, Invariants & Core Engines (Status: COMPLETED ✅)
- [x] **0.1 Project Scaffolding:** `pyproject.toml` with `uv`, Apache 2.0 License, `CITATION.cff`.
- [x] **0.2 Contributor & PR Guidelines:** `CONTRIBUTING.md` with Conventional Commits and PR checklist.
- [x] **0.3 AI Coding Agent Skill:** `.agents/skills/lilavati-dev/SKILL.md` enforcing zero math hallucinations.
- [x] **0.4 Cryptographic Provenance Engine:** `CitationRef` and `SourcedValue` with SHA-256 document hashing.
- [x] **0.5 Suvarṇa Z3 Formal Invariant Engine:** First-order logic verification for 3-statement balance and debt covenants.
- [x] **0.6 Financial Econometrics Suite:** ADF unit root test, Johansen cointegration, OU half-life, and GARCH(1,1).
- [x] **0.7 FastMCP Econometrics Server:** Exposes stationarity, cointegration, and GARCH tools over FastMCP.
- [x] **0.8 Financial Machine Learning Suite:** Fractional differentiation ($d^*$) and Triple-Barrier path-dependent labeling.
- [x] **0.9 FastMCP Financial ML Server:** Exposes fractional differentiation and triple-barrier tools over FastMCP.
- [x] **0.10 Fixed Income & Credit Risk Suite:** Bond pricing (Duration, Convexity, DV01), Nelson-Siegel yield curves, and Merton default model.
- [x] **0.11 FastMCP Fixed Income Server:** Exposes bond analytics, yield curve fitting, and Merton credit risk.
- [x] **0.12 Reactive Financial Computation Graph:** `StatementGraph` DAG propagating driver shocks with Z3 validation.
- [x] **0.13 Sustainable Finance & Climate Risk Suite:** Carbon WACI, carbon tax transition stress testing, and SLB covenants.
- [x] **0.14 FastMCP Sustainability Server:** Exposes WACI, carbon tax stress testing, and SLB covenant tools.
- [x] **0.15 Verification:** 36 automated unit tests passing with strict mypy typing.

---

### Phase 1: Real-World Ingestion & Bi-Temporal Connectors (Status: COMPLETED ✅)
*Goal: Connect the engine to live, real-world corporate filings and macroeconomic data feeds without look-ahead bias.*

- [x] **1.1 SEC EDGAR XBRL / Company Facts Connector:**
  * Pulls live company filings (10-K, 10-Q) from SEC EDGAR API with compliant User-Agent headers.
  * Parses standardized `us-gaap` taxonomy line items into canonical `ThreeStatementModel`.
  * Generates cryptographic `CitationRef` for every parsed fact.
  * *Validation:* Parse Apple (AAPL) and Microsoft (MSFT) latest 10-K and verify $Assets = Liabilities + Equity$.
- [x] **1.2 Market & Macro Series Connector:**
  * Async connector for historical OHLCV data (daily and intraday bars) normalized to Polars DataFrames.
  * Federal Reserve Economic Data (FRED) connector for SOFR, Treasury yields, CPI, and Fed Funds rate.
  * *Validation:* Fetch 5-year Treasury constant maturity series and verify Nelson-Siegel fit.
- [x] **1.3 India BSE/NSE Ind AS Corporate Filings Connector:**
  * Ingestion wrapper for Indian corporate disclosures and MCA Ind AS taxonomy filings.
  * Entity Taxonomy Reconciliation Engine (ETRE) mapping Ind AS terms to canonical `ChartOfAccounts`.
  * *Validation:* Parse Reliance Industries or Infosys annual report balance sheet with 100% reconciliation.
- [x] **1.4 Bi-Temporal DuckDB Local Data Warehouse:**
  * DuckDB storage layer implementing dual-time indexing: `valid_time` (period described) vs `as_of_timestamp` (filing date).
  * Enforces temporal filters preventing look-ahead leakage in historical backtests.
  * *Validation:* Query historical filing before and after an 8-K/restatement; verify restatement is invisible at $T_0$.

---

### Phase 2: Derivatives, Volatility Surfaces & Risk Engine (Status: COMPLETED ✅)
*Goal: Institutional derivatives pricing, volatility surface modeling, and multi-asset Greeks risk.*

- [x] **2.1 Option Pricing Suite:**
  * Analytical Black-Scholes-Merton for European options with continuous dividend yield.
  * Cox-Ross-Rubinstein (CRR) binomial tree for American early-exercise options.
  * Inversion engine solving for Black-Scholes implied volatility.
- [x] **2.2 Volatility Surface Calibration:**
  * Calibrate SABR model ($\alpha, \beta, \rho, \nu$) to market option chains.
  * SMT arbitrage-free verification: formal verification of butterfly spread convexity via Z3.
- [x] **2.3 First- & Second-Order Greeks Hedging:**
  * Real-time calculation of Delta ($\Delta$), Gamma ($\Gamma$), Vega ($\mathcal{V}$), Theta ($\Theta$), Rho ($\rho$), Vanna ($\frac{\partial \Delta}{\partial \sigma}$), and Volga ($\frac{\partial \mathcal{V}}{\partial \sigma}$).
- [x] **2.4 FastMCP Derivatives Server:**
  * Exposes `price_european_option`, `price_american_option`, `calculate_option_greeks`, `calibrate_sabr_volatility_model`, and `check_butterfly_arbitrage`.
- [x] **2.5 Verification:** 54 automated unit tests passing across all pricing models, Put-Call parity, and arbitrage constraints.

---

### Phase 3: Trading Microstructure, Execution & Portfolio Optimization (Status: COMPLETED ✅)
*Goal: Order book dynamics, optimal execution scheduling, and robust portfolio allocation.*

- [x] **3.1 Limit Order Book (LOB) Reconstruction:**
  * L1/L2 order book depth processing, bid-ask spread decomposition, and Order Flow Imbalance (OFI).
  * Volume-weighted microprice calculation and crossed-book guards.
- [x] **3.2 Optimal Execution Algorithms:**
  * **Almgren-Chriss Optimal Liquidation:** Analytical solver balancing permanent/temporary market impact and volatility risk.
  * Deterministic calculation of trajectory, trade slices, expected shortfall, and execution variance.
- [x] **3.3 Institutional Portfolio Optimization:**
  * **Black-Litterman Allocation:** Bayesian blending of passive market equilibrium priors with agent subjective views ($P, Q, \Omega$) solved via `cvxpy`.
  * **Hierarchical Risk Parity (HRP):** Dendrogram clustering on correlation distance matrices, avoiding matrix inversion singularities.
- [x] **3.4 FastMCP Portfolio & Execution Server:**
  * Exposes `analyze_order_book_microstructure`, `compute_almgren_chriss_liquidation_schedule`, `optimize_portfolio_black_litterman`, and `optimize_portfolio_hierarchical_risk_parity`.
- [x] **3.5 Verification:** 63 automated unit tests passing across execution trajectories and allocation algorithms.

---

### Phase 4: Multi-Agent Orchestration & The Adversarial Committee (Status: COMPLETED ✅)
*Goal: Role-bound agent loops debating investment theses under formal verification guardrails.*

- [x] **4.1 Role-Bound Financial Agents & Forensics:**
  * **Forensic Credit & Accounting Auditor:** Complete 8-variable Beneish M-Score manipulation detector and Altman Z-Score distress predictor.
  * **Thematic Bull Analyst:** Revenue growth drivers, operating income trajectories, and target models.
- [x] **4.2 The Adversarial Investment Committee Protocol:**
  * Deliberative multi-turn protocol: Bull presents thesis; Forensic Bear stress-tests earnings quality and receivables.
  * Mandatory Z3 formal verification gate (`SuvarnaEngine`) before emitting the binding `InvestmentCommitteeMemo`.
- [x] **4.3 FastMCP Committee Server:**
  * Exposes `evaluate_investment_committee_memo` and `compute_forensic_beneish_m_score` over FastMCP.
- [x] **4.4 Centralized Institutional Prompts Catalog (`src/lilavati/prompts/`):**
  * Core system prompt enforcing Zero LLM Arithmetic, SMT Invariant compliance, and Cryptographic Provenance.
  * Role-bound prompt templates: Bull Researcher, Forensic Bear, Sustainability Specialist, and Portfolio Manager.
  * Neuro-symbolic SMT reflection and citation rejection prompt generators.
- [x] **4.5 Multi-Provider LLM Client Adapter (`src/lilavati/llm/`):**
  * Multi-model abstraction supporting Google DeepMind Gemini, Anthropic Claude, OpenAI, and local OSS financial models (via vLLM / Ollama).
  * FastMCP tool schema binding, function calling, and Pydantic structured output validation.
- [x] **4.6 Neuro-Symbolic Agent Runtime & Reflection Loop (`src/lilavati/runtime/`):**
  * Autonomous execution loop: LLM planning -> sandboxed tool execution -> Z3 formal invariant check -> unsatisfiable core reflection loop -> verified synthesis.
- [x] **4.7 Institutional Tracing & OpenTelemetry Audit Trail (`src/lilavati/tracing/`):**
  * OpenTelemetry-compatible span models capturing agent runs, model calls, tool executions, SMT verification results, and citation checks.
  * Immutable JSONL audit trail exporter and compliance summaries.
- [x] **4.8 Institutional Tracing & OpenTelemetry Audit Trail (`src/lilavati/tracing/`):**
  * OpenTelemetry-compatible span models capturing agent runs, model calls, tool executions, SMT verification results, and citation checks.
  * Immutable JSONL audit trail exporter and compliance summaries.
- [x] **4.9 Advanced Autonomous Financial Agents (Search, Deep, Research) (`src/lilavati/agents/`):**
  * **FinancialSearchAgent:** Autonomous multi-source discovery across SEC EDGAR, India BSE/NSE Ind AS, and macro feeds with SHA-256 cryptographic provenance.
  * **DeepFinancialAgent:** Deep reasoning hypothesis tree search (Bull, Base, Bear) evaluated through reactive DAGs and Z3 SMT invariant pruning.
  * **FinancialResearchAgent:** End-to-end equity and credit research dossier synthesis integrating filing retrieval, forensic audits, deep scenario trees, and carbon WACI.
- [x] **4.10 Verification:** 88 automated unit tests passing across multi-role committee deliberation, model connectivity, tracing, runtime loops, and advanced agents.

---

### Phase 5: Līlāvatī-Bench (The Financial Agent Benchmark Suite) (Status: COMPLETED ✅)
*Goal: The definitive evaluation suite testing autonomous financial agents and domain LLMs.*

- [x] **5.1 Golden Benchmark Dataset Curation:**
  * 7 authoritative reference test cases across all foundational quantitative tracks with statutory SHA-256 document hashes.
  * Point-in-time cutoff dates enforced for every scenario.
- [x] **5.2 Automated Benchmark Runners across 7 Tracks:**
  * Track 1: Three-Statement Dynamic Reconciliation under Revenue Shock (Z3 SMT verified).
  * Track 2: Corporate Bond Duration, Convexity, and Structural Merton Default Probability.
  * Track 3: Econometric Rigor (ADF unit root testing & Engle-Granger Cointegration).
  * Track 4: Financial ML Methodological Soundness (Fractional differentiation $d^*$ and memory preservation).
  * Track 5: Derivatives & Volatility Arbitrage Invariance (BSM Greeks & SMT Butterfly Spread check).
  * Track 6: Market Microstructure & Optimal Execution (LOB Microprice, Spread, and Almgren-Chriss schedule).
  * Track 7: Sustainable Finance & Climate Stress Testing (Portfolio WACI & SLB coupon step-up check).
- [x] **5.3 Quantitative Metric Evaluators:**
  * **Proof-of-Citation Score (PoCS):** Evaluates SHA-256 statutory hash links and page/snippet verification.
  * **Accounting Invariant Compliance Rate (ICR):** Formally evaluated via Z3 SMT solver.
  * **Temporal Purity Index (TPI):** Detects look-ahead leakage and post-dated disclosure access.
  * **Tool Math Purity Ratio (TMPR):** Measures percentage of computations run through deterministic sandboxes vs mental math.
  * **Composite Līlāvatī Index:** Weighted institutional benchmark score (0-100).
- [x] **5.4 Public Leaderboard & Reproduction CLI:**
  * `lilavati-bench` command-line executable with `run` and `list-cases` subcommands.
  * Generates publication-ready Markdown tables, Rich terminal graphics, and JSON artifacts.
- [x] **5.5 Verification:** Reference solver passes 100.0% across all 7 tracks with full cryptographic citations.

---

### Phase 6: Academic Pre-Prints, Open-Source Launch & Community (Status: COMPLETED ✅)
*Goal: Academic recognition, peer-reviewed pre-prints, and viral open-source adoption.*

- [x] **6.1 Academic Pre-Print 1 (Framework Paper):**
  * *"Līlāvatī: A Neuro-Symbolic Agentic Framework for Institutional Financial Reasoning"*
  * Structured pre-print draft delivered at `docs/papers/01_framework_paper.md` (Target: arXiv q-fin / NeurIPS / ACM ICAIF).
- [x] **6.2 Academic Pre-Print 2 (Benchmark Paper):**
  * *"Līlāvatī-Bench: Stress-Testing Financial LLMs and Agents on Accounting Invariants and Look-Ahead Bias"*
  * Structured benchmark paper draft delivered at `docs/papers/02_benchmark_paper.md` (Target: Journal of Financial Data Science).
- [x] **6.3 Documentation & Interactive Tutorials:**
  * MkDocs Material documentation website (`mkdocs.yml`, `docs/index.md`, `docs/architecture.md`, `docs/benchmarks.md`).
  * 4 executable institutional tutorial scripts in `examples/`:
    1. `examples/01_three_statement_reconciliation.py`: Dynamic StatementGraph shock & SMT verification.
    2. `examples/02_statistical_arbitrage_pairs.py`: Engle-Granger cointegration, OU half-life, and GARCH.
    3. `examples/03_climate_risk_stress_test.py`: Portfolio WACI, shadow carbon tax, and SLB covenants.
    4. `examples/04_autonomous_agent_tracing.py`: Full agent loop with OpenTelemetry tracing and JSONL audit export.
- [x] **6.4 Community Launch Readiness:**
  * Ready for public release on GitHub, Hugging Face Spaces leaderboard, Hacker News, and FINOS.

