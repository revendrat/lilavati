# Numerical validation

Status of the reference-value audit (roadmap item 7.3). One status per engine, also returned by every
MCP tool in its `validation` field: [validation status](status.md). Each engine page lists, per public function,
the check, the independent reference (textbook example, original paper, or QuantLib 1.44 used as a
test-only dependency), the worst error measured, and whether a bug was fixed. Reference tests live
in `tests/reference/`.

| Engine | Page | Bugs fixed in audit | Open items |
| :--- | :--- | :---: | :--- |
| Fixed income (bonds, Nelson-Siegel, Merton) | [fixed_income](fixed_income.md) | 1 (Merton solver returned non-solutions in distress) | fractional coupon periods silently rounded; NS start-guess bounds |
| Derivatives (BSM, Greeks, CRR, IV, SABR, butterfly) | [derivatives](derivatives.md) | 7 (incl. SABR near-ATM, `is_arbitrage_free`, butterfly ordering, invalid CRR probability) | American Greeks are European BSM Greeks; calendar arbitrage not checked |
| Invariants (Z3 identities, covenants) | [invariants](invariants.md) | 2 (covenant at-limit false breach; non-finite inputs) | `net_income` unused (no retained-earnings roll-forward) |
| Sustainability (WACI, carbon tax, SLB) | [sustainability](sustainability.md) | 3 (SLB at-target rounding; invalid weights; zero baseline) | none |
| Forensics (Beneish, Altman) | [forensics](forensics.md) | 2 (Beneish coefficients, fixed earlier; Altman zero-denominator error message) | none |
| Almgren-Chriss execution | [execution](execution.md) | 4 (clipped sinh held risk-averse schedules to the end; volatility in the wrong units; continuous instead of discrete solution; a stray factor 0.5 in the variance) | none |
| Portfolio (Black-Litterman, HRP) | [execution](execution.md); audits open (#15, #16) | 1 (Black-Litterman returned equal weights when the solver failed; the solver was never checked) | not yet checked against a published example; HRP clustering distance and cluster variance to be checked against López de Prado (2016) |
| Econometrics (ADF, Engle-Granger + OU half-life, GARCH) | [econometrics](econometrics.md) | 7 (GARCH p/q swapped; half-life used the ln2/(1−φ) shortcut; unconverged GARCH returned start values; collinear/constant/non-finite inputs; unchecked significance level) | percent-return inputs not detected; √252 daily assumption; MacKinnon tables checked via statsmodels/arch, not the paper |
| Financial ML (fractional differencing, d* search, triple barrier) | [financial_ml](financial_ml.md) | 11 (placeholder d*=1.0 when no solution; ignored target p-value; float grid overshoot; d* rounding; exact barrier touch missed; invalid inputs) | d>0 tested on a shorter sample than d=0 (as in AFML); fixed-% barriers only |
| Backtest statistics (Probabilistic and Deflated Sharpe ratios, PBO by CSCV) | [financial_ml](financial_ml.md#backtest-statistics-corebacktest_overfittingpy) | 1 (zero-variance trial passed the check: sum-of-squares variance; found in development) | the number of independent trials is the caller's estimate |
| Purged and embargoed K-fold, combinatorial purged CV | [financial_ml](financial_ml.md#purged-and-embargoed-cross-validation-corebacktest_overfittingpy) | n/a | not reference-checked: tested against the definitions, not AFML's code or a reference library |
| Filing connectors (10-K PDF parser, EDGAR XBRL, filing-anchored extraction, Ind AS crosswalk) | [connectors](connectors.md) | 6 (wrong tax line, dropped non-current debt, par value read as equity, missing item reported as 0.0, made-up SEC contact, comparative periods returned as current; three-statement model filled untagged fields and assumed cash reconciled; PDF parser and Ind AS crosswalk assumed cash reconciled and substituted missing items; Ind AS cost of goods sold and operating income mis-mapped) | 5-company pilot; banks need their own template; 10-Q supported but not validated (cash flows are year-to-date); restatements not covered; the three-statement model refuses filings without operating income (J&J, banks); Ind AS crosswalk checked on one company's annual results (Maruti Suzuki FY2026, consolidated); exchange filing folds right-of-use assets into PP&E; NSE Integrated Filing reader piloted on the same filing (26 of 28 printed items equal, two definitional differences) |
| Order book, Black-Litterman, HRP | [execution](execution.md), [status](status.md) | n/a | not yet audited (#14–#16) |
| Statement graph (and the scenario tree on it) | [statement graph](statement_graph.md) | 4 (equity plug made the balance check hold for any input; CFO left out working capital; retained earnings were one year's net income; scenario branches dropped receivable and payable days) | hand-checked, not checked against a published worked example; debt, dividends and inventory held constant |

The audit is not complete. Until every row is audited, treat unaudited engines as unvalidated.

Which library does what, how each solver result is checked, and how to cite the libraries: [libraries, solvers and citations](libraries.md).
