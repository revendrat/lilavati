# Līlāvatī to-do: from validated toolkit to verifiable financial intelligence

Working plan from the strategy review of 2026-11-21. The phase summary is in [ROADMAP.md](ROADMAP.md)
(Phases 8–12); this file holds the detail. Every phase ends in a **gate**: measurable evidence that
must exist before the next phase starts, so ambition never runs ahead of proof.

**Mission:** verifiable intelligence for finance. Probabilistic cognition, deterministic computation,
verifiable evidence, reproducible conclusions. One validated engine shared by learners, practitioners,
researchers and AI engineers.

## Principles adopted from the review

- [ ] Publish the **layered guarantees** table in the README and every release note:

  | Layer | Guarantee |
  | :--- | :--- |
  | Financial calculation | Deterministic for fixed inputs, configuration and pinned dependencies, within stated tolerances |
  | Formal invariants | Checked by Z3 on the given numbers; failed identities diagnosed (candidate figures); two covenants decided over input ranges |
  | Data provenance | Traceable to identified sources (document hash, page, tag) |
  | Point-in-time queries | No observation later than the requested cutoff |
  | Agent execution | Reproducible plan and tool trace |
  | LLM reasoning | Evaluated and calibrated, not guaranteed deterministic |
  | Research conclusion | Evidence-supported, with uncertainty disclosed |

- MCP is the interoperability layer, not the product; Līlāvatī stays a tool layer for LangGraph,
  Google ADK and others, not a competing framework.
- Open code is not open data: every dataset states source, licence, retrieval method, version,
  limitations; where redistribution is not allowed, publish ingestion scripts instead of data.
- Every user-facing feature ships with a tutorial and, for workflows, a skill (see the dev skill).

## Corrections to the brainstorm (decided)

- **Multi-agent protocol as a library, not an orchestrator.** Plan validation against a tool
  registry, typed hand-off contracts and an evidence ledger, used inside LangGraph/ADK.
- **India-first data needs per-source licence checks.** *To verify before any doc states it:*
  redistribution terms of NSE/BSE market data, MCA filings, RBI DBIE, and third-party copyright on
  individual FRED series. Licence-clean starting points to confirm: SEC EDGAR, World Bank, ALFRED.
  Checked 2026-11-26: NSE's website terms of use prohibit systematic or automated data collection
  (scraping, extraction, harvesting) without NSE's written consent, and NSE sells the complete XBRL
  series by subscription; BSE's terms not yet read.
- **Decimal arithmetic only where it matters** (money, accounting identities; Z3 already uses exact
  rationals). Floating-point models (Black-Scholes, GARCH, optimisers) get stated tolerances instead.
- **Replay consistency is defined within a tolerance** on pinned dependencies (solvers can differ in
  the last digits across BLAS builds and platforms).
- **Education/conceptual-competency track deferred** until rubrics and human graders exist.
- **External benchmark facts must be verified before citing** (FinToolBench tool/question counts,
  QuantEval arXiv id, FinanceBench and Finance Agent Benchmark details).
- **Added:** contamination control (private held-out seed; keep it off free tiers that train on
  prompts) and project sustainability (domain reviewers, contributor ladder, funding).

## External review of 2026-11-25: decisions

An outside review (written from the docs site, the README and a file listing, not the code) was
checked against the repository. Adopted items are placed in the phases below; the rest, with reasons:

