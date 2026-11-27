# Līlāvatī: A Neuro-Symbolic Tool Layer with Checkable Numbers for Financial Language-Model Agents

**Author:** Revendranath Tirumalsety ([ORCID 0000-0003-0549-4022](https://orcid.org/0000-0003-0549-4022))  
**Subject areas:** Computational finance; artificial intelligence; software for language-model agents  
**Status:** Working paper, not peer reviewed. Version of 27 November 2026.  

---

> **Reading note.** Results in sections 4, 5 and 8 are measured: each names the test, script or
> results file that reproduces it, and numbers were re-run on 26 November 2026 unless dated otherwise.
> The case studies in section 7 run the repository's examples on one real 10-K, one Indian exchange
> filing and two synthetic cases; they demonstrate the workflow and are not evaluations.

## Abstract

Language-model agents are asked to read filings and compute financial quantities, but a model that
computes in text can return a figure that looks plausible and is wrong, and a figure without a source
cannot be checked. Līlāvatī is an open-source, alpha-stage tool layer that separates the two tasks:
models read text and choose tools, deterministic engines compute, and checks decide what may pass. It
exposes 32 tools on eight Model Context Protocol servers over 22 engines. Each engine carries one of
four validation statuses, reported in every tool result: 12 are checked against independent references
(papers, textbooks or QuantLib), four are piloted on real filings, one is a fixed decision rule, and
five are not yet checked. Accounting identities are checked in exact arithmetic with the Z3 solver;
when they fail, a MaxSMT diagnosis names the smallest sets of figures that could be wrong, and the same
solver answers covenant questions over input ranges and multi-year paths. Every extracted figure
carries a citation that is resolved against the sources a pipeline read. A filing-extraction agent uses
these checks to decide which figures a model should re-read. On five 10-Ks with four open-weight
models, a first evaluation found faults in the checker rather than in the models; once they were fixed,
all 240 figures were read correctly in one pass, so the effect of the repair step remains unmeasured.
The paper describes the design, the evidence for each component and its limits.

---

## 1. Introduction

Language models read financial text well but compute in it unreliably. In the companion benchmark
paper, open-weight models answering generated finance questions without tools scored between 21.2
and 100 per cent on the answers they returned (the mean share of answer fields correct), and one model
missed all four Black–Scholes cases; given deterministic tools, two of the models improved by 0.30 and 0.41 on the same questions,
with paired 95 per cent confidence intervals that exclude zero (Tirumalsety, 2026). On real filings the
remaining failures were of a different kind: reading the wrong line or the wrong definition, not
arithmetic (section 8.2).

Finance adds requirements that generic agent frameworks do not address. Figures must reconcile:
assets equal liabilities plus equity, and opening cash plus the year's cash flows equals closing cash.
Figures must be traceable to the filing they came from. Historical analysis must use only what was
public at the time, or backtests leak the future (López de Prado, 2018). Methods must be correct, which
for numerical code means agreement with an independent reference rather than with itself.

Līlāvatī is a tool layer for these requirements, not a model or an agent framework. Its tools are
served over the Model Context Protocol, so agents built with LangGraph, Google's Agent Development Kit
or any MCP client can call them. This paper makes four contributions:

1. Deterministic engines exposed as tools, each validated against an independent reference where one
   exists, with its validation status returned in every tool result (sections 3.5 and 4).
2. Exact checks of accounting identities, with a diagnosis of which figures could be wrong, and
   solver-based answers to covenant questions over ranges and multi-year paths (section 3.2).
3. Provenance that is resolved, not only recorded: citations are checked against the sources a
   pipeline read, for SEC XBRL facts, documents and Indian exchange filings (sections 3.3 and 5).
4. Agent workflows that use the checks to decide what a model should re-read, and a first real-model
   evaluation that reports what it did and did not show (sections 6 and 8.2).

Section 2 reviews related work. Section 3 describes the architecture and the checks, section 4 the
engines and section 5 the filing connectors. Section 6 covers the agents, section 7 the case studies
and section 8 the evaluation. Section 9 states the limitations and section 10 concludes.

### 1.1 The name

Bhāskara II's *Līlāvatī* (c. 1150 CE), the arithmetic volume of his *Siddhānta Śiromaṇi*, includes
chapters on commercial calculation: interest and partnership (*miśraka-vyavahāra*), buying and selling,
and the computation of gold (*suvarṇa-gaṇita*), which treats the fineness and weight of gold when
pieces of different purity are combined (Colebrooke, 1817; Patwardhan et al., 2001). The project takes
its name from this tradition of exact commercial arithmetic, and its identity engine from
*suvarṇa-gaṇita*.

---

## 2. Related work

### 2.1 Financial language models and benchmarks

Domain-adapted models include FinBERT (Araci, 2019), BloombergGPT (Wu et al., 2023) and FinGPT (Yang et
al., 2023). Benchmarks such as FinQA (Chen et al., 2021), TAT-QA (Zhu et al., 2021) and the Financial
PhraseBank (Malo et al., 2014) evaluate question answering over tables and text, or sentiment. They
score answers; they do not check that a model's figures reconcile, that its citations resolve, or that
it used only information available at a given date.

### 2.2 Tool use

Toolformer (Schick et al., 2023) and ReAct (Yao et al., 2023) showed that language models can learn or
be prompted to call external tools and to interleave reasoning with actions. Līlāvatī supplies the
tools and the checks for one domain; it is agnostic about the agent loop that calls them.

### 2.3 Neuro-symbolic methods and SMT solvers

Neuro-symbolic systems combine learned components with symbolic reasoning (Garcez et al., 2019;
Manhaeve et al., 2018); interactive theorem provers such as Lean (de Moura et al., 2015) and Isabelle <!-- claims-ok: names a class of tools -->
(Paulson, 1994) have been paired with language models to check formal proofs. Satisfiability modulo
theories (SMT) solvers decide formulas over arithmetic and other theories; Līlāvatī uses Z3 (De Moura &
Bjørner, 2008) and its optimising extension νZ (Bjørner et al., 2015). Its diagnosis of failed
identities follows consistency-based diagnosis, in which a diagnosis is a minimal hitting set of the
conflicts (Reiter, 1987).

### 2.4 Financial machine learning

López de Prado (2018) identified methodological traps in financial machine learning: integer
differencing destroys memory, ordinary cross-validation leaks information between overlapping labels,
and a strategy chosen from many backtests overstates its performance. The Deflated Sharpe Ratio
corrects a Sharpe ratio for the number of trials, non-normal returns and sample length (Bailey & López
de Prado, 2014); its threshold is the expected maximum Sharpe ratio of unskilled trials, formalised as
the false strategy theorem (López de Prado & Bailey, 2021). The probability of backtest overfitting is
estimated by combinatorially symmetric cross-validation (Bailey et al., 2017). Līlāvatī implements all
of these (section 4.4).

---

## 3. Architecture and checks

Līlāvatī has four tiers (Figure 1). Connectors read filings and data and attach provenance. Engines
compute. Gates check identities, covenants, citations and dates between steps. Agents and workflows
combine them.

```
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 4  AGENTS AND WORKFLOWS                                           │
│   tool loop with reflection · filing extraction with repair ·          │
│   research dossier · rule-based committee                              │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 3  GATES                                                          │
│   identities (Z3) + diagnosis · covenants · provenance · as-of date    │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 2  ENGINES (32 MCP tools on 8 servers, validation status on each) │
│   fixed income · econometrics · financial ML · backtest statistics ·   │
│   derivatives · execution · sustainability · forensics                 │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 1  CONNECTORS AND PROVENANCE                                      │
│   SEC XBRL · 10-K PDF · Ind AS crosswalk · NSE Integrated Filing ·     │
│   source store (SHA-256) · bi-temporal store (DuckDB)                  │
└────────────────────────────────────────────────────────────────────────┘
```

**Figure 1.** *The four tiers. Notes: a model reads text and chooses tools in tier 4; every number it
reports should come from tier 2 or a cited source in tier 1.*

### 3.1 A design rule: no model arithmetic

**Design rule 1 (no model arithmetic).** *No arithmetic that determines a valuation, a ratio or an
accounting reconciliation is performed by a language model in generated text; it is dispatched to a
deterministic tool.*

The rule is a design principle, not an enforced property. The prompts require it and the tools supply
the numbers; the integration examples check that a final answer quotes the tool outputs; but no gate
yet rejects a number in prose that no tool or source produced (section 9). Where the rule holds, the
model reads parameters and coordinates tools, and model arithmetic does not reach the reported figures.

### 3.2 Identity checks and their diagnosis

The identity engine (*Suvarṇa*) checks the statement identities on the figures given. With $A_t$ total
assets, $L_t$ total liabilities, $E_t$ total equity, $C_t$ closing cash, $CFO_t$, $CFI_t$ and $CFF_t$
the operating, investing and financing cash flows and $FX_t$ the effect of exchange rates on cash:

$$|A_t - (L_t + E_t)| \le \epsilon, \qquad |C_t - (C_{t-1} + CFO_t + CFI_t + CFF_t + FX_t)| \le \epsilon,$$

with $\epsilon$ a stated rounding tolerance in the filing's units. Each figure is bound to its decimal
value as an exact rational, so a satisfiable result is the same as exact arithmetic on the inputs: it
checks the numbers supplied, not a model over ranges of inputs. A simplified form of the check is:

```python
solver = z3.Solver()
a, liab, e = z3.Real("assets"), z3.Real("liabilities"), z3.Real("equity")
solver.add(z3.Abs(a - (liab + e)) <= tolerance)        # balance sheet
for var, val in observed.items():
    solver.add(var == z3.RealVal(str(val)))             # the figures as reported
status = solver.check()
```

When an identity fails, the engine reports which and by how much, and diagnoses which figures could be
wrong. Each figure's reported value becomes a soft constraint and each identity a hard one; Z3's MaxSMT
optimiser finds the smallest sets of figures whose change makes every identity hold, which are the
minimal hitting sets of the conflicts (Reiter, 1987; Bjørner et al., 2015). A figure that appears in
two failing identities is singled out, with the value the others imply. When one identity fails, all of
its figures are candidates, because arithmetic cannot tell them apart. The diagnosis is passed to the
agent, which is asked to re-check each candidate against the source (section 6).

The same solver answers three questions that go beyond given numbers. The smallest debt repayment that
meets a net-leverage and an interest-coverage covenant together is a linear optimisation, solved
exactly in rationals with `z3.Optimize` under a stated model (repayment from outside the cash balance;
interest proportional to debt). Whether both covenants hold for every combination of debt, cash, EBITDA
and interest within given ranges is decided by asking for a breach anywhere in the box: an
unsatisfiable answer is a statement about every value in the ranges. Over several years the inputs are
linked (interest on each year's opening debt; an excess cash sweep that may step down with leverage),
and checking the corners of the ranges is no longer enough: in the repository's two-year example, all
four corners of the EBITDA guidance comply while a mid-range first year breaches the second year's
coverage, because better results reduce the sweep. The path check searches every path in the ranges
and replays each counterexample in exact arithmetic; the smallest upfront repayment is found by a
counterexample-guided loop with a quantified bisection as fallback. Each is tested against a closed form
or an exhaustive search (`docs/validation/invariants.md`).

### 3.3 Provenance

Each extracted figure carries a citation:

$$\text{CitationRef} = \langle h, \text{form}, t_{\text{filed}}, t_{\text{period}}, p, \text{tag}, \sigma \rangle,$$

where $h$ is the SHA-256 digest of the source (the document's bytes for a PDF or HTML filing; the
canonical JSON of the fact record for an SEC XBRL fact), $t_{\text{filed}}$ the filing date,
$t_{\text{period}}$ the period end, $p$ the page where the source has pages, the XBRL tag where it has
tags, and $\sigma$ the snippet the figure was read from.

A citation is resolved against a source store of what the pipeline read. The digest must be a
registered source. For an XBRL fact, the tag, period end, filing date and value must match the record;
an XBRL record carries no concept name, so concepts reported with identical records share a digest and
the tag is part of the reference. For a document, the snippet must appear on the cited page. Snippets
are compared with whitespace removed and typographic quotes read as plain ones, because text extraction
adds or drops spaces between table cells; every other character must match. That rule came from the
evaluation in section 8.2, where a spacing-sensitive check rejected correct quotes. Without a store,
only the form of a citation is checked.

### 3.4 Point-in-time queries

A bi-temporal store on DuckDB records for each fact its valid period and the period in which it was
known. A query at epoch $t$ returns only facts known at $t$ whose period ended by $t$, so a restatement
filed later is excluded. This limits look-ahead leakage through the store; it does not stop an agent
using information obtained elsewhere.

### 3.5 Validation status as data

Every engine has one of four statuses, defined in code (`lilavati/validation_status.py`): checked
against an independent reference within a stated tolerance; piloted on named real filings; a fixed
decision rule over checked components; or not yet checked, in which case results should be treated as
unvalidated. Every tool result returns its engine's status, so an agent can tell a checked engine from
an unchecked one, and the documentation's status pages are generated from the same list. Of the 22
engines, 12 are reference-checked, four piloted on real data, one rule-based and five not yet checked
(Table 1).

---

## 4. Engines

Table 1 lists the engines by area, with the reference each is checked against and its status. The
validation pages (`docs/validation/`) give each check, the tolerance measured and the bugs fixed.

**Table 1.** *Engines, references and validation status*

| Area | Engine | Reference checked against | Status |
| :--- | :--- | :--- | :--- |
| Accounting | Identities, diagnosis, covenant checks (Z3) | closed forms; exhaustive search | reference-checked |
| Accounting | Multi-year covenant paths (Z3) | exact simulation; exhaustive search | reference-checked |
| Accounting | Statement graph with driver shocks | hand calculations only | not reference-checked |
| Fixed income | Bond price, durations, convexity, DV01 | QuantLib | reference-checked |
| Fixed income | Nelson–Siegel curve | Nelson & Siegel (1987); QuantLib | reference-checked |
| Credit | Merton structural model | Merton (1974) equations, as in Hull's textbook | reference-checked |
| Econometrics | ADF, Engle–Granger with half-life, GARCH(p, q) | statsmodels; arch | reference-checked |
| Financial ML | Fractional differencing, d* search, triple barrier | López de Prado (2018) | reference-checked |
| Financial ML | PSR, DSR, probability of backtest overfitting | Bailey & López de Prado (2014); Bailey et al. (2017) | reference-checked |
| Financial ML | Purged K-fold, combinatorial purged CV | definitions only | not reference-checked |
| Derivatives | Black–Scholes–Merton, Greeks, CRR, implied volatility, SABR, butterfly check | QuantLib; Hagan et al. (2002) | reference-checked |
| Execution | Almgren–Chriss schedule | Almgren & Chriss (2000/2001) | reference-checked |
| Execution | Order-book snapshot | none | not reference-checked |
| Portfolio | Black–Litterman | none yet | not reference-checked |
| Portfolio | Hierarchical risk parity | none yet | not reference-checked |
| Sustainability | WACI, carbon-tax stress, sustainability-linked bond | TCFD definition; hand-computed cases | reference-checked |
| Forensics | Beneish M-score, Altman Z-score | Beneish (1999); Altman (1968) | reference-checked |
| Committee | Rule-based investment committee | rule over checked components | rule-based |
| Filings | SEC XBRL extraction, three-statement model | five 10-Ks | piloted on real data |
| Filings | 10-K PDF parser | one 10-K | piloted on real data |
| Filings | Ind AS crosswalk | one company | piloted on real data |
| Filings | NSE Integrated Filing reader | one filing | piloted on real data |

*Notes: statuses as defined in section 3.5 and returned by every tool. Each validation page names the
reference, the cases and the tolerance measured; "definitions only" means tests against an independent
implementation of the method's definitions.*

### 4.1 Fixed income and credit

Bond analytics cover price, Macaulay and modified duration, convexity and DV01; the Nelson–Siegel curve
is fitted by bounded least squares:

$$y(\tau) = \beta_0 + \beta_1 \frac{1 - e^{-\tau/\lambda}}{\tau/\lambda} + \beta_2 \left( \frac{1 - e^{-\tau/\lambda}}{\tau/\lambda} - e^{-\tau/\lambda} \right).$$

The Merton model treats equity as a call on the firm's assets $V_A$ with debt $D$ due at $T$, and solves
for asset value and asset volatility from equity value and equity volatility. The default probability
reported is $\Phi(-d_2)$ under the risk-neutral measure (drift $r$, not the physical asset drift), with

$$d_2 = \frac{\ln(V_A / D) + (r - \tfrac{1}{2}\sigma_A^2)T}{\sigma_A \sqrt{T}}.$$

The solver's result is checked against both Merton equations before it is returned; an earlier version
returned points with large equation errors in distress.

### 4.2 Econometrics

The engines are the augmented Dickey–Fuller test, Engle–Granger cointegration (Engle & Granger, 1987)
with the mean-reversion half-life of the spread, and GARCH(p, q) volatility. The half-life is that of an
AR(1) fit with coefficient $\phi$, $-\ln 2 / \ln \phi$ periods, which equals $\ln 2 / \theta$ for an
Ornstein–Uhlenbeck process with $\phi = e^{-\theta}$. Johansen cointegration is not implemented. The
audit fixed swapped GARCH orders: the `arch` library's argument order is the opposite of the usual
GARCH(p, q) notation.

### 4.3 Fractional differencing and labelling

Fractional differencing applies $(1 - B)^d = \sum_{k \ge 0} (-1)^k \binom{d}{k} B^k$ with a fixed-width
window (López de Prado, 2018, ch. 5). The minimal order $d^*$ is the smallest value on the grid
$\{0, s, 2s, \ldots, 1\}$ whose differenced series has an augmented Dickey–Fuller $p$-value at or below
a target (0.01 by default in the tool); the correlation with the original series is reported, not
optimised. Triple-barrier labels (López de Prado, 2018, ch. 3) mark the first touch of a take-profit,
stop-loss or time barrier.

### 4.4 Backtest statistics and leakage-free cross-validation

The Probabilistic Sharpe Ratio is the probability that the true Sharpe ratio exceeds a benchmark
$SR^*$, given $T$ observations, skewness $\gamma_3$ and raw kurtosis $\gamma_4$ of the returns:

$$\widehat{PSR}(SR^*) = \Phi\!\left( \frac{(\widehat{SR} - SR^*)\sqrt{T - 1}}{\sqrt{1 - \gamma_3 \widehat{SR} + \frac{\gamma_4 - 1}{4} \widehat{SR}^2}} \right).$$

The Deflated Sharpe Ratio sets $SR^*$ to the expected maximum Sharpe ratio of $N$ independent unskilled
trials with variance $V$ (López de Prado & Bailey, 2021, eq. 1), with $\gamma$ the Euler–Mascheroni
constant:

$$SR_0 = \sqrt{V} \left[ (1 - \gamma)\,\Phi^{-1}\!\left(1 - \tfrac{1}{N}\right) + \gamma\,\Phi^{-1}\!\left(1 - \tfrac{1}{N e}\right) \right].$$

The implementation reproduces the published worked example: a daily strategy with an annualised Sharpe
ratio of 2.5 after 100 trials, $V = 1/2$, $T = 1{,}250$, skewness $-3$ and kurtosis 10 gives
$SR_0 = 0.1132$ and $DSR = 0.9004$. With normal returns the DSR falls below 0.95 after 89 trials, as the
theorem's authors state. The approximation for the expected maximum is 2.3 per cent above the exact
expectation at $N = 10$ and 0.4 per cent above at $N = 1{,}000$.

The probability of backtest overfitting is estimated by combinatorially symmetric cross-validation
(Bailey et al., 2017, Algorithm 2.3): the $T \times N$ matrix of trial returns is cut into $S$ blocks,
each of the $\binom{S}{S/2}$ halves serves once as the in-sample set, and the in-sample winner's
out-of-sample rank gives a logit; PBO is the share of logits at or below zero. It matches a direct
transcription of the algorithm and the paper's ranking example. The DSR and PBO are MCP tools.

Purged and embargoed K-fold and combinatorial purged cross-validation (López de Prado, 2018, ch. 7 and
12) drop training observations whose label interval meets a test label, and a gap after each test
block. They are tested against an independent implementation of the definitions, not yet against the
book's code or a reference library, and are marked not reference-checked.

### 4.5 Derivatives

The engine prices European options with Black–Scholes–Merton and American options with a
Cox–Ross–Rubinstein tree, with first- and second-order Greeks including vanna and volga; it computes
implied volatility, calibrates the SABR smile (Hagan et al., 2002), and checks butterfly convexity in
strike with Z3 on the given prices.

### 4.6 Execution and portfolio construction

The Almgren–Chriss schedule (Almgren & Chriss, 2000/2001) minimises expected shortfall plus a risk
penalty; the audit fixed volatility units and a clipping that held risk-averse schedules to the end. The
order-book snapshot reports spread, microprice and a simplified order-flow imbalance (the change in
best-bid size minus the change in best-ask size); it is not reference-checked. Black–Litterman (Black &
Litterman, 1992) and hierarchical risk parity are implemented but not yet checked against published
examples; the audit fixed a Black–Litterman fallback that returned equal weights when the optimiser
failed.

### 4.7 Sustainable finance and forensics

The weighted average carbon intensity is $\sum_i w_i (\text{Scope 1}_i + \text{Scope 2}_i) /
\text{Revenue}_i$, with revenue in US dollar millions. The carbon-tax stress deducts
$(\text{Scope 1} + \text{Scope 2}) \cdot \tau \cdot (1 - \text{pass-through})$ from EBIT and compares the
stressed interest coverage with a covenant floor. The sustainability-linked bond engine checks a target
and applies the coupon step-up. The forensic engines compute the Beneish M-score (Beneish, 1999) and the
Altman Z-score (Altman, 1968); the Beneish coefficients, including one sign, were wrong in an early
version and are now pinned by a test.

---

## 5. Filing connectors

**SEC XBRL.** The connector identifies a filing from SEC's submissions index and takes the facts with
that filing's accession, period end and duration. Selecting by the fiscal-year field returned a filing's
prior-year comparatives as current figures (Apple's FY2024 revenue as FY2026). It builds a
three-statement model in which each field is reported, derived by a recorded formula, or listed as not
reported, and it refuses filings that lack required items. Piloted on the latest 10-Ks of five companies.

**10-K PDF.** A parser reads the statements from a 10-K's PDF with page-level citations, checked line by
line against one filing (Apple, FY2026).

**Ind AS.** A crosswalk maps Schedule III line items into the canonical model, deriving cost of goods
sold from its three Schedule III lines. A reader for the National Stock Exchange of India's page for an
Integrated Filing (Financial) feeds it. The filing is made in XBRL against SEBI's Integrated Filing
Finance Taxonomy (`in-capmkt`, version 1.0 of 31 January 2025, 507 elements); NSE publishes it as a page
rendered from the XBRL, with labels and values but no XBRL markup. The reader matches labels within
sections and uses headings to separate repeated labels. It takes a page the user supplies, because NSE's
terms of use prohibit automated collection without consent. Section 7.2 reports its pilot.

---

## 6. Agents and workflows

**Tool loop with reflection.** The runtime lets a model request tools that registered functions execute,
caps tool rounds and reports a stopped run as incomplete rather than as an answer. A JSON answer is
checked against every statement identity its figures allow; on failure, the model receives the
diagnosis of section 3.2 and tries again.

**Filing extraction with diagnosis-driven repair.** A model (or any extractor) returns each requested
figure with the line it was read from. The quote must appear in the document and the value in the quote.
The figures that pass are checked against every identity they allow; on failure, only the figures the
diagnosis names are re-read. The re-read request names the failed identities but not the values they
imply, because a model shown the expected value can copy it instead of reading the source. After a set
number of rounds the agent abstains on what remains, and it lists the figures that no identity covers,
which only the quote check stands behind.

**Rule-based committee.** The investment committee calls no language model; its roles are labels for
fixed rules. A growth rule compares revenue growth with a target. A forensic rule flags a Beneish
M-score above $-1.78$,

$$M = -4.84 + 0.920\,\text{DSRI} + 0.528\,\text{GMI} + 0.404\,\text{AQI} + 0.892\,\text{SGI} + 0.115\,\text{DEPI} - 0.172\,\text{SGAI} + 4.679\,\text{TATA} - 0.327\,\text{LVGI},$$

and Altman's distress zone, $Z = 1.2X_1 + 1.4X_2 + 3.3X_3 + 0.6X_4 + 0.999X_5$, with $X_2$ retained
earnings over total assets. A risk rule rejects the memo if the balance sheet or the cash reconciliation
fails on the reported inputs. An earlier version derived equity and opening cash from the other inputs,
so its checks could not fail; they now use reported figures only.

**Research dossier.** A research agent builds a dossier from one 10-K filed by an as-of date: the
statement model, the committee's verdict, a scenario tree and a citation for every figure, resolved
against the SEC data read.

---

## 7. Case studies

### 7.1 A US 10-K: Apple, fiscal 2026

The PDF analyser (`examples/problem_solving/04_sec_10k_filing_analyzer.py`) reads Apple's FY2026 Form
10-K (123 pages; SHA-256 beginning `f9a3e5b32cb7cbf2`; the PDF is not redistributed). It reports net sales
of US$478,834 million (15.1 per cent above US$416,161 million), operating income of US$158,063 million,
net income of US$132,175 million, operating cash flow of US$145,097 million (1.10 times net income),
capital expenditure of US$9,041 million and free cash flow of US$136,056 million. Total assets of
US$404,548 million equal liabilities (US$292,455 million) plus equity (US$112,093 million). The Beneish
M-score is $-2.52$ and the Altman Z-score 9.71, so the committee's rules return "approved". Each figure
cites its page and line, for example page 35, "Total net sales 478,834 416,161 391,035". The carbon line
uses illustrative emissions, not Apple's disclosures; it shows the calculation, not Apple's exposure.

### 7.2 An Indian exchange filing: Maruti Suzuki, fiscal 2025-26

The NSE reader takes Maruti Suzuki India's consolidated Integrated Filing (Financial) for the year ended
31 March 2026, filed on 28 April 2026, in lakhs of rupees. All three crosswalk identities hold on the
exchange figures; for cash, 18,450 + 19,09,990 − 14,73,350 − 4,48,400 = 6,690 lakh. Against the printed
statements in the results PDF, 26 of 28 items are equal. The two differences are definitions and
reconcile to the unit (INR million): the printed profit before tax (191,185) includes the share of profit
of associates (2,591) and joint ventures (264), which the exchange format shows after tax (188,330); the
exchange's property, plant and equipment (340,195) includes right-of-use assets (5,998), a separate
printed line. Two correct sources can disagree, and a figure must say which presentation it comes from.

### 7.3 Two synthetic cases

In a synthetic acquisition (`examples/problem_solving/01_forensic_ma_due_diligence.py`), the target's
receivables grew faster than its sales (DSRI 1.48) and its Beneish M-score was $-1.34$, above the $-1.78$
threshold, so the rules reject the acquisition; a Beneish flag is a reason to investigate, not a finding
of fraud. In a synthetic private-credit case (`examples/problem_solving/02_credit_covenant_and_distress_monitor.py`),
interest coverage is 2.33 times against a 3.00 minimum, the two-year Merton default probability is 9.93
per cent, and a net debt reduction of US$17.5 million restores the leverage test; how a sponsor's equity
cure counts towards it is set by each credit agreement.

---

## 8. Evaluation

### 8.1 Engine validation

Each engine marked reference-checked in Table 1 is tested against its reference within a measured
tolerance (`tests/reference/`; `docs/validation/`). The audit found and fixed bugs that unit tests had not
caught, including the examples noted in section 4: swapped GARCH orders, Merton points that did not solve
the equations, wrong Beneish coefficients and an equal-weight fallback in Black–Litterman. While the
backtest statistics were built, a variance computed from sums of squares returned $10^{-19}$ instead of
zero for a constant strategy and passed a zero-variance check; variances are now combined from centred
moments.

### 8.2 Filing extraction with repair, on real 10-Ks

The extraction workflow of section 6 was run on the latest 10-Ks of five companies (Apple, Microsoft,
Walmart, Johnson & Johnson and JPMorgan Chase): 60 figures, each asked only if its value is printed in
the statements text the model sees, with each filing's own XBRL facts as the truth. Four open-weight
models served by Groq (gpt-oss-120b, gpt-oss-20b, Qwen3.6 27B and Qwen3.8 27B) were compared under four
arms that share the first reading: one pass; re-read only what the checks name; re-read everything after
any failure; and re-read with the implied values shown (`scripts/run_extraction_repair_eval.py`; replies
in `results/extraction/`).

The first run found faults in the checker and the prompt, not misreadings. The quote check required the
document's spacing and apostrophes, so a model that wrote "(139,500)" for the text's "(139,500 )" was
rejected; all 17 figures abstained on in the one-pass arm had correct values. The revenue label read
"total revenue (net sales)", and for Walmart, which prints net sales and total revenues, two models took
net sales; no identity involves revenue there, so the agent accepted it. After both were fixed, every
model read all 60 figures correctly in one pass at temperature 0 (240 of 240), and no repair ran.

At temperature 1.0 (two models, three samples, 360 figures), Qwen3.6 27B read all 180 figures
correctly. gpt-oss-20b quoted three lines that are not in the document; the quote check caught all three
and one re-read fixed each. Its one misreading passed: JPMorgan's revenue read from "Noninterest revenue"
instead of "Total net revenue". The line exists and holds the value, and no identity involves a bank's
revenue, so the agent accepted it and listed it as unchecked. No identity failed in any run, so these
runs do not measure the diagnosis-driven repair; that needs inputs where models misread, such as PDF
page text or quarterly columns.

### 8.3 Latency

Latency was measured with `scripts/benchmark_latency.py` (30 runs after warm-up; three for the PDF) on
22 November 2026, with Python 3.11.14 on macOS 15.5 (arm64) and Z3 5.4.1 (Table 2). The figures depend
on the machine.

**Table 2.** *Latency of selected operations*

| Operation | Library | Median (ms) | 95th percentile (ms) |
| :--- | :--- | ---: | ---: |
| Balance-sheet identity check | Z3 | 1.10 | 1.39 |
| Nelson–Siegel fit (10 points) | SciPy | 3.75 | 5.54 |
| Minimal-d search (1,000 observations) | NumPy, statsmodels | 53.19 | 60.92 |
| SABR calibration (9 strikes, with butterfly check) | SciPy | 2.53 | 2.75 |
| Bi-temporal as-of query | DuckDB (in memory) | 1.70 | 1.98 |
| 10-K extraction (123 pages) | pypdf | 5,081 | 5,281 |

### 8.4 The reference pipeline

The benchmark's deterministic reference solver passes its own checks by construction: it uses the same
engines that compute the expected answers. Its scores confirm that the harness runs, not that any model
or agent is reliable; measured model results are in the companion paper (Tirumalsety, 2026).

---

## 9. Limitations

Seven limitations qualify the results.

1. **The design rule is not enforced.** No gate yet rejects a number in an answer that no tool or source
   produced (section 3.1).
2. **Five engines are not reference-checked:** the statement graph (checked against hand calculations only;
   until 27 November 2026 it balanced by an equity plug, so its balance check could not fail), purged
   cross-validation, the order-book snapshot, Black–Litterman and hierarchical risk parity.
3. **The real-data pilots are small:** five 10-Ks for SEC extraction, one 10-K for the PDF parser and one
   Indian filing for the crosswalk and the NSE reader.
4. **Identity checks verify the given numbers.** They cannot catch a wrong figure that no identity
   involves; the extraction agent lists such figures instead of passing them silently (section 8.2).
5. **The repair step is unmeasured.** No identity failed in the real-model runs, so its effect on
   accuracy is not known.
6. **Point-in-time control is partial.** The bi-temporal store limits leakage through its own queries,
   not through what an agent learns elsewhere.
7. **Indian filings are read from a rendered page.** The reader matches labels, so a change in NSE's
   rendering surfaces as missing items; the XBRL instance itself is not yet read.

---

## 10. Conclusion

Līlāvatī separates what a language model should do in finance (read, plan, write) from what code should
do (compute, check, cite), and makes the boundary checkable: engines carry their validation status,
identities are checked exactly with a diagnosis when they fail, and citations are resolved against what
was read. The first real-model evaluation on 10-Ks found the checker's own faults before it found any
model's, and showed that the remaining risk lies in figures no identity covers. Measuring the repair
step on harder inputs, checking the remaining engines and reading the Indian XBRL instance are the next
steps.

**Code and data.** The code, tests, validation pages and results are at
[https://github.com/revendrat/lilavati](https://github.com/revendrat/lilavati) under the Apache License
2.0; results files are under CC BY 4.0.

**Use of AI tools.** The software and this text were developed with AI coding assistants under the
author's direction. The author reviewed the text, the code and every reference, and takes responsibility
for the contents. <!-- AUTHOR TO CONFIRM: wording and extent of AI use (arXiv asks authors to report significant use). -->

---

## References

Almgren, R., & Chriss, N. (2000/2001). Optimal execution of portfolio transactions. *Journal of Risk*, *3*(2), 5–39. https://doi.org/10.21314/JOR.2001.041

Altman, E. I. (1968). Financial ratios, discriminant analysis and the prediction of corporate bankruptcy. *The Journal of Finance*, *23*(4), 589–609.

Araci, D. (2019). *FinBERT: Financial sentiment analysis with pre-trained language models* (arXiv:1908.10063). arXiv.

Bailey, D. H., Borwein, J. M., López de Prado, M., & Zhu, Q. J. (2017). The probability of backtest overfitting. *Journal of Computational Finance*, *20*(4). https://doi.org/10.21314/JCF.2016.322

Bailey, D. H., & López de Prado, M. (2014). The deflated Sharpe ratio: Correcting for selection bias, backtest overfitting and non-normality. *The Journal of Portfolio Management*, *40*(5), 94–107. <!-- VERIFY: DOI 10.3905/jpm.2014.40.5.094; the worked example was checked against López de Prado (2015) slides, not the article itself. -->

Beneish, M. D. (1999). The detection of earnings manipulation. *Financial Analysts Journal*, *55*(5), 24–36.

Bjørner, N., Phan, A.-D., & Fleckenstein, L. (2015). νZ - An optimizing SMT solver. In *Tools and Algorithms for the Construction and Analysis of Systems (TACAS 2015)* (Lecture Notes in Computer Science, Vol. 9035, pp. 194–199). Springer. https://doi.org/10.1007/978-3-662-46681-0_14

Black, F., & Litterman, R. (1992). Global portfolio optimization. *Financial Analysts Journal*, *48*(5), 28–43.

Chen, Z., Chen, W., Smiley, C., Shah, S., Borova, I., Langdon, D., … Wang, W. Y. (2021). FinQA: A dataset of numerical reasoning over financial data. In *Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing* (pp. 3697–3711). <!-- VERIFY: complete the author list from the paper (APA lists up to 20 authors). -->

Colebrooke, H. T. (Trans.). (1817). *Algebra with arithmetic and mensuration from the Sanscrit of Brahmegupta and Bhascara*. John Murray.

de Moura, L., Kong, S., Avigad, J., van Doorn, F., & von Raumer, J. (2015). The Lean theorem prover (system description). In *Automated Deduction – CADE-25* (Lecture Notes in Computer Science, Vol. 9195). Springer. https://doi.org/10.1007/978-3-319-21401-6_26

De Moura, L., & Bjørner, N. (2008). Z3: An efficient SMT solver. In *Tools and Algorithms for the Construction and Analysis of Systems (TACAS 2008)* (pp. 337–340). Springer.

Engle, R. F., & Granger, C. W. J. (1987). Co-integration and error correction: Representation, estimation, and testing. *Econometrica*, *55*(2), 251–276.

Garcez, A. D., Gori, M., Lamb, L. C., Serafini, L., Spranger, M., & Tran, S. N. (2019). Neural-symbolic computing: An effective methodology for principled integration of machine learning and reasoning. *Journal of Applied Logics*, *6*(4), 611–631.

Hagan, P. S., Kumar, D., Lesniewski, A. S., & Woodward, D. E. (2002). Managing smile risk. *Wilmott Magazine*, September, 84–108.

López de Prado, M. (2018). *Advances in financial machine learning*. John Wiley & Sons.

López de Prado, M., & Bailey, D. H. (2021). The false strategy theorem: A financial application of experimental mathematics. *The American Mathematical Monthly*, *128*(9). https://doi.org/10.1080/00029890.2021.1965068

Malo, P., Sinha, A., Korhonen, P., Wallenius, J., & Takala, P. (2014). Good debt or bad debt: Detecting semantic orientations in economic texts. *Journal of the Association for Information Science and Technology*, *65*(4), 782–796.

Manhaeve, R., Dumancic, S., Kimmig, A., Demeester, T., & De Raedt, L. (2018). DeepProbLog: Neural probabilistic logic programming. In *Advances in Neural Information Processing Systems 31* (pp. 3749–3759).

Merton, R. C. (1974). On the pricing of corporate debt: The risk structure of interest rates. *The Journal of Finance*, *29*(2), 449–470.

Nelson, C. R., & Siegel, A. F. (1987). Parsimonious modeling of yield curves. *The Journal of Business*, *60*(4), 473–489.

Patwardhan, K. S., Naimpally, S. A., & Singh, S. L. (2001). *Līlāvatī of Bhāskarācārya: A treatise of mathematics of Vedic tradition*. Motilal Banarsidass.

Paulson, L. C. (1994). *Isabelle: A generic theorem prover* (Lecture Notes in Computer Science, Vol. 828). Springer.

Reiter, R. (1987). A theory of diagnosis from first principles. *Artificial Intelligence*, *32*(1), 57–95.

Schick, T., Dwivedi-Yu, J., Dessì, R., Raileanu, R., Lomeli, M., Zettlemoyer, L., … Scialom, T. (2023). Toolformer: Language models can teach themselves to use tools. In *Advances in Neural Information Processing Systems 36*. <!-- VERIFY: complete the author list from the paper. -->

Tirumalsety, R. (2026). *Līlāvatī-Bench: A pilot benchmark of numerical fidelity and tool use for financial language-model agents* [Working paper]. https://github.com/revendrat/lilavati/blob/main/docs/papers/02_benchmark_paper.md

Wu, S., Irsoy, O., Lu, S., Dabravolski, V., Dredze, M., Gehrmann, S., … Mann, G. (2023). *BloombergGPT: A large language model for finance* (arXiv:2303.17564). arXiv. <!-- VERIFY: complete the author list from the paper. -->

Yang, H., Liu, X.-Y., & Wang, C. D. (2023). *FinGPT: Open-source financial large language models* (arXiv:2306.06031). arXiv.

Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. In *International Conference on Learning Representations (ICLR 2023)*.

Zhu, F., Lei, W., et al. (2021). TAT-QA: A question answering benchmark on a hybrid of tabular and textual content in finance. In *Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing* (Vol. 1, pp. 3277–3287). <!-- VERIFY: complete the author list from the paper. -->
