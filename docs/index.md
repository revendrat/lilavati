# Project Līlāvatī: validated finance tools for AI agents

> *"Active and graceful maiden with playful eyes, Līlāvatī! If you have learned the method of inversion, tell me what is that number which multiplied by 3, then increased by three-fourths of the product, divided by 7, diminished by one-third of the quotient, multiplied by itself, diminished by 52, the square root extracted, then 8 added, and divided by 10, gives the number 2?"*
> — **Bhāskarācārya II**, *Līlāvatī* (c. 1150 CE)

---

## What is Project Līlāvatī?

**Project Līlāvatī** is an open-source tool layer for financial agents (alpha) and an evaluation benchmark, covering quantitative finance, debt/credit markets, econometrics, financial machine learning, derivatives, market microstructure, and sustainability finance. Under the hood, models read and plan; reference-tested engines compute; Z3 checks accounting identities on the given numbers.

General-purpose LLM agent frameworks do not by themselves check where a number came from: models compute in text, can use information published after the as-of date, and leave no auditable provenance.

Līlāvatī addresses this with a **tool layer for agents**:

1. **Zero LLM Arithmetic (design goal):** LLMs read and plan; calculations run in deterministic, tested code (Python, Polars, DuckDB), exposed as FastMCP tools.
2. **First-Order Formal Invariants (Z3 SMT Solver):** Core accounting identities ($Assets = Liabilities + Equity$) are checked with the Z3 SMT solver on the given numbers (exact rational arithmetic), and debt covenants are checked arithmetically with an at-limit tolerance. These verify the numbers supplied, not a model over all inputs.
3. **Cryptographic Provenance (`CitationRef`):** Every numerical fact extracted from SEC EDGAR or Ind AS filings carries a citation: a SHA-256 hash of its source (the document for PDF or HTML, the fact record SEC serves for XBRL), the filing and period, the page where the source has pages, and a snippet.
4. **Bi-Temporal Point-in-Time Isolation:** Disclosures are indexed with Dual-Time semantics (Valid Time $T_v$ vs System Time $T_s$) so that queries return only what was known at the as-of time; detecting look-ahead use by an agent is still partial (TPI).
5. **OpenTelemetry-Compatible Tracing:** A trace of agent turns, LLM prompts and tokens, deterministic tool outputs and solver check results.

**Alpha software for research and teaching; not investment advice.**

## Start here

- **New here?** [Getting started](getting-started.md): install, then a first result from Python, an
  AI assistant (MCP), an agent framework or the benchmark, in a few minutes each.
- **Learning?** Eight [tutorials](tutorials/01_build_your_first_financial_agent.md) and a draft
  [course](course/index.md).
- **Checking the numbers?** [Numerical validation](validation/index.md) and the
  [benchmark evidence](benchmarks.md).
- **Contributing?** [Contributing guide](contributing.md), with first tasks.
- **Stuck?** [FAQ and troubleshooting](faq.md); full function documentation in the
  [API reference](reference/index.md).

---

## Quickstart

### Installation

Not on PyPI yet. To use it:

```bash
pip install "lilavati-finance @ git+https://github.com/revendrat/lilavati@main"
```

To contribute, or to run the tutorials and the commands below, work from a clone:

```bash
git clone https://github.com/revendrat/lilavati.git
cd lilavati
uv sync
```

### Running the Līlāvatī-Bench CLI

Run the deterministic reference solver across all 7 tracks (`--model` only labels the report card;
to score a real LLM use `scripts/run_llm_baseline.py`, see [Benchmarks](benchmarks.md)):

```bash
uv run lilavati-bench run --format rich
```

### Inspecting Golden Test Cases

```bash
uv run lilavati-bench list-cases
```

---

## Flagship Pillars

