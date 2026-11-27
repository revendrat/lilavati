# Project Līlāvatī: Development Roadmap & Task Validation Protocol

> *"As a drop of water on a lotus leaf shines like a pearl... so does true knowledge when firmly established in rigor."*
> — **Bhāskarācārya**, *Līlāvatī*

This document defines the engineering roadmap, task list, and validation protocol for **Project Līlāvatī**. It is our shared source of truth during development.

**Current goal:** complete internal verification and validation (Phase 7) before any public announcement. Items below are marked `[x]` only when they exist in code with tests; anything weaker is marked partial (🟡) and explained.

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
   * Unit tests comparing output against independent reference values (textbook worked examples, original papers, or mature libraries such as QuantLib/statsmodels), cited in the test.
   * Edge-case boundary tests (zero divisions, negative rates, extreme volatility).
   * SMT invariant satisfiability checking via `SuvarnaEngine` (Z3).
4. **Stage 4: Code Quality Gates:**
   * Linting: `uv run ruff check .` (zero warnings).
   * Formatting: `uv run ruff format .`.
   * Type Safety: `uv run mypy src/ --strict` (zero type errors).
5. **Stage 5: Collaborative Sign-off & Git Push:**
   * Milestone summarized with test coverage and verification output.
   * Atomic Conventional Commit (`feat(...)`, `fix(...)`, `bench(...)`).
   * Approved by project lead before push.

---

## 🗺️ Phased Roadmap & To-Do List

### Phase 0: Foundations, Invariants & Core Engines (Status: IMPLEMENTED — ALPHA)
- [x] **0.1 Project Scaffolding:** `pyproject.toml` with `uv`, Apache 2.0 License, `CITATION.cff`.
- [x] **0.2 Contributor & PR Guidelines:** `CONTRIBUTING.md` with Conventional Commits and PR checklist.
- [x] **0.3 AI Coding Agent Skill:** `.claude/skills/lilavati-dev/SKILL.md`: coding, testing and documentation rules for AI agents, updated as bugs reveal new patterns.
- [x] **0.4 Cryptographic Provenance Engine:** `CitationRef` and `SourcedValue` with SHA-256 document hashing.
- [x] **0.5 Suvarṇa Z3 Formal Invariant Engine:** First-order logic verification for 3-statement balance and debt covenants.
- [x] **0.6 Financial Econometrics Suite:** ADF unit root test, Engle-Granger cointegration, OU half-life, and GARCH(p,q).
- [x] **0.7 FastMCP Econometrics Server:** Exposes stationarity, cointegration, and GARCH tools over FastMCP.
- [x] **0.8 Financial Machine Learning Suite:** Fractional differentiation ($d^*$) and Triple-Barrier path-dependent labeling.
- [x] **0.9 FastMCP Financial ML Server:** Exposes fractional differentiation and triple-barrier tools over FastMCP.
- [x] **0.10 Fixed Income & Credit Risk Suite:** Bond pricing (Duration, Convexity, DV01), Nelson-Siegel yield curves, and Merton default model.
- [x] **0.11 FastMCP Fixed Income Server:** Exposes bond analytics, yield curve fitting, and Merton credit risk.
- [x] **0.12 Reactive Financial Computation Graph:** `StatementGraph` DAG propagating driver shocks with Z3 validation.
- [x] **0.13 Sustainable Finance & Climate Risk Suite:** Carbon WACI, carbon tax transition stress testing, and SLB covenants.
- [x] **0.14 FastMCP Sustainability Server:** Exposes WACI, carbon tax stress testing, and SLB covenant tools.
- [x] **0.15 Verification:** unit tests and strict mypy typing in CI (`pytest`, `ruff`, `mypy`).

---

### Phase 1: Real-World Ingestion & Bi-Temporal Connectors (Status: IMPLEMENTED — ALPHA)
*Goal: Connect the engine to live, real-world corporate filings and macroeconomic data feeds without look-ahead bias.*

