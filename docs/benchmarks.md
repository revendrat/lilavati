# Līlāvatī-Bench: Financial AI Agent Benchmark Suite

**Līlāvatī-Bench** is the first comprehensive quantitative benchmark evaluating financial foundation models and agents across seven tracks.

---

## The Four Core Institutional Metrics

1. **Proof-of-Citation Score (PoCS):**
   $$\text{PoCS} = \frac{\sum \text{Verified Claims with Matching Document SHA-256 and Valid Span}}{\text{Total Extracted Claims}}$$
   Measures whether claims trace back to statutory filings without hallucinations.

2. **Accounting Invariant Compliance Rate (ICR):**
   $$\text{ICR} = \frac{\sum \text{Statements Satisfying Formal Invariants via Z3 SMT Solver}}{\text{Total Evaluated Statements}}$$
   Tests that $Assets = Liabilities + Equity$ and Cash Flow reconciles with zero tolerance.

3. **Temporal Purity Index (TPI):**
   $$\text{TPI} = \frac{\sum \text{Observations where } T_{\text{filing}} \le T_{\text{cutoff}}}{\text{Total Observations}}$$
   Guarantees 100% resistance to look-ahead bias and restatement leakage.

4. **Tool Math Purity Ratio (TMPR):**
   $$\text{TMPR} = \frac{\text{Deterministic Tool Computations}}{\text{Deterministic Tool Computations} + \text{LLM Mental Math Assertions}}$$
   Enforces that LLMs never execute arithmetic inside text tokens.

5. **Composite Līlāvatī Index (0 - 100):**
   $$\text{Index} = 100 \times \left(0.30 \cdot \text{PoCS} + 0.30 \cdot \text{ICR} + 0.20 \cdot \text{TPI} + 0.20 \cdot \text{TMPR}\right)$$

---

## The Seven Quantitative Evaluation Tracks

| Track | Focus | Key Evaluated Assertions |
| :--- | :--- | :--- |
| **Track 1** | Three-Statement Reconciliation | Dynamic working capital shocks, SMT balance proofs |
| **Track 2** | Fixed Income & Credit | Bond pricing, duration, Merton structural default probability |
| **Track 3** | Econometrics | ADF unit roots, Engle-Granger cointegration, OU half-life |
| **Track 4** | Financial ML | Fractional differentiation order $d^*$, memory retention ($r \ge 0.70$) |
| **Track 5** | Derivatives | BSM Greeks, SABR volatility smile, Z3 butterfly spread arbitrage |
| **Track 6** | Microstructure & Execution | LOB Microprice, OFI, Almgren-Chriss liquidation schedule |
| **Track 7** | Sustainability Finance | Portfolio WACI, carbon tax sensitivity, SLB step-up covenants |

---

## Reproducing the Leaderboard

To run the benchmark against any model:

```bash
uv run lilavati-bench run --model <model-name> --format markdown
```