<!-- BEGIN generated: pillar table (scripts/render_validation_status.py) -->
| Pillar | Capability | Engines and validation status |
| :--- | :--- | :--- |
| **Pillar I** | Three-Statement Modeling & Accounting Checks | Accounting identities, diagnosis and covenant checks (Z3) ✅ [reference-checked](validation/invariants.md); Statement graph with driver shocks 🟡 [not reference-checked](validation/statement_graph.md) |
| **Pillar II** | Fixed Income, Credit & Debt Covenants | Bond price, durations, convexity, DV01 ✅ [reference-checked](validation/fixed_income.md); Nelson-Siegel curve fit ✅ [reference-checked](validation/fixed_income.md); Merton structural default model ✅ [reference-checked](validation/fixed_income.md); Multi-period covenant paths (linked interest, cash sweep), over ranges (Z3) ✅ [reference-checked](validation/invariants.md) |
| **Pillar III** | Financial Econometrics & Stationarity | ADF, Engle-Granger with OU half-life, GARCH(p, q) ✅ [reference-checked](validation/econometrics.md) |
| **Pillar IV** | Financial ML (de Prado Paradigm) | Fractional differencing, minimal-d search, triple barrier ✅ [reference-checked](validation/financial_ml.md); Probabilistic and Deflated Sharpe ratios, probability of backtest overfitting ✅ [reference-checked](validation/financial_ml.md); Purged and embargoed K-fold, combinatorial purged cross-validation 🟡 [not reference-checked](validation/financial_ml.md) |
| **Pillar V** | Derivatives, Volatility Surfaces & Greeks | Black-Scholes-Merton, Greeks, CRR, implied vol, SABR, butterfly check ✅ [reference-checked](validation/derivatives.md) |
| **Pillar VI** | Market Microstructure, Execution & Portfolio | Almgren-Chriss liquidation schedule ✅ [reference-checked](validation/execution.md); Order-book snapshot (spread, microprice, order-flow imbalance) 🟡 [not reference-checked](validation/execution.md); Black-Litterman posterior and weights 🟡 [not reference-checked](validation/execution.md); Hierarchical risk parity 🟡 [not reference-checked](validation/execution.md) |
| **Pillar VII** | Sustainable Finance & Climate Risk | WACI, carbon-tax stress test, sustainability-linked bond ✅ [reference-checked](validation/sustainability.md) |
| **Filings & agents** | Filing Connectors, Forensics & Agents | Beneish M-score, Altman Z-score ✅ [reference-checked](validation/forensics.md); Rule-based investment committee ✅ [rule-based](validation/forensics.md); SEC XBRL filing-anchored extraction and three-statement model 🟡 [piloted on real data](validation/connectors.md); 10-K PDF parser 🟡 [piloted on real data](validation/connectors.md); Ind AS crosswalk 🟡 [piloted on real data](validation/connectors.md); NSE Integrated Filing (Financial) page reader, Ind AS 🟡 [piloted on real data](validation/connectors.md) |

Status meanings and every MCP tool: [validation status](validation/status.md).
<!-- END generated: pillar table -->

---

## 📚 Tutorials

Runnable walkthroughs; CI runs their code exactly as written. Each has objectives, the real mistakes
it guards against, exercises and instructor notes.

1. [Tutorial 01: Your First Credit Workflow](tutorials/01_build_your_first_financial_agent.md):
   maintenance covenants (net leverage and interest coverage, exact at the limit), the debt reduction
   needed to comply, a Merton default probability and a local API. Code: `examples/06_build_custom_agent_and_api.py`.
2. [Tutorial 02: Statistical Arbitrage and Optimal Execution](tutorials/02_statistical_arbitrage_and_execution_agent.md):
   Engle-Granger cointegration, OU half-life, fractional differencing ($d^*$), order-book metrics and
   an Almgren-Chriss liquidation schedule. Code: `examples/07_stat_arb_and_execution_agent.py`.
3. [Tutorial 03: Forensic Accounting Screens and a Bull/Bear Committee](tutorials/03_forensic_accounting_and_adversarial_committee.md):
   Beneish M-score, Altman Z-score, a Z3 balance-sheet check and a rule-based committee.
   Code: `examples/08_forensic_committee_agent.py`.
4. [Tutorial 04: Climate Risk in a Portfolio](tutorials/04_climate_risk_and_sustainable_portfolio.md):
   WACI, carbon-tax stress, sustainability-linked bond covenants and HRP allocation (HRP not yet
   checked against a reference). Code: `examples/09_climate_sustainable_portfolio_agent.py`.
5. [Tutorial 05: Benchmarking LLMs with Free and Open Models](tutorials/05_benchmarking_llms_with_open_models.md):
   choosing a free or local provider, keeping keys private, and no-tool baselines with failures
   classified (provider error, model error, truncation, unparsable).
6. [Tutorial 06: Analysing, Publishing and Citing Results](tutorials/06_analysing_and_publishing_results.md):
   the results manifest, bootstrap confidence intervals and paired comparisons.
7. [Tutorial 07: Tools versus Mental Math](tutorials/07_tools_versus_mental_math.md): the same
   questions with and without deterministic tools, and tool grounding.
8. [Tutorial 08: A Real 10-K, Three Ways](tutorials/08_real_10k_llm_vs_lilavati.md): SEC figures
   taken from the filing itself, compared across an LLM alone, an LLM with Līlāvatī and Līlāvatī alone.
9. [Tutorial 09: Is This Backtest Real?](tutorials/09_is_this_backtest_real.md): the Deflated Sharpe
   Ratio, the probability of backtest overfitting and purged cross-validation, on a rule tried 400 ways.
10. [Tutorial 10: An Indian Company from Its Exchange Filing](tutorials/10_indian_company_from_exchange_filing.md):
   NSE's Integrated Filing read into the Ind AS crosswalk, checked against the printed statements.