- [x] **1.1 SEC EDGAR XBRL / Company Facts Connector:**
  * Pulls live company filings (10-K, 10-Q) from SEC EDGAR API with compliant User-Agent headers.
  * Parses standardized `us-gaap` taxonomy line items into canonical `ThreeStatementModel`.
  * Generates cryptographic `CitationRef` for every parsed fact.
  * *Validation:* filing-anchored extraction (`connectors/sec_filing.py`, MCP tool `get_filing_figures`) piloted on the latest 10-Ks of 5 companies (7.5, `docs/validation/connectors.md`); tests on verbatim SEC data. The `ThreeStatementModel` path uses the fiscal year's own 10-K, records derived fields and refuses filings missing required items (86 of 86 reported values found in 3 10-Ks; J&J and JPMorgan refused).
- [~] **1.2 Market & Macro Series Connector (🟡 partial):**
  * Implemented: OHLCV normalisation to Polars DataFrames and Nelson-Siegel fitting from supplied yield observations.
  * Not implemented: data fetching (OHLCV download, FRED connector for SOFR, Treasury yields, CPI, Fed Funds).
- [~] **1.3 India Ind AS Crosswalk (🟡 partial):**
  * Implemented: `IndiaFilingsClient.parse_ind_as_disclosure` maps Schedule III (Division II) line items, supplied by the caller, into the canonical `ThreeStatementModel`, with `derived` formulas, `not_reported` items and checks (balance sheet totals; Ind AS 7 cash reconciliation).
  * Reads NSE's Integrated Filing (Financial) page, supplied by the user (`connectors/nse_integrated_filing.py`, 2026-11-26; piloted on one filing, Tutorial 10). Not implemented: fetching from BSE, NSE or MCA (NSE's terms prohibit automated collection without consent), the XBRL instance itself, BRSR.
  * *Validation:* checked on Maruti Suzuki's audited consolidated results for FY2025-26, line by line against the printed statements (cost of goods sold, operating income, balance sheet and cash checks all hold; the exchange filing folds right-of-use assets into PP&E), plus a fictional disclosure for edge cases (`docs/validation/connectors.md`). 🟡 One company and year; no retrieval.
- [x] **1.4 Bi-Temporal DuckDB Local Data Warehouse:**
  * DuckDB storage layer implementing dual-time indexing: `valid_time` (period described) vs `as_of_timestamp` (filing date).
  * Enforces temporal filters preventing look-ahead leakage in historical backtests.
  * *Validation:* Query historical filing before and after an 8-K/restatement; verify restatement is invisible at $T_0$.
