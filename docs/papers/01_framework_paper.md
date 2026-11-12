# Līlāvatī: A Neuro-Symbolic Agentic Framework for Institutional Financial Reasoning

**Authors:** Project Līlāvatī Contributors  
**Classification:** Quantitative Finance, Artificial Intelligence, Multi-Agent Systems  
**Target:** arXiv (q-fin.ST / cs.AI / cs.MA), SSRN, ACM ICAIF  

---

## Abstract

Generic large language model (LLM) agent frameworks exhibit high failure rates in institutional finance due to numerical token hallucination, lack of formal invariant satisfaction, look-ahead bias, and absence of auditable provenance. In this paper, we present **Līlāvatī**, an open-source neuro-symbolic agentic framework inspired by Bhāskara II's 12th-century mathematical treatise. Līlāvatī establishes a strict separation between unstructured semantic perception (handled by foundation models) and deterministic quantitative computation (handled by high-performance engines and SMT solvers). 

The system features:
1. A **Zero LLM Arithmetic** protocol enforced via the Model Context Protocol (FastMCP).
2. The **Suvarṇa Engine**, an automated first-order logic solver using Z3 to formally verify accounting identities ($Assets = Liabilities + Equity$) and debt covenants with unsatisfiable core reflection.
3. Cryptographic provenance tracking linking all claims to source disclosure SHA-256 hashes (`CitationRef`).
4. Dual-time bi-temporal indexing (Valid Time $T_v$ vs System Time $T_s$) in DuckDB to eliminate look-ahead bias.

We demonstrate the framework across corporate credit analysis, derivatives pricing, statistical arbitrage, and sustainable finance.

---

## 1. Introduction

* The failure of standard LLM RAG pipelines in quantitative finance.
* Historical context: Bhāskara II's *Līlāvatī* and the tradition of verified arithmetic.
* The neuro-symbolic imperative: Language models for planning and extraction; formal solvers for verification.

## 2. Architecture & Design Principles

* The Four-Layer Architecture: Connectors, FastMCP Tool Bus, Skills, and Role-Bound Agents.
* The Non-Negotiable Rules: Zero LLM Math, Cryptographic Hashes, Point-in-Time Isolation.
* SMT Solver Formulation of Accounting Equations ($Suvarṇa-Gaṇita$).

## 3. Core Quantitative Engines

* Three-Statement Reactive Financial Graphs (`StatementGraph`).
* Fixed Income, Yield Curves (Nelson-Siegel), and Merton Structural Credit Risk.
* Econometric Stationarity and Engle-Granger Cointegration.
* Financial Machine Learning: Optimal Fractional Differentiation $d^*$ (de Prado).
* Analytical Derivatives, Greeks, and SABR Stochastic Volatility.
* Trading Microstructure: Order Book Microprice, OFI, and Almgren-Chriss Optimal Execution.
* Sustainability Finance: Carbon WACI, Carbon Tax Stress Testing, and SLB Step-Up Covenants.

## 4. Multi-Agent Deliberation: The Adversarial Investment Committee

* The Bull-Bear Protocol.
* The Formal SMT Verification Gatekeeper.
* Synthesis into Audited Investment Committee Memoranda.

## 5. Empirical Results & Discussion

* Latency and throughput benchmarks across FastMCP servers.
* Invariant satisfaction rate under stress conditions.

## 6. Conclusion & Roadmap

* Path to open-source financial foundation models trained on verified reasoning traces.

