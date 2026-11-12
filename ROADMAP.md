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

### Phase 1: Real-World Ingestion & Bi-Temporal Connectors (Status: IN PROGRESS 🎯)
*Goal: Connect the engine to live, real-world corporate filings and macroeconomic data feeds without look-ahead bias.*

- [ ] **1.1 SEC EDGAR XBRL / Company Facts Connector:**
  * Pulls live company filings (10-K, 10-Q) from SEC EDGAR API with compliant User-Agent headers.
  * Parses standardized `us-gaap` taxonomy line items into canonical `ThreeStatementModel`.
  * Generates cryptographic `CitationRef` for every parsed fact.
  * *Validation:* Parse Apple (AAPL) and Microsoft (MSFT) latest 10-K and verify $Assets = Liabilities + Equity$.
- [ ] **1.2 Market & Macro Series Connector:**
  * Async connector for historical OHLCV data (daily and intraday bars) normalized to Polars DataFrames.
  * Federal Reserve Economic Data (FRED) connector for SOFR, Treasury yields, CPI, and Fed Funds rate.
  * *Validation:* Fetch 5-year Treasury constant maturity series and verify Nelson-Siegel fit.
- [ ] **1.3 India BSE/NSE Ind AS Corporate Filings Connector:**
  * Ingestion wrapper for Indian corporate disclosures and MCA Ind AS taxonomy filings.
  * Entity Taxonomy Reconciliation Engine (ETRE) mapping Ind AS terms to canonical `ChartOfAccounts`.
  * *Validation:* Parse Reliance Industries or Infosys annual report balance sheet with 100% reconciliation.
- [ ] **1.4 Bi-Temporal DuckDB Local Data Warehouse:**
  * DuckDB storage layer implementing dual-time indexing: `valid_time` (period described) vs `as_of_timestamp` (filing date).
  * Enforces temporal filters preventing look-ahead leakage in historical backtests.
  * *Validation:* Query historical filing before and after an 8-K/restatement; verify restatement is invisible at $T_0$.

---

### Phase 2: Derivatives, Volatility Surfaces & Risk Engine (Status: QUEUED ⏳)
*Goal: Institutional derivatives pricing, volatility surface modeling, and multi-asset Greeks risk.*

- [ ] **2.1 Option Pricing Suite:**
  * Analytical Black-Scholes-Merton for European options with continuous dividend yield.
  * Cox-Ross-Rubinstein (CRR) binomial tree for American early-exercise options.
  * Numerical Monte Carlo engine for Asian and barrier options.
- [ ] **2.2 Volatility Surface Calibration:**
  * Calibrate SABR model ($\alpha, \beta, \rho, \nu$) and Heston stochastic volatility model to market option chains.
  * Extract Dupire local volatility surfaces.
  * SMT arbitrage-free verification: verify no calendar spread or butterfly arbitrage ($C(K_1) - 2C(K_2) + C(K_3) \ge 0$).
- [ ] **2.3 First- & Second-Order Greeks Hedging:**
  * Real-time calculation of Delta ($\Delta$), Gamma ($\Gamma$), Vega ($\mathcal{V}$), Theta ($\Theta$), Rho ($\rho$), Vanna ($\frac{\partial \Delta}{\partial \sigma}$), and Volga ($\frac{\partial \mathcal{V}}{\partial \sigma}$).
  * Dynamic delta-hedging and gamma-scalping simulation.
- [ ] **2.4 FastMCP Derivatives Server:**
  * Expose option pricing, SABR calibration, and Greeks computation tools over FastMCP.
- [ ] **2.5 Verification:** Test against CBOE SPX/VIX option chains with verified no-arbitrage bounds.

---

### Phase 3: Trading Microstructure, Execution & Portfolio Optimization (Status: QUEUED ⏳)
*Goal: Order book dynamics, optimal execution scheduling, and robust portfolio allocation.*

- [ ] **3.1 Limit Order Book (LOB) Reconstruction:**
  * L2/L3 order book depth processing, bid-ask spread decomposition, and Order Flow Imbalance (OFI).
  * VPIN (Volume-Synchronized Probability of Toxicity) to detect informed trading and adverse selection.
- [ ] **3.2 Optimal Execution Algorithms:**
  * **Almgren-Chriss Optimal Liquidation:** Analytical solver balancing permanent/temporary market impact and volatility risk.
  * Algorithmic execution schedulers: TWAP, VWAP, POV (Percentage of Volume), and Implementation Shortfall tracking.