- [ ] **1.5 Pluggable PDF parser connectors (🗺️ planned):**
  * Today the 10-K PDF parser (`connectors/pdf_10k.py`) reads text with pypdf only, and its labels are Apple's.
  * Split text extraction from statement mapping: a small backend interface (page count, page lines or tables, document hash) so that the row matching, `missing_items` and checks run unchanged on any backend.
  * Backends as optional extras, chosen per call: pypdf (default), pdfplumber (tables), Docling or unstructured (layout), OCR for scanned filings (Tesseract), and hosted parsers (API keys from environment variables only). Record each backend's licence (PyMuPDF is AGPL) before adding it.
  * Label sets per issuer and per standard (US GAAP 10-K, Ind AS annual report) instead of Apple's labels in code.
  * Provenance: the citation records the backend and its version, since page text and row splits differ between backends.
  * *Validation:* each backend on the same filings (Apple's FY2026 10-K first, then other issuers and an Ind AS annual report), line by line against the printed statements, in `docs/validation/connectors.md`; backends that disagree on a value are reported, not averaged. A test that every backend gives the same figures on a shared fixture.

---

### Phase 2: Derivatives, Volatility Surfaces & Risk Engine (Status: IMPLEMENTED — ALPHA)
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
- [x] **2.5 Verification:** unit tests for pricing, put-call parity and arbitrage checks. Reference-value audit pending (Phase 7).

---

### Phase 3: Trading Microstructure, Execution & Portfolio Optimization (Status: IMPLEMENTED — ALPHA)
*Goal: Order book dynamics, optimal execution scheduling, and robust portfolio allocation.*

- [x] **3.1 Limit Order Book (LOB) Reconstruction:**
  * L1/L2 order book depth processing, bid-ask spread decomposition, and Order Flow Imbalance (OFI).
  * Volume-weighted microprice calculation and crossed-book guards.
- [x] **3.2 Optimal Execution Algorithms:**
  * **Almgren-Chriss Optimal Liquidation:** discrete-time solution of Almgren & Chriss (2000), with η̃ = η − γτ/2, prices in $ units via `arrival_price`, overflow-safe trajectory, expected cost and variance. Validated against the paper's Section 3.4 parameters and an independent numerical optimiser.
- [x] **3.3 Institutional Portfolio Optimization:**
  * **Black-Litterman Allocation:** Bayesian blending of passive market equilibrium priors with agent subjective views ($P, Q, \Omega$) solved via `cvxpy`.
  * **Hierarchical Risk Parity (HRP):** Dendrogram clustering on correlation distance matrices, avoiding matrix inversion singularities.
- [x] **3.4 FastMCP Portfolio & Execution Server:**
  * Exposes `analyze_order_book_microstructure`, `compute_almgren_chriss_liquidation_schedule`, `optimize_portfolio_black_litterman`, and `optimize_portfolio_hierarchical_risk_parity`.
- [x] **3.5 Verification:** unit tests across execution trajectories and allocation algorithms.

---

### Phase 4: Multi-Agent Orchestration & The Adversarial Committee (Status: IMPLEMENTED — ALPHA)
*Goal: Role-bound agent loops debating investment theses under formal verification guardrails.*

- [x] **4.1 Role-Bound Financial Agents & Forensics:**
  * **Forensic Credit & Accounting Auditor:** 8-variable Beneish (1999) M-Score (coefficients corrected and tested against the paper) and Altman Z-Score.
  * **Bull rule:** revenue growth against a target (the committee is rule-based; role prompts for model-based roles are in `prompts/committee.py`).
- [x] **4.2 The Adversarial Investment Committee Protocol:**
  * Rule-based: growth against a target; Beneish and Altman flags; balance-sheet (Z3) and cash identities on reported inputs; a failed identity rejects the memo. No model is called. A model-based committee is a Phase 11 research design ([agent workflows](docs/agent-workflows.md), workflow 5).
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
  * Autonomous execution loop: LLM planning -> sandboxed tool execution -> Z3 identity check -> reflection prompt with a diagnosis of which figures could be wrong (MaxSMT, from 2026-11-25) -> synthesis.
- [x] **4.7 Institutional Tracing & OpenTelemetry Audit Trail (`src/lilavati/tracing/`):**
  * OpenTelemetry-compatible span models capturing agent runs, model calls, tool executions, SMT verification results, and citation checks.
  * Immutable JSONL audit trail exporter and compliance summaries.
- [x] **4.8 Advanced Autonomous Financial Agents (Search, Deep, Research) (`src/lilavati/agents/`):**
  * **FinancialSearchAgent:** the latest SEC 10-K filed by an as-of date, five figures with citations; India not implemented; no macro feeds.
  * **DeepFinancialAgent:** three fixed (or supplied) scenarios on the statement graph, probability-weighted, pruning branches with negative cash or a closing balance sheet that does not balance; no model is called. The statement graph has no plug since 2026-11-27, so the balance check can fail.
  * **FilingExtractionAgent (2026-11-25):** a model reads figures with the lines they came from; quotes are checked against the document, identities diagnosed, and only the diagnosed figures re-read; it abstains on what it cannot settle. First real-model runs (five 10-Ks, four models on Groq, 2026-11-25): after fixing the quote check and a revenue label, 240 of 240 figures correct in one pass, so the repair is not yet measured; harder inputs next.
  * **FinancialResearchAgent:** dossier from one 10-K (latest filed by the as-of date): this year and the prior-year comparatives from the filing's own XBRL facts, the three-statement model with checks, the rule-based committee (Beneish, Altman, identities), a scenario tree calibrated from the filing (assumed multipliers, listed), carbon WACI only from supplied emissions, and every citation resolved against the SEC data read. Refuses when an input is not reported. Checked live on Apple, Microsoft, Walmart and Nvidia (2026-11-24); J&J refused.
- [x] **4.9 Verification:** unit tests across the committee, model connectivity, tracing, runtime loops (including scripted-model reflection with a diagnosis) and agents. Note: the default LLM is a mock; real-model agent runs are not yet part of the test suite.
- [ ] **4.10 Agent workflows ([docs/agent-workflows.md](docs/agent-workflows.md)):** extraction with diagnosis-driven repair (implemented; first real-model runs found no misreadings to repair on 10-K statements text; ablations on harder inputs open); covenant monitoring against guidance; answers with evidence (a gate on unsupported numbers); committee ladder (Phase 11).

---

### Phase 5: Līlāvatī-Bench (The Financial Agent Benchmark Suite) (Status: IMPLEMENTED — ALPHA)
*Goal: an evaluation suite for autonomous financial agents and domain LLMs.*

- [x] **5.1 Golden Benchmark Dataset Curation:**
  * 7 golden test cases (one per track). Their `doc_hash` values are hashes of source labels, not of real documents.
  * Seeded templated generator for 5 tracks with balanced True/False answers (content-free baseline: 15.7% vs 63.6% on golden cases).
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
  * **Proof-of-Citation Score (PoCS):** 🟡 currently checks hash membership only; page/snippet verification against real documents is planned.
  * **Accounting Invariant Compliance Rate (ICR):** Formally evaluated via Z3 SMT solver.
  * **Temporal Purity Index (TPI):** 🟡 compares the filing date the agent reports with the cutoff; detection from the values used is planned.
  * **Tool Math Purity Ratio (TMPR):** 🟡 not yet measured for LLMs (hard-coded for the reference solver).
  * **Composite Līlāvatī Index:** Weighted institutional benchmark score (0-100).
- [x] **5.4 Reproduction CLI and baselines:**
  * `lilavati-bench` CLI (`run`, `list-cases`); `scripts/run_llm_baseline.py` direct-prompt baseline with raw outputs in `results/`.
  * First measured baseline (4 Google models, Nov 2026): answered items were almost all correct, so the golden cases are saturated.
  * Groq baselines (5 open-weight models, 2026-11-20, `--provider groq`): generated cases separate models (item accuracy 0.2625-0.9500); truncation, unparsable and provider failures counted separately; `--rescore` re-scores stored replies.
  * No public leaderboard yet.
- [x] **5.5 Verification:** reference solver passes all 7 golden tracks (by construction; it uses the same engines the checks use).

---

### Phase 6: Pre-Prints, Documentation & Soft Launch (Status: DRAFTS — ALPHA)
*Goal: working-draft papers, documentation and a quiet public repository for early feedback.*

- [x] **6.1 Academic Pre-Print 1 (Framework Paper):**
  * *"Līlāvatī: A Neuro-Symbolic Agentic Framework for Institutional Financial Reasoning"*
  * Working draft at `docs/papers/01_framework_paper.md` (not peer reviewed).
- [x] **6.2 Academic Pre-Print 2 (Benchmark Paper):**
  * *"Līlāvatī-Bench: Stress-Testing Financial LLMs and Agents on Accounting Invariants and Look-Ahead Bias"*
  * Working draft at `docs/papers/02_benchmark_paper.md` with measured baselines (not peer reviewed).
- [x] **6.3 Documentation & Interactive Tutorials:**
  * MkDocs Material documentation website (`mkdocs.yml`, `docs/index.md`, `docs/architecture.md`, `docs/benchmarks.md`).
  * 4 executable institutional tutorial scripts in `examples/`:
    1. `examples/01_three_statement_reconciliation.py`: statement graph with a driver shock, its balance check, and a wiring fault that fails it.
    2. `examples/02_statistical_arbitrage_pairs.py`: Engle-Granger cointegration, OU half-life, and GARCH.
    3. `examples/03_climate_risk_stress_test.py`: Portfolio WACI, shadow carbon tax, and SLB covenants.
    4. `examples/04_autonomous_agent_tracing.py`: Full agent loop with OpenTelemetry tracing and JSONL audit export.
- [x] **6.4 Soft launch:** public GitHub repository, `v0.1.0-alpha` pre-release, CI, SECURITY.md, CODE_OF_CONDUCT.md, issue/PR templates.
- [x] **6.5 MCP usability:** `lilavati-mcp-*` launch commands for all 8 servers and `docs/mcp-setup.md` (Claude Code / Claude Desktop configuration).

---

### Phase 7: Verification & Validation → Public Announcement (Status: IN PROGRESS)
*Goal: every capability we announce is independently verified. No announcement until the gate below is green.*

**7A. Correctness (blocking)**
- [x] 7.0 LLM tool calling for Gemini and Anthropic (previously tools were silently dropped, so agents never called tools on those providers); bounded retries on 429/5xx; tool-round limit separate from reflection limit; mocked format tests and opt-in live tests (`tests/integration/`).
- [x] 7.1 Fix Beneish M-score coefficients (TATA 4.679, LVGI −0.327) with tests against Beneish (1999).
- [x] 7.2 Fix Almgren-Chriss schedule (clipping bug, price units, discrete solution) with reference tests.
- [~] 7.3 Reference-value audit of every engine, published in `docs/validation/`. 🟡 Done: fixed income, derivatives, invariants, sustainability, forensics, Almgren-Chriss, econometrics, financial ML (33 bugs fixed). Pending: LOB / Black-Litterman / HRP, statement graph (equity plug removed and hand-checked 2026-11-27; no published reference yet), connectors.
- [x] 7.4 Purged and embargoed K-fold and combinatorial purged CV (López de Prado 2018, ch. 7 and 12), with the Probabilistic and Deflated Sharpe ratios and the probability of backtest overfitting (CSCV), in `core/backtest_overfitting.py` (2026-11-26). DSR and PBO checked against the authors' worked example and Algorithm 2.3; the CV splits against an independent implementation of the definitions (not yet against AFML's code). Tutorial 09.
- [~] 7.5 Live-data validation: EDGAR company facts for at least 2 real issuers; the 10-K parser on at least 2 filings; one real Ind AS annual report. 🟡 Started 2026-11-22: 10-K parser checked line by line on Apple's FY2026 10-K (4 bugs fixed; `docs/validation/connectors.md`); EDGAR client contact fixed. Done 2026-11-23: filing-anchored XBRL extraction validated on 5 companies (71 of 71 values found in the filing documents; comparative-period bug fixed); LLM comparison on 4 real 10-Ks (Tutorial 08). Also 2026-11-23: the same flow as the MCP tool `get_filing_figures`, with ticker lookup through SEC's company list. Done 2026-11-24: Ind AS crosswalk on Maruti Suzuki's FY2025-26 audited results. Pending: banks and insurers, 10-Q validation (cash-flow items are year-to-date) and restatements, a second Ind AS company.