| Suggestion | Decision |
| :--- | :--- |
| One machine-readable capability and validation manifest rendered into README and docs | **Adopted** (Phase 8): the docs home pillar table shows no validation status while the README table does |
| Validation status returned by every MCP tool | **Adopted** (Phase 8), with our own status levels tied to the validation pages |
| Validation page for execution | **Adopted** (Phase 8): Almgren-Chriss was checked against the paper but has no page |
| Typed quantities (scale, instant or duration, accounting basis, consolidation scope) | **Adopted** into the `VerifiedResult` contract (Phase 9) |
| Provenance of derived outputs (inputs' citations, engine version, checks run) | **Adopted** into the evidence ledger (Phase 9) |
| Z3 beyond point checks: unsat cores fed back to the agent; symbolic covenant cure with `z3.Optimize` | **Adopted** (Phase 9). Point checks on concrete numbers do not need an SMT solver; Z3 earns its place on symbolic questions |
| Purged and combinatorial purged CV with Deflated Sharpe Ratio and probability of backtest overfitting | **Adopted** (Phase 9, with 7.4) |
| Calendar and Durrleman density conditions for volatility surfaces | **Adopted** (Phase 9) |
| Process-level benchmark metrics: tool-output faithfulness, unit traps, injected instructions in filing text, cost and latency | **Adopted** (Phase 9) |
| Counterfactual twins to estimate parametric look-ahead; restatement cases; a post-cutoff split | **Adopted** (Phase 10) |
| US GAAP and Ind AS comparability adjustments (leases, cash-flow classification) | **Adopted** (Phase 10), after checking the standards' text |
| Macro-financial pillar on vintage data | **Adopted** as a staged track after the vintage connectors (Phases 10–11) |
| Static trace viewer for teaching and audit | **Adopted** (Phase 12) |
| Common filing-connector interface across XBRL, HTML and PDF | **Adopted** with roadmap 1.5 |
| Move raw benchmark replies out of Git | **Not adopted**: they are the published evidence (1.1 MB, checked against the manifest in CI); the Zenodo snapshot will archive them as well |
| Merge `runtime/` into `framework/` | **Not adopted**: not a duplicate; `framework.FinancialAgent` wraps `runtime.NeuroSymbolicAgent`. Document the layering instead |
| Move result models into `schemas/` | **Not adopted**: cosmetic; the Pydantic result models exist in each engine module |
| README still says "Five Pillars" | Not found in the README; the real drift is covered by the manifest item |
| PyPI release now | Deferred by the maintainer until reviewer feedback |

## Gap analysis (brainstorm item → what exists → gap)

| Item | Exists | Gap |
| :--- | :--- | :--- |
| `VerifiedResult` contract | `SourcedValue`, `CitationRef`, `InvariantCheckResult`, `AgentOutput.completed` | One result type: value, unit, currency, method and engine version, input hashes, status VERIFIED / UNVERIFIED / FAILED / NOT_APPLICABLE |
| Evidence ledger, replay | Tracer spans; tool-arm records store every tool call and output; results manifest with content hashes | Claim-level ledger; re-executing a recorded trace and comparing within tolerance |
| Typed plans / DAG | `core/graph.py` statement DAG; `FinancialState`, `FinancialStateGraph` | Validate an LLM-proposed plan against an allowlisted tool registry |
| Point-in-time | Bi-temporal DuckDB store; TPI partial | Vintage sources (ALFRED); poisoned-corpus track (roadmap 7.15) |
| Data connectors | SEC EDGAR XBRL, 10-K PDF parser, Ind AS crosswalk, market-data normalisation | Live validation (7.5); FRED/ALFRED, World Bank, RBI connectors |
| Ontology | Ind AS crosswalk | Canonical metric ids mapped across US GAAP, IFRS, Ind AS |
| Benchmark | 7-track harness; generator for 5 tracks; no-tool and tool arms; manifest, CIs, paired tests | Real-document cases, abstention cases, multi-agent track, scale (7.13c) |
| Multi-agent | Adversarial committee; MCP servers; LangGraph/ADK/A2A examples | A measured architecture comparison |
| Academy | Tutorials 01, 05–07 at the standard; draft course; two skills | Tutorials 02–04 retrofit; tutorial code run in CI |
| Numerical precision | Z3 exact rationals for identities; tolerance rules in the dev skill | Written rounding and tolerance policy per engine |
| Model governance | Validation pages for audited engines | Remaining audits; assumption registry; intended use and limitations per engine |

## Phase 8 (about 4 weeks): earn credibility, v0.2

- [~] Finish Phase 7 blocking items (2026-11-22):
    - [x] CI runs the strict docs build, every example, tutorial code, claims linter and manifest check.
    - [x] Claims linter and sweep of README, docs, docstrings and examples (7.8, language part).
    - [x] Release workflow (Trusted Publishing, clean-install smoke test) and docs deploy workflow.
    - [x] GitHub Pages enabled (source: GitHub Actions) and `pypi` environment created, tag-restricted (7.10, 7.11).
    - [ ] Maintainer: register the PyPI trusted publisher (7.10). *Blocked: maintainer action (PyPI deferred).*
    - [x] Author name and ORCID in `pyproject.toml`, `CITATION.cff` and the papers (7.12).
    - [x] Framework paper sections 6–7 traced to scripts; Table 1 venues verified and corrected (7.8).
    - [x] All 27 unique reference entries verified against primary sources; 9 corrected or removed (7.8).
- [x] Tutorials 02–04 retrofitted and executed in CI (7.24, 2026-11-22).
- [x] Paired tool/no-tool runs on four Groq models, recorded in the benchmark paper §5.3 (2026-11-22).
- [x] Units in every MCP tool description (2026-11-24; `tests/test_mcp_registry.py` checks it).
- [ ] Tool prompt t3: re-run the tool arm with 3+ samples on the new descriptions; analyse
      `rejected_output` of malformed calls (vega per vol point caused a double division). *Blocked: needs API
      budget; after reviewer feedback, together with benchmark v2 (Phase 9).*
- [ ] Zenodo DOI for the release (7.13b). *Blocked: maintainer action (Zenodo deferred).*
- [ ] External review: one practitioner, one software reviewer (7.17). *Blocked: waiting for the reviewers contacted on 2026-11-24.*
- [x] One machine-readable validation-status manifest for every engine and MCP tool
      (`lilavati.validation_status`); the docs home pillar table and `docs/validation/status.md` are
      generated from it; tests check README rows agree (2026-11-25, review 2026-11-25).
- [x] Every MCP tool result carries its engine's validation status, open items and page (2026-11-25).
- [x] Validation page for execution: the Almgren-Chriss checks against Almgren and Chriss (2000) and the
      fixes; order book, Black-Litterman and HRP listed as open (#14–#16) (2026-11-25).
- **Gate:** v0.2 tagged; every number in README, docs and papers traceable to `results/manifest.json`
  or a validation page.

## Alpha release gate (v0.2)

Do not tag, publish or announce until every item below is true; then ask the maintainer to confirm.

- [x] Claims linter clean and every remaining number traced (7.8).
- [x] Tutorials 01–07 at the tutorial standard and executed in CI (7.24).
- [x] `results/manifest.json` current; benchmark paper numbers match `results/ANALYSIS.md`.
- [x] Author and ORCID (7.12); Pages enabled (7.11); `pypi` environment (7.10); commits on
      `release/v0.2.0`, PR #1 (2026-11-22).
- [x] PR #1 merged with CI green on `main` (b899560); docs site live.
- [ ] PyPI trusted publisher registered by the maintainer (7.10), then tag `v0.2.0`. *Blocked: maintainer action (PyPI deferred).*
- [x] Release candidate artifacts built and verified locally (2026-11-22, `dist/`, see `dist/VERIFICATION-0.2.0.md`).
- [ ] Maintainer go-ahead for the release. *Blocked: maintainer decision.*

## Public announcement readiness (reviewed 2026-11-22)

**Must do before announcing**
- [x] Install path for early users: `pip install "lilavati-finance @ git+https://github.com/revendrat/lilavati@main"`
      (checked in a clean Python 3.12 environment, 2026-11-23; README and getting-started updated).
- [ ] PyPI release deferred by the maintainer (2026-11-23) until reviewer feedback and the LinkedIn
      announcement are in. Do not push a `v*` tag before the trusted publisher is registered: it
      triggers `release.yml`, whose PyPI upload would fail (7.10, 7.18). *Blocked: deferred by the maintainer.*
- [ ] External review by one practitioner and one software reviewer (7.17), or announce explicitly as
      "alpha, seeking review" and link the known limitations. Reviewer email and LinkedIn drafts written
      2026-11-23 (maintainer sends them). *Blocked: waiting for the reviewers contacted on 2026-11-24.*
- [ ] Announcement text and channels (not drafted yet); link the docs site, getting-started page and
      known limitations. *Blocked: after reviewer feedback (the release announcement).*
- [x] First-contribution tasks opened as GitHub issues (2026-11-23): #6–#13 `good first issue`,
      #14–#16 `help wanted` (engine audits).
- [x] First outside contributions merged (2026-11-24): #6 and #7 fixed in PRs #23 and #24; tasks
      removed from the contributing guide's list.

**Recommended at or soon after the announcement**
- [ ] Zenodo DOI for the release (7.13b), so researchers can cite a fixed snapshot. *Blocked: maintainer action (Zenodo deferred).*
- [x] Branch protection on `main` (2026-11-23): CI jobs test (3.11), test (3.12) and docs-and-evidence
      required, also for admins; no force pushes or deletion.
- [x] GitHub repository description and topics (2026-11-23): description matches the docs site
      (no "audited" or "institutional"), homepage is the docs site, 20 topics.
- [ ] Optionally enable GitHub Discussions for questions. *Blocked: maintainer action (GitHub settings).*

**Disclosed limitations (follow-up work, not blockers)**
- [ ] Remaining engine audits: order book (open to contributors as #14), Black-Litterman, HRP, connectors
      (7.3). *Due: 2026-12-01 for Black-Litterman and HRP: check issues #15 and #16 first; if unclaimed,
      audit both.*
- [x] Statement graph slice of the engine audits (2026-11-27): no equity plug (the balance check held for
      any input), CFO includes the working-capital changes, retained earnings roll forward, the opening
      balance sheet must balance, scenario branches keep every driver (they dropped receivable and payable
      days), the research agent opens the graph at the filing's balance sheet. Hand-checked
      (`docs/validation/statement_graph.md`); still not reference-checked.
- [ ] Statement graph: check against a published three-statement worked example, and model the lines it
      holds constant (debt issuance and repayment, dividends and buybacks, inventory).
- [ ] Tutorial for the statement graph and the scenario tree (no tutorial covers them): an opening
      balance sheet, a driver shock, what the balance check tests, and a wiring fault that fails it.
- [ ] Live-data validation of the connectors (7.5): SEC XBRL piloted on five companies. Open here: 10-Qs
      (cash flows are year to date) and banks (their own statement template). The 10-K PDF parser's second
      issuer and a second Ind AS company are separate items below, blocked on downloads.
- [x] Fiscal-year three-statement path now filing-anchored, without placeholders (2026-11-23).
- [x] Ind AS crosswalk and 10-K PDF parser: no zero-fill or substitutes; real cash and balance checks
      (2026-11-23).
- [ ] Pluggable PDF parser connectors (roadmap 1.5): a backend interface so pypdf, pdfplumber, layout and
      OCR parsers share the statement mapping and checks; per-backend validation on the same filings; one
      filing-connector interface across XBRL, HTML and PDF. *Blocked: after reviewer feedback.*
- [x] Ind AS crosswalk on real audited results, line by line against the printed statements (7.5;
      2026-11-24: Maruti Suzuki FY2025-26 consolidated; all checks hold; the exchange filing folds
      right-of-use assets into PP&E).
- [ ] Ind AS (roadmap 1.3): a standalone statement and a second company (the exchange's filing is now read directly,
      `connectors/nse_integrated_filing.py`; plan under "India exchange XBRL" in Phase 10). *Blocked: needs filings downloaded by hand by the maintainer.*
- [ ] 10-K PDF parser on a second issuer (labels are Apple's today) (7.5); list prior-year items not found
      (only current-year items are in `missing_items`); footnote markers such as "(1)" after a label are
      read as −1. *Blocked: needs a second issuer's 10-K PDF downloaded by hand (the second sample PDF is Apple's again).*
- [x] `ProvenanceGate(store)` resolves citations against a `SourceStore` of the sources read (2026-11-23);
      without a store it still checks the form only.
- [x] `FinancialResearchAgent` builds its dossier from one 10-K's reported figures (2026-11-24); live on
      Apple, Microsoft, Walmart and Nvidia (Nvidia rejected by the Beneish growth effect; see
      docs/validation/forensics.md).
- [ ] Larger evidence base, real-document, look-ahead and multi-step tracks (7.13c, 7.14–7.16).
- [ ] Scheduled live-model CI job (7.21b); live Anthropic tool-calling run (7.22). *Blocked: needs a CI secret and an Anthropic API key.*

## Phase 9 (months 1–3): contracts and evidence

- [ ] `VerifiedResult` contract on top of `SourcedValue`; adopt it in all MCP servers. Typed quantities:
      currency, scale, instant or duration, accounting basis (US GAAP, Ind AS, IFRS, non-GAAP) and
      consolidation scope; adding a stock to a flow, or mixing scales or currencies without a dated FX
      citation, raises. (The Maruti exchange filing and Walmart's two revenue totals are the motivating
      cases.)
- [ ] Evidence ledger built from tool traces; replay of a recorded trace with tolerance comparison. Derived
      outputs carry their inputs' citations, the engine version and commit, and the checks run (a
      provenance graph; W3C PROV serialisation optional).
- [x] Z3 beyond point checks (2026-11-25): `diagnose_identities` (MaxSMT: smallest sets of figures that
      explain every failed identity, with implied values; an unsat core for explanation), fed to the
      reflection prompt by `SMTBalanceGate`; `minimum_debt_repayment` (exact optimum meeting leverage and
      coverage together, `z3.Optimize`); `check_covenants_over_ranges` (no breach for any input in a box,
      or a counterexample). MCP tools; reference tests against closed forms and hand-solved cases.
- [x] Z3 multi-period covenant paths with linked inputs (2026-11-25): interest on each year's opening debt,
      amortisation, cash sweep (fixed or leverage grid), leverage step-downs, coverage and minimum
      liquidity over yearly EBITDA and rate ranges; smallest upfront repayment; corners can miss breaches.
- [ ] Z3 next: trailing-twelve-month EBITDA for quarterly tests, revolver draws, dividends and fixed-charge
      cover; equity-cure mechanics per a named credit agreement's definition.
- [x] Financial ML: purged and embargoed K-fold and combinatorial purged CV (7.4), with the Deflated
      Sharpe Ratio and the probability of backtest overfitting (2026-11-26; `core/backtest_overfitting.py`,
      two MCP tools, Tutorial 09). DSR reproduces the authors' worked example (0.9004); PBO matches
      Algorithm 2.3. Open: check the CV splits against AFML snippets 7.1-7.3 or skfolio (a test-only
      dependency needs approval); estimate the effective number of trials (correlated trials); the
      minimum track record length.
- [ ] Derivatives: static no-arbitrage across a surface: total implied variance non-decreasing in
      maturity (calendar) and the Durrleman density condition (verify Gatheral and Jacquier before citing).
- [ ] Agent workflows (roadmap 4.10, [docs/agent-workflows.md](docs/agent-workflows.md)): extraction with
      diagnosis-driven repair evaluated on the pilot 10-Ks with four models (2026-11-25, x1 and x2:
      checker and label faults fixed, then 240 of 240 correct in one pass, nothing to repair). Next: the
      same arms on inputs where models misread (PDF page text, 10-Q columns, Ind AS reports in lakhs or
      crores), plus the no-provenance-check ablation; build the covenant-monitoring agent (terms and guidance
      read with quotes, paths checked by tools); an answer gate rejecting numbers no tool or source
      produced. Record token usage in traces.
- [ ] Benchmark process metrics: whether the final answer quotes tool outputs unchanged (no re-rounding or
      unit drift), unit-trap and mixed-scale tables, instructions injected into filing text, and tokens,
      tool rounds and latency in the manifest (accuracy against cost).
- [ ] Benchmark v2: all 7 tracks generated, 20+ cases per track, 3+ samples per model, private seed.
      *Blocked: the bigger benchmark run needs API budget; after reviewer feedback.*
- [ ] Abstention cases (missing or contradictory inputs, where the right answer is "cannot conclude").
- [ ] Real-document cases: SEC EDGAR for 2 issuers and one Ind AS annual report (7.5, 7.14).
- **Gate:** a paired tool/no-tool result whose CI excludes zero on non-saturated cases, written up
  as a short paper (deterministic execution for probabilistic financial agents).

## Phase 10 (months 3–6): narrow data commons, driven by the benchmark

- [ ] Licence review per source (see corrections); record the result in a dataset card.
- [ ] Connectors (roadmap 1.2): SEC EDGAR company facts (filing-anchored extraction done, 2026-11-23), ALFRED vintages,
      World Bank, RBI DBIE and MOSPI release snapshots (licence check first). *Blocked: after reviewer feedback.*
- [ ] **India exchange XBRL** (outside review, assessed 2026-11-26). Facts checked: SEBI's Integrated
      Filing circular of 31 Dec 2024 (Governance in XBRL only from the quarter ended March 2025;
      Financial within 45 days of a quarter, 60 after the year); BSE made XBRL results mandatory from
      1 April 2017; MCA's Ind AS filing manual allows no extensions to the core taxonomy; MCA exempts
      banks, insurers, NBFCs and housing finance companies from XBRL financial statements. Confirmed
      from NSE's taxonomy archive (2026-11-26): SEBI's Integrated Filing Finance Taxonomy is
      `in-capmkt`, version 1.0 of 2025-01-31, 507 elements, with sections for the results, the
      statement of assets and liabilities and direct and indirect cash flows; the Maruti filing for
      the year tags all three. NSE's `..._iXBRL_WEB.html` link is a page rendered from the XBRL
      (labels, no tags), not inline XBRL. Not confirmed, do not repeat until checked: "~893" BRSR tags,
      the power-sector exemption (MCA's FAQ and the rule text disagree), whether insurers now file
      results in XBRL. Scope 3 is, as far as known, a voluntary (leadership) BRSR indicator: check the
      format before relying on it. Steps:
  - [ ] Access: ask NSE and BSE for written consent or a research licence, including permission to keep
        one or two filings as test fixtures; read BSE's terms. Until then no fetcher: the reader takes a
        file the user supplies, real filings stay in git-ignored `data/raw/`, and committed tests use
        synthetic pages. *Blocked: maintainer outreach to NSE and BSE.*
  - [x] Reader for NSE's rendered page (`connectors/nse_integrated_filing.py`, 2026-11-26): sections,
        columns, headings, Indian digit grouping; labels mapped to the crosswalk; nothing filled; every
        figure cited to the page's hash. Maruti FY2026 consolidated: 26 of 26 earlier manual readings
        and 26 of 28 printed items equal (two definitional differences reconciled); identities hold.
        Tutorial 10.
  - [ ] The XBRL instance itself (element names and contexts, no label table), if NSE publishes it
        for download: ask the maintainer to look for an XML link on the filing's row. *Blocked: maintainer to look for the XML.*
  - [ ] Maruti's standalone filing and a second company (another sector); a quarterly (non-Q4) filing,
        whose balance sheet and cash flows are half-yearly. *Blocked: needs filings downloaded by hand by the maintainer.*
  - [ ] Banking, NBFC and insurance formats (their own taxonomies in NSE's archive). *Blocked: needs filings downloaded by hand by the maintainer.*
  - [ ] Point in time: the submission time from NSE's file name as knowledge time (read, not yet used
        by the bi-temporal store); re-filed results become restatement cases (below).
  - [ ] BRSR XBRL reader for the sustainability engine: Scope 1 and 2 emissions, energy and water, with
        units and the reporting boundary; element names from the BRSR taxonomy (in NSE's archive,
        versions 2023-06-30 to 2025-05-31); BRSR Core assurance flag; validate two companies against
        their BRSR PDFs. *Blocked: needs BRSR filings downloaded by hand by the maintainer.*
  - [ ] MCA AOC-4 XBRL (full statements with notes): deferred. No free bulk access found (paid per
        document on MCA V3); revisit if MCA grants research access. *Blocked: no access to MCA filings.*
  - [ ] An MCP tool for the reader (it would need the page's content or a path under `data/raw/`).
- [ ] Typed macro series (frequency, unit, nominal or real, base year, seasonal adjustment,
      transformation, stock or flow, release time) and conversion tools (rebasing, SAAR and year-on-year,
      deflating); a release calendar so an observation is usable only after its publication time.
- [ ] Restatement cases: one period, two filing dates (10-K/A, Ind AS prior-period adjustments), as
      reported against as restated.
- [ ] Counterfactual twins for look-ahead: anonymised names, shifted dates, controlled perturbations; the
      accuracy gap between originals and twins estimates parametric leakage. A split built only from
      filings published after the evaluated models' cutoffs.
- [ ] Comparability adjustments between US GAAP and Ind AS where they differ (leases; classification of
      interest and dividends in the cash flow statement), checked against the standards' text first.
- [ ] Curated India set (about 20 companies) with provenance and licence notes per source. *Blocked: needs NSE/BSE consent and filings downloaded by hand.*
- [ ] Minimal ontology: about 30 canonical metrics used by the benchmark and tutorials, mapped
      across US GAAP, IFRS and Ind AS, with consolidated/standalone, audited/unaudited, reported/derived,
      restatement links.
- [ ] Point-in-time track with a poisoned corpus (7.15).
- **Gate:** a point-in-time leak measured on a real vintage dataset.

## Macro-financial track (after the vintage connectors; Phases 10–11)

- [ ] Identity checks on macro scenarios: sectoral balances, balance of payments, and government debt
      dynamics, with `z3.Optimize` for the debt-stabilising primary balance.
- [ ] Engines with reference checks (statsmodels and the original papers): Hamilton (2018) regression
      filter, local projections (Jordà 2005) with HAC errors, Taylor rules.
- [ ] Transmission into existing engines: a rate or inflation shock moves the Nelson-Siegel curve, then
      bond prices, covenant headroom and Merton default probability; a tutorial from a central-bank
      shock to a covenant breach.
- [ ] Benchmark track on vintages: questions whose answer changed between the first and a revised
      estimate. *Blocked: needs the vintage connectors (after reviewer feedback).*
- **Gate:** a look-ahead leak measured on real ALFRED or RBI vintages; each engine checked against a
  reference.

## Phase 11 (months 6–9): multi-agent reliability as research

- [ ] Architecture ladder on LangGraph with constant model, data, questions and budget: no tools;
      tools; two agents; committee; committee + verification; + point-in-time data.
- [ ] Plan validation against the tool registry; disagreement resolved by evidence, not majority.
- [ ] Measure accuracy, unsupported claims, cost per successful task, latency, replay consistency.
- **Gate:** pilot Līlāvatī Financial AI Reliability Report v0, with sample sizes stated.

## Phase 12 (months 9–12): Academy and community

- [ ] Three learning pathways (students, practitioners, researchers/AI engineers) built from the
      tutorials and course; executable lessons with a deliberately wrong AI answer to correct.
- [ ] Pilot the course with one university; collect instructor feedback. *Blocked: maintainer action.*
- [ ] Student benchmark competition on a private seed. *Blocked: maintainer action.*
- [ ] Static trace viewer (HTML from recorded tool traces) for grading student agents and for audit.
- **Gate:** outside contributors landing validated engines through the skills and review process.

## Enterprise-quality track (runs alongside all phases)

- [x] One goal per day (2026-11-26): `lilavati-daily` skill (open, pick, goal card, build, prove, close;
      a "go" on the card approves the merge once checks and CI pass); `scripts/next_goal.py` ranks the
      unblocked items here; `scripts/check_all.py` runs every check; `*Blocked:*` and `*Due:*` markers,
      a test checks that waiting items are marked.
- [ ] Semantic versioning; API stability and deprecation policy.
- [ ] Coverage reporting; CI for docs, examples, tutorial code and `scripts/` lint.
- [ ] Dependency vulnerability scanning, SBOM, signed releases.
- [ ] Authentication option for the API server; threat model for agent tool use (prompt injection
      from retrieved documents, tool permission boundaries).
- [ ] Maintainer team with CODEOWNERS per engine; response targets; release cadence. *Blocked: maintainer action.*
- [ ] Independent audit of the core engines before any "production" language. *Blocked: needs an outside auditor.*

## Decisions for the maintainer

1. Primary audience for the next 6 months: researchers (recommended), students or practitioners?
2. India as flagship geography: yes or no; who owns the licensing checks?
3. Capacity: solo or team; this decides whether Phases 10–12 run in sequence or in parallel.
4. Funding and partners: grants or a university partner would change the timeline.
