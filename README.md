<div align="center">

# 🪷 Līlāvatī (लीलावती)

### The Open-Source, Neuro-Symbolic Agentic Stack for Institutional Finance

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/Protocol-FastMCP-green)](https://github.com/jlowin/fastmcp)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Status](https://img.shields.io/badge/Status-Alpha%20%2F%20Research-orange)](#academic-research--pre-prints)

*A domain-specific runtime, standardized FastMCP tool bus, and benchmark suite for autonomous financial reasoning, econometrics, credit risk, and algorithmic execution.*

</div>

---

## 📖 The Historic Anecdote & Ethos

In **1150 CE**, Indian mathematician and astronomer **Bhāskarācārya (Bhāskara II)** completed the classical mathematical treatise *Līlāvatī* (*Siddhānta Śiromaṇi*). Unlike contemporary academic texts of antiquity, Bhāskara framed mathematics as an engaging, dialogic conversation with his daughter, Līlāvatī, incorporating affectionate feminine vocatives (*"O Līlāvatī, intelligent girl..."*) throughout.

Crucially, substantial portions of the *Līlāvatī* were devoted to practical commercial and financial mathematics:
* **Miśraka-vyavahāra**: Partnerships, capital shares, joint ventures, and interest rate calculations.
* **Kraya-vikraya**: Buying, selling, price elasticity, and barter economies.
* **Suvarṇa-gaṇita**: Alligation and gold purity verification—history’s earliest recorded treatise on **financial auditing, assaying, and ledger balance verification**.

**Project Līlāvatī** channels this 900-year heritage into modern computational finance. We replace the stochastic, hallucination-prone arithmetic of generic Large Language Models with **deterministic execution, formal invariant verification, and bi-temporal precision**.

---

## ⚡ Why Generic Agent Frameworks Fail in Institutional Finance

Generic LLM agent frameworks (LangChain, AutoGen, CrewAI) treat numerical quantities as token probabilities. In institutional finance, this leads to catastrophic failures:

1. **Mental Math Hallucinations:** LLMs attempt multi-step CAGR, DCF, or bond duration math inside token generation, producing subtly erroneous values.
2. **Missing Cryptographic Provenance:** Summaries lack verbatim hash-linked references (`CitationRef`) to the underlying 10-K, 10-Q, or statutory footnote.
3. **Look-Ahead & Restatement Poisoning:** Static RAG pipelines ingest historical filings alongside future restatements or subsequent events, corrupting backtests and credit assessments.
4. **Broken Accounting Invariants:** LLMs frequently produce three-statement projections where $Assets \neq Liabilities + Equity$ or the cash flow ending balance fails to reconcile with balance sheet cash.
5. **Econometric Naivety:** Naive agents regress un-differenced non-stationary price series, creating spurious alpha signals from pure noise.

---

## 🏛️ The Five Pillars of Līlāvatī

Līlāvatī spans the full capital structure and operational lifecycle of institutional investing:

```
                                  PROJECT LĪLĀVATĪ
                     Unified Institutional Agentic Architecture
                                         │
    ┌──────────────────┬─────────────────┼─────────────────┬──────────────────┐
    ▼                  ▼                 ▼                 ▼                  ▼
PILLAR I:          PILLAR II:        PILLAR III:       PILLAR IV:         PILLAR V:
Fixed Income       Financial         Financial ML      Derivatives &      Trading, Micro-
& Credit           Econometrics      (de Prado)        Volatility         structure & Exec
─────────────────  ────────────────  ────────────────  ─────────────────  ─────────────────
• Yield Curves     • ADF / KPSS      • Dollar / Volume • SABR / Heston    • L2/L3 Order
  (Nelson-Siegel)    Unit Root         Bars              Calibration        Books (OFI/VPIN)
• Duration, KRD,   • Johansen        • Fractional      • Local Vol        • Almgren-Chriss
  DV01 / PV01        Cointegration     Diff (d*)         Surfaces           Optimal Exec
• Merton Default   • GARCH & DCC     • Triple-Barrier  • 1st & 2nd Order  • Black-Litterman
  Model / CDS        Heterosked.       Labels            Greeks (Vanna,     & Hierarchical
• Debt Covenants   • Markov Regime   • Purged &          Volga)             Risk Parity
  & Waterfalls       Switching         Embargoed CV      • Delta Neutral    • VWAP / TWAP
                     (MS-AR / HMM)   • Meta-Labeling     Rebalancing        Slippage Models
```

### Pillar I: Fixed Income, Debt & Credit Capital Markets
* **Yield Curves & Sensitivities:** QuantLib-powered bootstrapping of spot, forward, and par yield curves (Nelson-Siegel, Nelson-Siegel-Svensson); calculation of Modified Duration, Key Rate Durations (KRD), and DV01/PV01.
* **Credit Risk:** Merton structural default model (equity as a call option on corporate assets); ISDA standard CDS hazard rate bootstrapping.
* **Covenant Headroom & Waterfalls:** Parsing credit agreements to model Net Leverage ($TotalDebt / EBITDA$), Interest Coverage, and senior vs. subordinated repayment tranches.

### Pillar II: Financial Econometrics
* **Unit Root Diagnostics:** Automated Augmented Dickey-Fuller (ADF), Phillips-Perron, and KPSS tests to prevent spurious regression.
* **Cointegration & Stat-Arb:** Engle-Granger and Johansen cointegration tests, Vector Error Correction Models (VECM), and Ornstein-Uhlenbeck mean-reversion half-life estimation.
* **Volatility Modeling:** GARCH(1,1), EGARCH (for asymmetric leverage), and DCC-GARCH (Dynamic Conditional Correlation) for multi-asset hedging.
* **Regime Detection:** Markov-Switching Autoregression (MS-AR) and Hidden Markov Models (HMM) for regime identification.

### Pillar III: Financial Machine Learning (Marcos López de Prado Paradigm)
* **Information-Driven Bars:** Dollar, Volume, and Tick Imbalance Bars (TIBs).
* **Fractional Differentiation:** Minimal $d^* \in (0, 1)$ solving for stationarity while preserving maximum memory.
* **The Triple-Barrier Method:** Path-dependent labeling (Take-Profit, Stop-Loss, Expiration).
* **Purged & Embargoed Cross-Validation:** Elimination of serial correlation leakage across overlapping returns.
* **Meta-Labeling:** Primary model predicts position; secondary ML model filters false positives and sizes bets.

### Pillar IV: Derivatives, Volatility Surfaces & Risk
* **Surface Calibration:** Calibration of SABR and Heston stochastic volatility models to market smiles.
* **Arbitrage Invariance:** Autonomous verification of calendar spread and butterfly arbitrage conditions.
* **Greeks Hedging:** Real-time computation of first- and second-order Greeks ($\Delta, \Gamma, \mathcal{V}, \Theta, \rho, \text{Vanna}, \text{Volga}$).

### Pillar V: Trading, Microstructure & Algorithmic Execution
* **Order Book Dynamics:** L2/L3 order book depth reconstruction, Order Flow Imbalance (OFI), and VPIN toxicity detection.
* **Optimal Execution:** Almgren-Chriss market impact vs. volatility trade-off, TWAP, VWAP, and POV algorithms.
* **Portfolio Construction:** Black-Litterman allocation (fusing equilibrium priors with agent views) and Hierarchical Risk Parity (HRP).

---

## 🧩 The Core Runtime Architecture

Līlāvatī separates the cognitive reasoning of LLMs from deterministic mathematical execution:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        COGNITIVE AGENT LAYER                           │
│   Adversarial Committee (Macro Strategist ↔ Quant ↔ Credit ↔ Auditor)  │
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
│   mcp-filings-xbrl  │  mcp-fixed-income  │  mcp-econometrics-quant     │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ Normalizes Ingestion
┌────────────────────────────────────▼───────────────────────────────────┐
│                    CANONICAL DATA & ONTOLOGY LAYER                     │
│   DuckDB Bi-temporal Storage │ US-GAAP ↔ IFRS ↔ Ind AS Reconciliation  │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Zero LLM Arithmetic Policy:** LLMs are strictly forbidden from emitting calculated numbers directly in their responses. All mathematical values must originate from deterministic FastMCP servers.
2. **`CitationRef` Provenance:** Every extracted line item carries a cryptographic hash: `CitationRef(doc_hash, page, table_id, xbrl_tag)`.
3. **Bi-Temporal Point-in-Time Isolation:** Using DuckDB bi-temporal semantics, queries specify `valid_time` and `as_of_timestamp` to prevent look-ahead bias and restatement contamination.
4. **Z3 SMT Invariant Verification (`Suvarna` Engine):** Financial statement identities ($A = L + E$) and no-arbitrage bounds are encoded in first-order logic. Infeasible projections trigger automatic agent self-correction.

---

## 🏆 Līlāvatī-Bench: The Financial Agent Benchmark

To measure progress, we are developing **Līlāvatī-Bench**, an open benchmark testing autonomous agents and finance-tuned foundation models across six tracks:

* **Track 1: Three-Statement Dynamic Reconciliation:** Propagation of operational shocks across 3 statements verified via Z3 SMT solver.
* **Track 2: Fixed Income, Credit & Debt Waterfalls:** Recovery of debt indentures, tranche seniority, covenant headroom, and Merton default probabilities.
* **Track 3: Econometric Rigor & Spurious Correlation Resistance:** Automated detection of unit roots and cointegration testing before model fitting.
* **Track 4: Financial ML Methodological Soundness:** Enforcement of fractional differentiation and purged cross-validation.
* **Track 5: Derivatives & Volatility Arbitrage Invariance:** SABR calibration and arbitrage-free implied volatility surface constraints.
* **Track 6: Market Microstructure & Optimal Execution:** Almgren-Chriss liquidation and VWAP slippage optimization on simulated order books.

---

## 🎓 Academic Research & Pre-Prints

Project Līlāvatī is designed to produce open-source software and peer-reviewed research. We invite researchers and practitioners to collaborate on upcoming papers:

1. **"Līlāvatī: A Neuro-Symbolic Agentic Framework for Institutional Financial Reasoning"** (Target: NeurIPS / ACL / FinNLP).
2. **"Līlāvatī-Bench: Stress-Testing Financial LLMs and Autonomous Agents on Accounting Invariants and Look-Ahead Bias"** (Target: Journal of Financial Data Science / SSRN / arXiv).
3. **"Eliminating Arithmetic Hallucinations in Financial Agents via SMT Solvers and FastMCP"** (Target: ACM ICAIF - International Conference on AI in Finance).

### Citing Project Līlāvatī

If you use Līlāvatī in your research or applications, please cite:

```bibtex
@software{lilavati2026,
  author = {Project Lilavati Contributors},
  title = {Līlāvatī: An Open-Source, Neuro-Symbolic Agentic Operating System for Finance},
  year = {2026},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/revendrat/lilavati}}
}
```

---

## 🤝 Contributing & Community

We are building a welcoming, mathematically rigorous community of:
* **Quantitative Researchers & Econometricians:** Implement statistical arbitrage, GARCH, and term-structure modules.
* **Credit & Debt Specialists:** Build covenant parsers and debt waterfall solvers.
* **Core Software Engineers:** Scale FastMCP servers, DuckDB bi-temporal pipelines, and Rust bindings.
* **Academic Contributors:** Expand golden datasets for `Līlāvatī-Bench`.

Please read our [Contributing Guidelines](CONTRIBUTING.md) to get started.

### Coding with AI Tools (Claude Code, Cursor, Antigravity, Codex)

If you are using AI coding agents or assistants to write code for this repository, please direct your agent to read the repository skill:
👉 [`.agents/skills/lilavati-dev/SKILL.md`](.agents/skills/lilavati-dev/SKILL.md)

This skill instructs coding agents on our **Zero LLM Arithmetic** rule, Z3 invariant verification, type annotations, and PR validation standards.

---

## 📄 License

Project Līlāvatī is licensed under the [Apache License 2.0](LICENSE).