- [ ] **3.3 Institutional Portfolio Optimization:**
  * **Black-Litterman Allocation:** Bayesian blending of passive market equilibrium priors with agent subjective views ($P, Q, \Omega$).
  * **Hierarchical Risk Parity (HRP):** Dendrogram clustering on asset correlation matrices, avoiding matrix inversion singularities.
  * Risk metrics: Parametric VaR, Historical VaR, and Conditional Value-at-Risk (CVaR / Expected Shortfall).
- [ ] **3.4 FastMCP Portfolio & Execution Server:**
  * Expose Black-Litterman, HRP, Almgren-Chriss, and VWAP execution tools over FastMCP.
- [ ] **3.5 Verification:** Run backtest on multi-asset portfolio verifying lower drawdown vs naive Markowitz.

---

### Phase 4: Multi-Agent Orchestration & The Adversarial Committee (Status: QUEUED ⏳)
*Goal: Role-bound agent loops debating investment theses under formal verification guardrails.*

- [ ] **4.1 Role-Bound Financial Agents:**
  * **Macro & Rates Strategist:** Analyzes central bank releases, yield curves, and macroeconomic regime shifts.
  * **Forensic Credit & Accounting Auditor:** Executes Beneish M-Score, Altman Z-Score, and footnote contradiction scans.
  * **Quantitative Equity & Stat-Arb Modeler:** Tests stationarity, cointegration, and runs fractional diff alpha models.
  * **Sustainable Finance Analyst:** Models Scope 1/2/3 carbon liabilities and SLB covenant risks.
  * **Execution Trader & Risk Officer:** Sizes positions using Kelly Criterion/meta-labeling and monitors execution slippage.
- [ ] **4.2 The Adversarial Investment Committee Protocol:**
  * Deliberative multi-turn protocol: Bull agent generates thesis; Bear/Auditor agent actively tries to falsify revenue recognition or covenants.
  * Mandatory Z3 formal verification gate before final memo output.
- [ ] **4.3 Verification:** End-to-end multi-agent evaluation on real historical distressed credits (e.g. SVB, Enron, Wirecard).

---

### Phase 5: Līlāvatī-Bench (The Financial Agent Benchmark Suite) (Status: QUEUED ⏳)
*Goal: The definitive evaluation suite testing autonomous financial agents and domain LLMs.*

- [ ] **5.1 Golden Benchmark Dataset Curation:**
  * 100 real-world corporate filings: 50 US SEC filings (10-K, 10-Q) + 50 India BSE/NSE filings (Ind AS).
  * Audited reference answers for ratios, three-statement reconciliations, and debt covenants.
  * 25 historical filings with verified accounting anomalies/restatements.
- [ ] **5.2 Automated Benchmark Runners across 7 Tracks:**
  * Track 1: Three-Statement Dynamic Reconciliation
  * Track 2: Fixed Income, Credit & Debt Waterfalls
  * Track 3: Econometric Rigor & Spurious Correlation Resistance
  * Track 4: Financial ML Methodological Soundness (de Prado)
  * Track 5: Derivatives & Volatility Arbitrage Invariance
  * Track 6: Market Microstructure & Optimal Execution
  * Track 7: Sustainable Finance & Climate Stress Testing
- [ ] **5.3 Quantitative Metric Evaluators:**
  * Proof-of-Citation Score (PoCS)
  * Accounting Invariant Compliance Rate (ICR)
  * Temporal Purity Index (TPI)
  * Tool Math Purity Ratio
- [ ] **5.4 Public Leaderboard & Reproduction CLI:**
  * `lilavati-bench run --model <model-name>` CLI tool generating reproducible leaderboard markdown.

---

### Phase 6: Academic Pre-Prints, Open-Source Launch & Community (Status: QUEUED ⏳)
*Goal: Academic recognition, peer-reviewed pre-prints, and viral open-source adoption.*

- [ ] **6.1 Academic Pre-Print 1 (Framework Paper):**
  * *"Līlāvatī: A Neuro-Symbolic Agentic Framework for Institutional Financial Reasoning"*
  * Target: arXiv / SSRN / NeurIPS / ACL FinNLP workshop.
- [ ] **6.2 Academic Pre-Print 2 (Benchmark Paper):**
  * *"Līlāvatī-Bench: Stress-Testing Financial LLMs and Agents on Accounting Invariants and Look-Ahead Bias"*
  * Target: Journal of Financial Data Science / ACM ICAIF.
- [ ] **6.3 Documentation & Tutorials:**
  * MkDocs Material documentation website with interactive notebooks.
- [ ] **6.4 Community Launch:**
  * Release on GitHub, Hugging Face Spaces leaderboard, Hacker News, Reddit (r/algotrading, r/MachineLearning), and FINOS.
