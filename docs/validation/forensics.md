# Validation: forensic scores (`agents/forensics.py`)

Audited 2026-11-19. Tests: `tests/test_beneish.py`, `tests/reference/test_forensics_reference.py`.

| Function | Check | Reference | Tolerance | Status |
| :--- | :--- | :--- | :--- | :--- |
| `calculate_beneish_m_score` | 8-variable coefficients; all indices 1 ⇒ M = −2.480 | Beneish (1999), FAJ 55(5) | 1e-9 | **fixed**: TATA 4.037 → 4.679, LVGI +0.0327 → −0.327 |
| `calculate_beneish_m_score` | TATA definition | Beneish (1999) | n/a | documented: uses (NI − CFO)/TA simplification, not the balance-sheet accruals definition |
| `calculate_altman_z_score` | hand-computed Z = 2.8288 (grey), 1.2295 (distress), safe case | Altman (1968), J. Finance 23(4) | 1e-12 | pass |
| `calculate_altman_z_score` | zero total assets/liabilities | n/a | n/a | **fixed**: previously raised `ZeroDivisionError`; now a `ValueError` naming the input (`tests/reference/test_forensics_reference.py`) |
| `calculate_altman_z_score` | NaN or infinite input; non-positive total assets, total liabilities, sales or market value of equity | n/a | n/a | **fixed**: a NaN score used to be classed "Safe" and negative totals gave a number; each case now raises a `ValueError` naming the input (`tests/reference/test_forensics_reference.py`) |

**On real 10-Ks (2026-11-24, `FinancialResearchAgent`, all inputs from the filing).** Apple FY2026
M = −2.52, Microsoft −2.64, Walmart −2.72; Nvidia FY2026 M = −1.15, above the −1.78 threshold. For
Nvidia the sales growth index (SGI = 215,938 / 130,497 = 1.65, weighted 0.892) contributes most,
with the asset quality index (1.52) and accruals (TATA 0.084). Beneish (1999) models rapid growth as
pressure to manipulate, so fast-growing companies can exceed the threshold without manipulation.
The screen is computed correctly; read a flag together with the indices behind it. Test:
`tests/test_advanced_agents.py::test_research_flags_high_growth_through_beneish`.
