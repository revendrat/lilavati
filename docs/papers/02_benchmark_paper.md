# Līlāvatī-Bench: Stress-Testing Financial LLMs and Agents on Accounting Invariants and Look-Ahead Bias

**Authors:** Project Līlāvatī Contributors  
**Classification:** Quantitative Finance, Benchmarking, Machine Learning  
**Target:** Journal of Financial Data Science / NeurIPS Datasets & Benchmarks Track  

---

## Abstract

Evaluation benchmarks for financial artificial intelligence currently overemphasize multiple-choice question answering (e.g., FinQA, CFA exam questions) while failing to test actual production operational requirements: formal balance sheet reconciliation, look-ahead bias resistance, and cryptographic provenance. We introduce **Līlāvatī-Bench**, an open-source evaluation suite designed to stress-test financial LLMs and multi-agent systems across seven core quantitative disciplines.

Līlāvatī-Bench introduces four institutional metrics:
1. **Proof-of-Citation Score (PoCS)**: Measures verifiable cryptographic linkage of extracted claims to statutory filings.
2. **Accounting Invariant Compliance Rate (ICR)**: Formally evaluates adherence to balance sheet identities and debt covenants via Z3 SMT solver satisfiability.
3. **Temporal Purity Index (TPI)**: Quantifies resistance to point-in-time look-ahead bias.
4. **Tool Math Purity Ratio (TMPR)**: Assesses the degree of delegation to deterministic compute sandboxes versus token-level arithmetic hallucinations.

Across our evaluation of state-of-the-art commercial and open-source models, standard prompting achieves low ICR (< 40%) due to rounding and hallucination errors, whereas the Līlāvatī neuro-symbolic reference solver achieves 100.0% ICR and 100.0% PoCS.

---

## 1. Introduction & Related Work

* Flaws in current financial benchmarks (FinQA, TAT-QA, FinGPT).
* Why multiple choice tests do not reflect trading and credit underwriting risks.
* The need for formal verification in financial benchmarks.

## 2. Benchmark Design & Dataset Curation

* Seven Foundational Tracks:
  1. Three-Statement Dynamic Reconciliation
  2. Fixed Income & Credit Risk
  3. Financial Econometrics & Stationarity
  4. Financial Machine Learning (Fractional Differentiation)
  5. Derivatives & Greeks
  6. Market Microstructure & Optimal Execution
  7. Sustainable Finance & Carbon Accounting
* Golden reference datasets with statutory SHA-256 document hashes.
* Point-in-time temporal boundaries ($T_{\text{cutoff}}$).

## 3. Evaluation Metrics Formulation

* Mathematical definition of PoCS, ICR, TPI, TMPR, and Composite Līlāvatī Index.
* Automated SMT Verification via `SuvarnaEngine`.

## 4. Empirical Evaluation & Findings

* Leaderboard comparison across leading foundation models.
* Failure modes: mental math compounding, restatement contamination, lack of covenant awareness.

## 5. Reproduction & Open Leaderboard

* Command-line execution via `lilavati-bench`.
* Submission guidelines for model creators.
