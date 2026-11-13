# Project Līlāvatī: The Open-Source Operating System for Institutional Finance

> *"Active and graceful maiden with playful eyes, Līlāvatī! If you have learned the method of inversion, tell me what is that number which multiplied by 3, then increased by three-fourths of the product, divided by 7, diminished by one-third of the quotient, multiplied by itself, diminished by 52, the square root extracted, then 8 added, and divided by 10, gives the number 2?"*
> — **Bhāskarācārya II**, *Līlāvatī* (c. 1150 CE)

---

## What is Project Līlāvatī?

**Project Līlāvatī** is an open-source, audited & verifiable agentic stack and evaluation benchmark suite exclusively engineered for institutional quantitative finance, debt/credit markets, econometrics, financial machine learning, derivatives, market microstructure, and sustainability finance. Under the hood, it pairs generative semantic perception with deterministic formal verification and theorem proving.

Generic LLM agent frameworks fail in institutional finance because they treat numbers as text tokens, suffer from mental math hallucinations, leak future information through look-ahead bias, and lack auditable provenance.

Līlāvatī solves this through a **Domain-Specific Runtime & Protocol Layer**:
1. **Zero LLM Arithmetic:** LLMs plan and reason; all calculations are executed deterministically through Python, Polars, DuckDB, and FastMCP.
2. **First-Order Formal Invariants (Z3 SMT Solver):** Core accounting identities ($Assets = Liabilities + Equity$) and debt covenants are formally proved via SMT solvers, enabling neuro-symbolic self-correction.
3. **Cryptographic Provenance (`CitationRef`):** Every numerical fact extracted from SEC EDGAR or Ind AS filings carries an immutable SHA-256 document hash, page, and snippet citation.
4. **Bi-Temporal Point-in-Time Isolation:** Disclosures are indexed with Dual-Time semantics (Valid Time $T_v$ vs System Time $T_s$) to guarantee zero look-ahead bias in backtests and agent evaluations.
5. **OpenTelemetry-Compatible Tracing:** Full compliance audit trails capturing agent turns, LLM prompts/tokens, deterministic tool outputs, and formal solver proofs.

---

## Quickstart

### Installation

```bash
git clone https://github.com/revendrat/lilavati.git
cd lilavati
uv sync
```

### Running the Līlāvatī-Bench CLI

Evaluate an agent or model across all 7 quantitative tracks:

```bash
uv run lilavati-bench run --model lilavati-reference-v1 --format rich
```

### Inspecting Golden Test Cases

```bash
uv run lilavati-bench list-cases
```

---

## Flagship Pillars

| Pillar | Capability | Key Technologies |
| :--- | :--- | :--- |
| **Pillar I** | Dynamic Three-Statement Modeling & Valuation | Reactive DAG, Polars, Z3 SMT Solver |
| **Pillar II** | Fixed Income, Credit & Debt Indentures | Bond Analytics (DV01, Convexity), Nelson-Siegel, Merton Structural Model |
| **Pillar III** | Financial Econometrics & Stationarity | ADF Unit Root, Johansen Cointegration, OU Half-Life, GARCH(1,1) |
| **Pillar IV** | Financial ML (de Prado Paradigm) | Fractional Differentiation ($d^*$), Triple-Barrier Labeling, Purged CV |
| **Pillar V** | Derivatives, Volatility Surfaces & Greeks | Black-Scholes-Merton, CRR Binomial Trees, SABR Calibration, Arbitrage Invariants |
| **Pillar VI** | Market Microstructure & Optimal Execution | LOB Microprice, OFI, Almgren-Chriss Liquidation, Black-Litterman, HRP |
| **Pillar VII** | Sustainable Finance & Climate Risk | Scope 1/2/3 WACI, Shadow Carbon Tax Stress Testing, SLB Step-Up Covenants |