**7B. Honest documentation (blocking)**
- [x] 7.6 README, docs, dev skill and roadmap list only implemented capabilities; planned items are marked.
- [x] 7.7 Draft papers: placeholder results removed; measured baselines and limitations stated.
- [x] 7.8 Final claims sweep (completed 2026-11-22). Done: claims linter (`scripts/check_claims.py`, in CI) over README, docs, docstrings and examples; all flagged proof/guarantee/"audited"/maturity/priority language reworded (2026-11-22); benchmark paper numbers come from `results/ANALYSIS.md`. Also done: framework-paper sections 6–7 traced to scripts (6.3 replaced untraceable figures with the credit example's output; latency re-measured; the 100% metrics labelled as by construction); Table 1 venues verified (ConvFinQA is EMNLP 2022; PIXIU task count and two reference entries corrected). References: all 27 unique entries verified against primary sources; corrected TAT-QA authors and title, Garcez et al. venue, Toolformer and ReAct years, Almgren-Chriss issue year and DOI; removed a non-existent "FinBench" entry (arXiv:2311.12345) and an in-text citation to a fictional "Līlāvatī Benchmark Consortium"; added the missing Lean and Isabelle entries. Heritage passages no longer make priority or anachronistic claims; the claims linter skips bibliography titles and now catches historical priority wording.

**7C. Packaging & release (blocking)**
- [x] 7.9 Distribution renamed to `lilavati-finance` (PyPI name `lilavati` belongs to an unrelated project).
- [~] 7.10 PyPI release. 🟡 Done: `.github/workflows/release.yml` (tag/version check, build, clean-install smoke test on 3.11 and 3.12, Trusted Publishing); local clean installs verified; sdist excludes private `.agents/tasks/`. Done 2026-11-22: GitHub `pypi` environment created, restricted to `v*` tags. Pending (maintainer): register the trusted publisher on PyPI; then tag the release. Deferred 2026-11-23 until reviewer feedback and the announcement; early users install from GitHub.
- [x] 7.11 Docs site and CI. 🟡 Done: CI runs the strict docs build, every example, tutorial code, claims and manifest checks; `.github/workflows/docs.yml` deploys to Pages. Done 2026-11-22: Pages enabled (source "GitHub Actions"); the site is live at https://revendrat.github.io/lilavati/ and redeploys on every docs change to `main`.
- [x] 7.12 Author Revendranath Tirumalsety (ORCID 0000-0003-0549-4022) in `pyproject.toml`, `CITATION.cff`, the README citation and both papers.

**7D. Benchmark credibility (recommended before announcing the benchmark; not blocking the toolkit)**
- [x] 7.13 Tool-augmented baseline with measured TMPR (tool grounding): `scripts/run_tool_baseline.py`, paired with the no-tool arm on the same questions; four Groq models (2026-11-21/22; allam-2-7b has no tool support on Groq), results in `results/ANALYSIS.md` and benchmark paper §5.3.
- [x] 7.13a Results published as evidence: raw replies tracked, `results/manifest.json` (hashes, settings, case hashes), CC BY 4.0 data licence, `scripts/analyse_results.py` (bootstrap CIs, paired differences); generated case ids made unique (content hashes); prompt versioning (v3 fixed the "5-year bond" key).
- [ ] 7.13b Citable snapshot: GitHub release archived on Zenodo (DOI) once the maintainer enables the integration.
- [ ] 7.13c Larger evidence base: 20+ generated cases per track on all 7 tracks, 3+ samples per model, held-out private seed.
- [ ] 7.14 Citation track on real documents (real PoCS).
- [ ] 7.15 Look-ahead track with a poisoned corpus (real TPI).
- [ ] 7.16 Multi-step three-statement generated cases.

**7F. Positioning & integrations (blocking for soft release)**
- [x] 7.19 Position Līlāvatī as validated finance tools for agents over MCP (works with LangGraph, Google ADK, Claude), not as a competing orchestration framework; README intro updated.
- [x] 7.20 LangGraph example (`examples/integrations/langgraph_agent.py`), run end to end on Gemma 4 31B; runs in its own env because `langchain-mcp-adapters` needs `mcp<2`.
- [x] 7.21 Google ADK example (`examples/integrations/adk_agent.py`), run end to end on Gemma 4 31B.
- [x] 7.21a A2A: ADK agent served over Agent2Agent (`adk_a2a_server.py`) with a protocol-only client (`a2a_client.py`), run end to end.
- [ ] 7.21b CI job running the integration examples against a cheap model on a schedule (needs a CI secret).
- [ ] 7.22 Live Anthropic tool-calling run (needs an API key); live Gemini 4 Neon run (free-tier quota exhausted on 2026-11-19).
- [x] 7.22a Live Groq tool-calling runs: gpt-oss-120b, gpt-oss-20b, qwen3.6-27b passed 3/3; qwen3.8-27b passed 1/3 (malformed tool calls rejected by Groq, HTTP 400 `tool_use_failed`).

**7G. Tutorials and teaching**
- [x] 7.23 Tutorials 05–07 (benchmarking with open models; analysing and publishing results; tools versus mental math), user skill `lilavati-bench`, draft course syllabus (`docs/course/index.md`).
- [x] 7.24a Tutorial 01 retrofitted (2026-11-22): both covenants checked, "debt reduction to comply" instead of a mislabelled equity cure, no "proof" language, localhost serving, real outputs, runnable tests, exercises; `examples/06` rewritten to match.
- [x] 7.24 Tutorials 02–04 retrofitted (2026-11-22) and executed in CI; examples 07–09 rewritten to match. Fixed on the way: Tutorial 02 could not run as written (empty price series); Tutorial 03 reported a manipulation finding for a firm whose statements were inconsistent, used a real company's name for synthetic data and proxied retained earnings; Tutorial 04 split emissions by an invented 70/30 ratio. The carbon-tax engine docstring now states its unit rule.

**7E. Announcement**
- [ ] 7.17 External review by at least one practitioner (quant/credit) and one software reviewer; issues triaged.
- [ ] 7.18 Announce as an alpha toolkit for feedback (GitHub install), then tag `v0.2.0` and publish to PyPI (order changed 2026-11-23). 🟡 Release candidate built and verified locally on 2026-11-22 (`dist/`: wheel, sdist, results bundle, SBOM, vulnerability scan, verification report, checksums; release notes in `docs/releases/v0.2.0.md`); version bumped to 0.2.0. Waiting on the maintainer inputs and go-ahead.

---

## Phases 8–12: from validated toolkit to verifiable financial intelligence (planned)

*From the strategy review of 2026-11-21. Tasks, gap analysis and open decisions: [TODO.md](TODO.md).
Each phase ends in a gate: measurable evidence before the next phase starts.*

- [ ] **Phase 8 (about 4 weeks): credibility, v0.2.** Phase 7 blocking items, tutorials 02–04 retrofit, paired runs in the paper, DOI, external review. *Gate:* every published number traceable to the manifest or a validation page.
- [ ] **Phase 9 (months 1–3): contracts and evidence.** `VerifiedResult` contract with typed quantities, evidence ledger with derived provenance, trace replay, Z3 unsat cores and symbolic covenant questions, purged CV with Deflated Sharpe Ratio, surface no-arbitrage, benchmark v2 (7 tracks, 20+ cases each, 3+ samples, private seed; needs API budget) with process metrics, abstention and real-document cases. *Gate:* a paired tool/no-tool result whose CI excludes zero on non-saturated cases.
- [ ] **Phase 10 (months 3–6): narrow data commons.** Licence review per source; EDGAR company facts, ALFRED, World Bank, RBI DBIE and MOSPI vintages; typed macro series; curated India set; minimal ontology with US GAAP and Ind AS comparability adjustments; point-in-time track with restatement cases and counterfactual twins.
- [ ] **Macro-financial track (Phases 10–11).** Macro identity checks (sectoral balances, balance of payments, debt dynamics), reference-checked engines (Hamilton filter, local projections, Taylor rules), transmission into curve, covenant and default-probability engines, a vintage benchmark track. *Gate:* a look-ahead leak measured on real vintages. *Gate:* a measured point-in-time leak on a real vintage dataset.
- [ ] **Phase 11 (months 6–9): multi-agent reliability research.** Architecture ladder on LangGraph at constant model, data and budget. *Gate:* pilot Financial AI Reliability Report v0.
- [ ] **Phase 12 (months 9–12): Academy and community.** Learning pathways, university pilot, student competition, static trace viewer. *Gate:* outside contributors landing validated engines.
- [ ] **Enterprise-quality track (alongside):** semantic versioning and API policy, coverage and full CI, vulnerability scanning and SBOM, signed releases, API authentication, CODEOWNERS and maintainer team, independent audit.

---

## Not yet implemented (previously advertised; tracked honestly)

- [ ] Meta-labeling, information-driven bars (dollar/volume/imbalance); purged and embargoed CV done (7.4)
- [ ] Johansen/VECM, KPSS, Phillips-Perron, EGARCH, DCC-GARCH, Markov-switching/HMM
- [ ] Heston, local volatility, full-surface no-arbitrage checks
- [ ] Key-rate durations, Nelson-Siegel-Svensson, CDS hazard-rate bootstrapping, debt tranche waterfalls
- [ ] VPIN, TWAP/VWAP/POV execution schedules
- [ ] US-GAAP to IFRS reconciliation; full NGFS scenario pathways
