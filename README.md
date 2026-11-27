<div align="center">

# 🪷 Līlāvatī (लीलावती)

### Validated quantitative-finance tools for AI agents

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/Protocol-FastMCP-green)](https://github.com/jlowin/fastmcp)
[![M8ven Score](https://m8ven.ai/badge/mcp/revendrat-lilavati-1rcgwi?v=47231e534c8336ceb9b52c8a4709ba98)](https://m8ven.ai/mcp/revendrat-lilavati-1rcgwi?s=readme)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Status](https://img.shields.io/badge/Status-Alpha%20%2F%20Research-orange)](#project-status-and-limitations)

*Deterministic, reference-tested finance engines (fixed income, derivatives, econometrics, financial ML, execution, sustainability, accounting checks) served as MCP tools for LangGraph, Google ADK, Claude and any MCP client, plus a benchmark for financial agents.*

</div>

---

> **Alpha / research preview. Not investment advice.** Outputs are not independently audited; see [Project status and limitations](#project-status-and-limitations) before relying on them.

---

## 💡 Why Līlāvatī

AI agents are being asked to price bonds, read filings, check covenants and size trades. Two things go wrong, and this open source project has measured both:

1. **Models get numbers wrong when they compute in text.** Without tools, five open-weight models
   (gpt-oss-120b, gpt-oss-20b, Qwen3.6 27B, Qwen3.8 27B and ALLaM 2 7B, served by Groq) scored between
   21% and 94% item accuracy on the same 20 generated finance cases; Qwen3.8 27B missed all four
   Black-Scholes cases ([results](results/ANALYSIS.md)). With a tool, the question becomes parameter
   extraction: in our live tool-calling test, **gpt-oss-120b, gpt-oss-20b and Qwen3.6 27B** called the
   bond-pricing tool correctly in all three runs, while Qwen3.8 27B produced malformed tool calls in two
   of three. On the same 20 questions, tools raised Qwen3.6 27B from 0.70 to 1.00 and Qwen3.8 27B from
   0.39 to 0.80 item accuracy (paired 95% CIs exclude zero), and exposed new failure modes to measure,
   such as tool-call loops.
2. **Finance code is easy to get subtly wrong, even when written with care.** Auditing our own engines
   against textbooks, original papers and QuantLib found and fixed **33 bugs**, among them GARCH orders
   passed to `arch` swapped, a Beneish coefficient with the wrong sign, and a Merton solver that returned
   non-solutions for distressed firms ([validation](docs/validation/index.md)). Every team that writes these
   formulas from scratch, or asks an agent to, carries the same risk.

On top of that, general-purpose agent frameworks do not by themselves track where a number came from,
whether a balance sheet still balances, or whether a backtest used data published after its as-of date.

**What Līlāvatī gives you**

- **Validated engines as tools.** Deterministic fixed-income, derivatives, econometrics, financial-ML,
  execution and sustainability functions. Audited engines are tested against independent references with
  the measured tolerance published per engine; engines still awaiting audit are marked as such.
- **No new framework to adopt.** Eight MCP servers that plug into LangGraph, Google ADK, A2A, Claude or any
  MCP client; the model extracts parameters, the tool returns the number.
- **Checks agents usually skip.** Z3 accounting-identity checks, `CitationRef` provenance on extracted
  values, and bi-temporal as-of queries against look-ahead and restatement leakage.
- **An honest benchmark.** Līlāvatī-Bench reports provider failures, truncation, unparsable replies and wrong
  answers separately, with a content-free baseline for calibration.

**Why contribute**

- **One validated implementation, shared.** A fix here (such as the GARCH order bug) fixes every agent that
  calls the tool, instead of each team finding it alone.
- **Small, checkable contributions.** A typical PR is one function plus a reference test that cites its
  source. Open work: auditing the order book, Black-Litterman and HRP engines; checking purged cross-validation against a reference;
  Heston, Nelson-Siegel-Svensson and key-rate durations; harder multi-step benchmark cases
  ([roadmap](ROADMAP.md)).
- **Domain expertise counts as much as code.** Practitioners who can supply a worked example from a
  textbook, term sheet or filing make the references stronger.
- **AI-assisted contributions are welcome.** The [repository skill](.claude/skills/lilavati-dev/SKILL.md)
  gives coding agents the same rules human contributors follow.

---

## 👥 Who it is for

| You are | What Līlāvatī gives you today | Start here | Status |
| :--- | :--- | :--- | :--- |
| **Finance student or educator** | Runnable tutorials with exercises and instructor notes; a draft 12-week course; everything runs on free tiers or local models | [Tutorial 01](docs/tutorials/01_build_your_first_financial_agent.md), [course](docs/course/index.md) | ✅ all ten tutorials at the tutorial standard, their code executed in CI (except steps that read a file the reader downloads by hand, in Tutorial 10) |
| **Quantitative researcher or academic** | Līlāvatī-Bench with no-tool and tool arms; every model reply published with a manifest, bootstrap CIs and paired comparisons; reference-tested engines; the Deflated Sharpe Ratio, the probability of backtest overfitting and purged cross-validation for judging backtests | [Tutorial 06](docs/tutorials/06_analysing_and_publishing_results.md), [Tutorial 09](docs/tutorials/09_is_this_backtest_real.md), [results](results/ANALYSIS.md), [paper drafts](docs/papers/02_benchmark_paper.md) | 🟡 pilot-scale evidence (20 generated cases per model, one pass) |
| **Credit, equity or risk analyst** | Bond analytics, Merton PD, covenant checks, Beneish and Altman scores, WACI and sustainability-linked bond checks; SEC EDGAR, 10-K and Ind AS connectors, and a reader for NSE's Integrated Filing (Indian listed companies) | Tutorials [01](docs/tutorials/01_build_your_first_financial_agent.md), [03](docs/tutorials/03_forensic_accounting_and_adversarial_committee.md), [04](docs/tutorials/04_climate_risk_and_sustainable_portfolio.md), [08](docs/tutorials/08_real_10k_llm_vs_lilavati.md), [10](docs/tutorials/10_indian_company_from_exchange_filing.md) | 🟡 engines validated; SEC XBRL extraction piloted on five companies' latest 10-Ks; 10-K PDF parser checked on one filing (Apple FY2026), Ind AS crosswalk on one company's annual results (Maruti Suzuki FY2026) |
| **AI or agent engineer** | Eight MCP servers; LangGraph, Google ADK and A2A examples; one client for OpenAI-compatible (incl. Groq, Ollama, vLLM), Gemini and Anthropic APIs; a tool-use evaluation harness | [Integrations](docs/integrations.md), [MCP setup](docs/mcp-setup.md), [Tutorial 07](docs/tutorials/07_tools_versus_mental_math.md) | ✅ live-tested on Gemini and Groq; Anthropic format-tested only |
| **Model validation, audit or compliance** | Per-engine validation pages (reference, measured tolerance, bugs fixed); provenance on extracted values; Z3 accounting-identity checks; a reproducible evidence trail | [Numerical validation](docs/validation/index.md) | 🟡 order book, Black-Litterman, HRP and statement graph not yet audited; connectors piloted ([connectors page](docs/validation/connectors.md)) |
| **Open-source contributor** | Clear rules (developer skill, CONTRIBUTING), a roadmap with open items, small checkable tasks (one function plus a cited reference test) | [CONTRIBUTING](CONTRIBUTING.md), [roadmap](ROADMAP.md), [to-do](TODO.md) | ✅ |
| **Enterprise platform team** | Typed Python APIs, local REST serving, Apache-2.0 | [SECURITY.md](SECURITY.md) | 🗺️ not yet enterprise-ready (see below) |

### Towards enterprise quality

The goal is an open-source project that an institution can adopt with the same confidence as
commercial software. Where it stands:

| In place | Still needed (tracked in [ROADMAP](ROADMAP.md) and [TODO](TODO.md)) |
| :--- | :--- |
| Apache-2.0; typed Pydantic APIs checked with mypy | PyPI release with semantic versioning and an API stability and deprecation policy |
| 600+ tests, including reference tests against textbooks, papers and QuantLib | Coverage reporting |
| CI on Python 3.11 and 3.12: lint, type check, tests; strict docs build, every example, tutorial code, claims linter, results manifest | Dependency vulnerability scanning and SBOM |
| Release workflow with PyPI Trusted Publishing and a clean-install smoke test (ready; awaiting PyPI setup) | First PyPI release (deferred until reviewer feedback; install from GitHub meanwhile) |
| Validation pages per audited engine; published benchmark evidence with a manifest; documentation site on GitHub Pages | Audits of the remaining engines; wider live-filing validation (more companies, 10-Q, banks); independent review |
| Security policy, code of conduct, citation file, changelog | Authentication for the API server; a maintainer team, response targets and release cadence |

---

## 🎓 Learn: tutorials and a course

Every feature comes with a tutorial (ten so far): what it is for, runnable steps, the real mistakes it guards
against, how to use it with Claude Code, and exercises.

| Tutorial | You will learn to |
| :--- | :--- |
| [01 Credit workflow: covenants, Merton PD & API](docs/tutorials/01_build_your_first_financial_agent.md) | check covenants exactly at the limit, compute a Merton PD, test and serve the workflow |
| [02 Statistical arbitrage & execution](docs/tutorials/02_statistical_arbitrage_and_execution_agent.md) | test cointegration, validate the estimates on a simulated pair, schedule a liquidation |
| [03 Forensic screens & bull/bear committee](docs/tutorials/03_forensic_accounting_and_adversarial_committee.md) | check statement consistency first, then screen with Beneish and Altman |
| [04 Climate risk in a portfolio](docs/tutorials/04_climate_risk_and_sustainable_portfolio.md) | compute WACI, stress a debtor under a carbon price, check a sustainability-linked bond |
| [05 Benchmarking LLMs with free & open models](docs/tutorials/05_benchmarking_llms_with_open_models.md) | run fair no-tool baselines and classify failures |
| [06 Analysing, publishing & citing results](docs/tutorials/06_analysing_and_publishing_results.md) | compute CIs, pair comparisons, publish evidence |
| [07 Tools versus mental math](docs/tutorials/07_tools_versus_mental_math.md) | measure what tools change, on the same questions |
| [08 A real 10-K, three ways](docs/tutorials/08_real_10k_llm_vs_lilavati.md) | get figures from SEC filings reliably across companies, and compare an LLM alone, an LLM with Līlāvatī, and Līlāvatī alone |
| [09 Is this backtest real?](docs/tutorials/09_is_this_backtest_real.md) | deflate the best of many backtests (DSR), estimate the probability of backtest overfitting, and build purged cross-validation splits |
| [10 An Indian company from its exchange filing](docs/tutorials/10_indian_company_from_exchange_filing.md) | read NSE's Integrated Filing into the Ind AS crosswalk, check it against the printed statements, and cite every figure |

**For universities:** a draft one-semester course, [*AI in Finance: Harnessing LLMs, Correcting
Their Mistakes*](docs/course/index.md), maps these tutorials to a 12-week schedule with labs,
assessments and capstone projects that can become pull requests.

**For AI coding agents:** the [`lilavati-dev`](.claude/skills/lilavati-dev/SKILL.md) skill (contributing
code) and the [`lilavati-bench`](.claude/skills/lilavati-bench/SKILL.md) skill (running and analysing
benchmarks) give an agent the same rules as a human contributor.

---

## 🚀 Quick start

Python 3.11 or 3.12. Not on PyPI yet: install from GitHub to use it, or from source to contribute.

```bash
# Use it (import name: lilavati)
pip install "lilavati-finance @ git+https://github.com/revendrat/lilavati@main"

# Or work on it
git clone https://github.com/revendrat/lilavati.git && cd lilavati
uv sync --extra dev          # or: pip install -e ".[dev]"
uv run python -c "from lilavati.core.fixed_income import FixedIncomeEngine as F; \
print(F.analyze_bond(face_value=100, coupon_rate=0.05, ytm=0.06, years_to_maturity=10, frequency=2).clean_price)"
uv run pytest                # the test suite
```

**Next:** [Getting started](docs/getting-started.md) (first results from Python, an AI assistant
over MCP, an agent framework, or the benchmark) · [Tutorials](docs/tutorials/01_build_your_first_financial_agent.md)
· [FAQ and troubleshooting](docs/faq.md) · [Contributing guide](docs/contributing.md) (with first
tasks) · [Documentation site](https://revendrat.github.io/lilavati/), including the API reference.

### Use it from your agent framework

Līlāvatī is a tool layer, not another orchestration framework: LangGraph or Google ADK provide
graphs, checkpointing, streaming and human-in-the-loop; Līlāvatī provides the numbers.

| Framework | How | Example |
| :--- | :--- | :--- |
| LangGraph | `langchain-mcp-adapters` → `create_react_agent` | [`examples/integrations/langgraph_agent.py`](examples/integrations/langgraph_agent.py) |
| Google ADK | `McpToolset` in an `LlmAgent` | [`examples/integrations/adk_agent.py`](examples/integrations/adk_agent.py) |
| A2A (Agent2Agent) | ADK agent served with `to_a2a` | [`examples/integrations/adk_a2a_server.py`](examples/integrations/adk_a2a_server.py) |
| Claude Code / Desktop, any MCP client | `lilavati-mcp-*` stdio servers | [`docs/mcp-setup.md`](docs/mcp-setup.md) |

All three framework examples ran end to end on a real model (Gemma 4 31B via the Gemini API),
with answers matching the tool outputs; see [`examples/integrations/README.md`](examples/integrations/README.md).

---

## 📖 The Historic Anecdote & Ethos

In **1150 CE**, Indian mathematician and astronomer **Bhāskarācārya (Bhāskara II)** completed the mathematical treatise *Līlāvatī*, the first part of his *Siddhānta Śiromaṇi*. It poses its problems to a girl named Līlāvatī (by tradition, Bhāskara's daughter), in verses such as *"O Līlāvatī, intelligent girl..."*.

Substantial parts of the *Līlāvatī* deal with commercial mathematics:
* **Miśraka-vyavahāra** (mixtures): interest, partnerships and the division of profits by capital shares.
* **Kraya-vikraya** (buying and selling): rules of proportion for prices and quantities.
* **Suvarṇa-gaṇita** (gold): the purity and weight of gold alloys when pieces of different fineness are combined.

**Project Līlāvatī** takes its name and its spirit from that tradition of exact commercial computation: language models read and plan, while the numbers come from **deterministic, tested code**, with accounting identities checked and data kept point-in-time.

---

## 🏛️ What is implemented today

Status legend: ✅ implemented and tested · 🟡 partial · 🗺️ planned (see [ROADMAP.md](ROADMAP.md)). Per-engine validation status, also returned by every MCP tool: [validation status](docs/validation/status.md). Numerical validation against independent references is in progress ([docs/validation](docs/validation/index.md)); engines not yet audited should be treated as unvalidated.

| Area | Capability | Status | Module |
| :--- | :--- | :---: | :--- |
| **Fixed income & credit** | Bond price, Macaulay/modified duration, convexity, DV01 | ✅ | `core/fixed_income.py` |
| | Nelson-Siegel curve fit | ✅ | `core/fixed_income.py` |
| | Merton structural default model | ✅ | `core/fixed_income.py` |
| | Covenant checks (net leverage, interest coverage); smallest debt repayment meeting both, and checks over input ranges (Z3); multi-year covenant paths with linked interest and a cash sweep | ✅ | `core/invariants.py`, `core/covenant_paths.py` |
| | Nelson-Siegel-Svensson, key-rate durations, CDS hazard rates, tranche waterfalls | 🗺️ | n/a |
| **Econometrics** | ADF stationarity test | ✅ | `core/econometrics.py` |
| | Engle-Granger cointegration + OU half-life | ✅ | `core/econometrics.py` |
| | GARCH(p,q) volatility | ✅ | `core/econometrics.py` |
| | KPSS / Phillips-Perron, Johansen/VECM, EGARCH, DCC-GARCH, regime switching | 🗺️ | n/a |
| **Financial ML** | Fractional differentiation + minimal-d search | ✅ | `core/financial_ml.py` |
| | Triple-barrier labeling | ✅ | `core/financial_ml.py` |
| | Deflated Sharpe ratio, Probabilistic Sharpe ratio, probability of backtest overfitting (CSCV) | ✅ | `core/backtest_overfitting.py` |
| | Purged and embargoed K-fold, combinatorial purged CV with backtest paths (tested against the definitions; not yet checked against a reference) | ✅ | `core/backtest_overfitting.py` |
| | Meta-labeling, information-driven bars | 🗺️ | n/a |
| **Derivatives** | Black-Scholes price and Greeks, CRR American options, implied vol | ✅ | `core/derivatives.py` |
| | SABR smile calibration, butterfly arbitrage check (Z3) | ✅ | `core/derivatives.py` |
| | Heston, local vol, full-surface no-arbitrage | 🗺️ | n/a |
| **Execution & portfolio** | Order-book snapshot (spread, microprice, imbalance) | 🟡 not yet checked against a reference (#14) | `core/execution.py` |
| | Almgren-Chriss schedule (discrete, Almgren & Chriss 2000) | ✅ | `core/execution.py` |
| | Black-Litterman (weights by CVXPY with Clarabel, solver status checked), hierarchical risk parity | 🟡 not yet checked against a reference (#15, #16) | `core/execution.py` |
| | VPIN, TWAP/VWAP/POV | 🗺️ | n/a |
| **Sustainable finance** | WACI, carbon-tax stress test, SLB step-up covenant | ✅ | `core/sustainability.py` |
| | Full NGFS scenario pathways | 🟡 enum only | `schemas/sustainability.py` |
| **Verification & data** | Z3 three-statement invariants; diagnosis of which figures could be wrong when they fail | ✅ | `core/invariants.py` |
| | Statement DAG with driver shocks | 🟡 not yet checked against a reference (hand-checked; no plug, so its balance check can fail) | `core/graph.py` |
| | Bi-temporal DuckDB store, `CitationRef` provenance | ✅ | `core/temporal.py`, `core/provenance.py` |
| | SEC EDGAR XBRL: filing-anchored extraction (5-company live pilot), 10-K PDF parser, Ind AS crosswalk (PDF parser and crosswalk each checked on one company) | ✅ | `connectors/` |
| | NSE Integrated Filing (Financial) reader: an Ind AS company's exchange filing into the crosswalk, every figure cited (pilot on one filing, 26 of 28 printed items equal) | ✅ | `connectors/nse_integrated_filing.py` |
| | Market data: OHLCV normalisation, curve fit from supplied yields | 🟡 no data fetching / FRED yet | `connectors/market_data.py` |
| | US-GAAP ↔ IFRS reconciliation | 🗺️ | n/a |
| **Agents** | Neuro-symbolic runtime (identity checks with diagnosis on answers); filing extraction with diagnosis-driven repair; rule-based committee (Beneish, Altman, identity checks on reported inputs); research dossier from one 10-K with every input cited and checked against the SEC data read | ✅ | `runtime/`, `agents/` |
| | LLM tool calling: OpenAI-compatible (incl. Groq presets), Gemini, Anthropic, with retries on 429/5xx | ✅ live-tested on Gemini API (Gemma 4 31B, Gemini 4 Hydrogen) and Groq (gpt-oss-120b, gpt-oss-20b, qwen3.6-27b: 3/3 runs; qwen3.8-27b: 1/3, malformed tool calls); Anthropic format-tested only | `llm/client.py`, `llm/providers.py` |
| | Checkpointing, streaming, async, human-in-the-loop | not in core by design: use LangGraph / Google ADK with Līlāvatī's MCP servers | n/a |
| **Integrations** | LangGraph, Google ADK and A2A examples, run end to end on a real model | ✅ | `examples/integrations/` |
| | Eight FastMCP tool servers | ✅ | `mcp_servers/` |

---

## Project status and limitations

- **Not production software and not investment advice.** Outputs have not been independently audited. Do
  not use them for trading, credit or compliance decisions without your own validation. Provided "AS IS"
  under Apache-2.0.
- **The default LLM is a mock.** Out of the box, agents use `mock-evaluator`, which returns canned text, so
  the examples exercise the deterministic tools, not a real model. Set a provider key (OpenAI, Anthropic,
  Gemini, Groq or any OpenAI-compatible endpoint, vLLM, Ollama) in an environment variable to run real
  agent loops.
- **Benchmark scope.** The harness, a reference solver (passes by construction), a case generator and
  no-tool baselines for four Google and five Groq-hosted open-weight models are in
  [`results/README.md`](results/README.md). The 7 golden cases are saturated; the 20 generated cases
  separate models. Tool-augmented runs for four Groq models are in the same folder ([Tutorial 07](docs/tutorials/07_tools_versus_mental_math.md)), and a
  real-10-K comparison in `results/filings/` ([Tutorial 08](docs/tutorials/08_real_10k_llm_vs_lilavati.md)). Runs are single-step and
  single-pass; multi-step tracks are future work.
- **Not on PyPI yet.** Install from GitHub (see Quick start). The PyPI name `lilavati` belongs to an unrelated
  project; this package will be published as `lilavati-finance` (import name stays `lilavati`). The optional `quantlib` extra is
  currently unused by the code.
- **The API server** binds to `127.0.0.1` and has no built-in authentication. Put it behind your own auth or
  proxy before exposing it.

---

## 🧩 The Core Runtime Architecture

Līlāvatī separates the cognitive reasoning of LLMs from deterministic mathematical execution:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        COGNITIVE AGENT LAYER                           │
│   Rule-based Committee (Bull growth ↔ Bear Beneish/Altman ↔ Risk ids)  │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ Dispatches Structured Intent
┌────────────────────────────────────▼───────────────────────────────────┐
│                    LĪLĀVATĪ RUNTIME & VERIFICATION                     │
│  ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────┐ │
│  │ Zero-Arithmetic Guard │ │ Bi-Temporal (PIT) │ │ Z3 SMT Invariants │ │
│  └───────────────────────┘ └───────────────────┘ └───────────────────┘ │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ Dispatches Tool Execution via MCP
┌────────────────────────────────────▼───────────────────────────────────┐
│                       STANDARDIZED FAST-MCP BUS                        │
│  corporate-filings │ fixed-income │ econometrics │ 5 more MCP servers  │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ Normalizes Ingestion
┌────────────────────────────────────▼───────────────────────────────────┐
│                    CANONICAL DATA & ONTOLOGY LAYER                     │
│   DuckDB Bi-temporal Storage │ SEC XBRL & Ind AS ingestion             │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Zero LLM Arithmetic Policy (design goal):** Agents are designed so that calculated numbers originate from deterministic tools. Prompts require it and the integration examples check that answers quote tool outputs; no gate yet rejects a number in prose that no tool or source produced (proposed: [agent workflows](docs/agent-workflows.md), workflow 4).
2. **`CitationRef` Provenance:** Every extracted line item carries a citation, `CitationRef(doc_hash, page, table_id, xbrl_tag)`: a SHA-256 of the source document, or for XBRL of the fact record SEC serves (XBRL facts have no page).
3. **Bi-Temporal Point-in-Time Isolation:** Using DuckDB bi-temporal semantics, queries specify `valid_time` and `as_of_timestamp` to prevent look-ahead bias and restatement contamination.
4. **Z3 checks (`Suvarna` engine):** statement identities ($A = L + E$, the cash roll-forward) and no-arbitrage bounds are checked on the given numbers; when they fail, a diagnosis names the smallest sets of figures that could be wrong, and the agent re-checks those. Covenants are also checked over ranges and multi-year paths.

The agents (what each does and does not do) are described in [docs/agents.md](docs/agents.md); new workflows built from these parts, one implemented and four designed, in [docs/agent-workflows.md](docs/agent-workflows.md).

---

## 🏆 Līlāvatī-Bench: The Financial Agent Benchmark

To measure progress, we are developing **Līlāvatī-Bench** (harness available; no-tool baselines for Google and Groq-hosted open-weight models and a paired tool-augmented arm, in [`results/ANALYSIS.md`](results/ANALYSIS.md); no leaderboard yet), an open benchmark testing autonomous agents and finance-tuned foundation models across seven tracks:

| Track | What the cases test today | Planned |
| :--- | :--- | :--- |
| 1. Three-statement accounting | balance sheet balances; cash flow reconciles opening to closing cash | multi-step shock propagation across statements |
| 2. Fixed income and credit | bond price; Macaulay duration range; Merton distance to default and default probability | covenant headroom, tranche waterfalls |
| 3. Econometrics | unit-root (ADF) judgement on a random walk; rejecting a spurious levels regression | cointegration and half-life cases |
| 4. Financial ML | stationarity after fractional differencing; memory retained | cases for purged cross-validation, the Deflated Sharpe Ratio and PBO (the engines exist; the benchmark does not test them yet) |
| 5. Derivatives | Black-Scholes price, delta, gamma, vega; butterfly no-arbitrage check | SABR and volatility-surface cases |
| 6. Microstructure and execution | spread, microprice; Almgren-Chriss holdings at start and end | full schedules, VWAP |
| 7. Sustainable finance | portfolio WACI; sustainability-linked bond target, coupon and step-up | extraction of disclosed emissions from documents |

Tracks 1, 2, 5, 6 and 7 also have seeded generated cases; 3 and 4 have golden cases only.

Reproduce the paired experiment, no tools versus tools on the same questions (keys are read only
from environment variables):

```bash
export GROQ_API_KEY=...   # or GEMINI_API_KEY with --provider gemini
uv run python scripts/run_llm_baseline.py --provider groq --model openai/gpt-oss-120b \
    --generated 4 --seed 2026 --max-tokens 8192 --rpm 20 --out results/my_no_tools.jsonl
uv run python scripts/run_tool_baseline.py --provider groq --model openai/gpt-oss-120b \
    --generated 4 --seed 2026 --out results/my_tools.jsonl
uv run python scripts/build_results_manifest.py && uv run python scripts/analyse_results.py
```

All published replies, the manifest and the generated analysis are in [`results/`](results/README.md)
(data under CC BY 4.0). See [docs/benchmarks.md](docs/benchmarks.md) for how failures are counted.

---

## 🎓 Academic Research & Pre-Prints

Two working drafts live in `docs/papers/` (not peer reviewed): a framework paper
([01](docs/papers/01_framework_paper.md)) and a benchmark paper ([02](docs/papers/02_benchmark_paper.md))
whose results come from `results/ANALYSIS.md`. Researchers and practitioners are welcome to help with
larger evaluations; the research plan is in [TODO.md](TODO.md) (Phases 9–11).

### Citing Project Līlāvatī

If you use Līlāvatī in your research or applications, please cite:

```bibtex
@software{lilavati2026,
  author  = {Tirumalsety, Revendranath},
  title   = {Līlāvatī: Validated quantitative-finance tools for AI agents, and a benchmark for financial agents},
  year    = {2026},
  version = {0.2.0},
  url     = {https://github.com/revendrat/lilavati},
  note    = {Alpha release. ORCID 0000-0003-0549-4022}
}
```

### Built on

Līlāvatī wraps mature open-source libraries rather than reimplementing them: NumPy, SciPy,
statsmodels, arch, CVXPY with the Clarabel solver, Z3, DuckDB, Polars, pypdf, FastMCP, Pydantic and
httpx (QuantLib for test reference values). If your work relies on a result from one of them, please
cite it too: [libraries, solvers and citations](docs/validation/libraries.md) lists what each library
does here, how its output is checked, its licence and its preferred citation.

---

## 🤝 Contributing & Community

We are building a welcoming, mathematically rigorous community of:
* **Quantitative Researchers & Econometricians:** Implement statistical arbitrage, GARCH, and term-structure modules.
* **Credit & Debt Specialists:** Build covenant parsers and debt waterfall solvers.
* **Core Software Engineers:** Scale FastMCP servers, DuckDB bi-temporal pipelines, and Rust bindings.
* **Academic Contributors:** Expand golden datasets for `Līlāvatī-Bench`.

Please read our [Contributing Guidelines](CONTRIBUTING.md) to get started, and explore our [Development Roadmap & To-Do List](ROADMAP.md) to track active and upcoming engineering milestones.

### Coding with AI Tools (Claude Code, Cursor, Antigravity, Codex)

If you are using AI coding agents or assistants to write code for this repository, please direct your agent to read the repository skill:
👉 [`.claude/skills/lilavati-dev/SKILL.md`](.claude/skills/lilavati-dev/SKILL.md)

This skill instructs coding agents on our **Zero LLM Arithmetic** rule, Z3 invariant verification, type annotations, and PR validation standards.

---

## 📄 License

Project Līlāvatī is licensed under the [Apache License 2.0](LICENSE).

