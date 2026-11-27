# Contributing guide

Līlāvatī is useful only if its numbers are right, so contributions are small, checkable and tested
against independent references. This page gets you from a fresh clone to a merged pull request. The
full rules are in [CONTRIBUTING.md](https://github.com/revendrat/lilavati/blob/main/CONTRIBUTING.md)
and the [developer skill](https://github.com/revendrat/lilavati/blob/main/.claude/skills/lilavati-dev/SKILL.md).

## 1. Set up and run the checks

```bash
git clone https://github.com/revendrat/lilavati.git && cd lilavati
uv sync --extra dev --extra docs
uv run ruff check src tests scripts examples
uv run mypy src
uv run pytest
```

Before you open a pull request, also run what CI runs on documentation:

```bash
uv run mkdocs build --strict                 # docs build
uv run python scripts/check_claims.py        # no proof, guarantee or maturity language
uv run python scripts/check_tutorials.py     # tutorial and guide code runs as written
```

Or run everything at once, with a one-line result per check:

```bash
uv run python scripts/check_all.py           # add --fast to skip the docs build and the tutorials
```

## 2. Pick a first contribution

These are real open items from the [validation pages](validation/index.md) and the
[roadmap](https://github.com/revendrat/lilavati/blob/main/ROADMAP.md), roughly in order of size.
`uv run python scripts/next_goal.py` lists every open item in `TODO.md` that is not waiting on the
maintainer, reviewers, budget or a download, ranked; comment on the issue (or open one) before you start.

| Task | Where | What "done" means |
| :--- | :--- | :--- |
| Clear error when the Nelson-Siegel start guess is out of bounds (opaque scipy error) | `core/fixed_income.py` | `ValueError` naming the bad input, and a test |
| Audit the order-book metrics (spread, microprice, order-flow imbalance) | `core/execution.py` | reference tests citing the definitions, a validation page |
| Audit Black-Litterman against a published worked example | `core/execution.py` | reference test with the source cited, validation page |
| Audit HRP against López de Prado (2016) | `core/execution.py` | reference test, validation page |
| Add a KPSS stationarity test | `core/econometrics.py` | engine function, reference test against statsmodels and a textbook value, MCP tool |
| Use `net_income` in the three-statement check (retained-earnings roll-forward) | `core/invariants.py` | new identity, tests including an at-limit case |
| Add `effective_tax_rate` (income tax / pretax income) to `filing_ratios` | `connectors/sec_filing.py` | function and a test on the Apple fixture with the value from the 10-K |
| Run the SEC pilot on companies from one sector and report what is missing | `scripts/validate_sec_filings.py` | a row per company on the [connectors page](validation/connectors.md), from the script's output |
| Improve a tutorial exercise, or add one | `docs/tutorials/` | the code runs under `check_tutorials.py` |

Comment on (or open) an issue before a large change, so work is not duplicated.

## 3. Write the test first

For a bug, write a test that fails on the current code, then fix it. For numeric code, test against
an **independent** reference (a textbook worked example, the original paper, or QuantLib), never
against the implementation itself, and cite the source next to the expected value. A template,
modelled on `tests/reference/test_forensics_reference.py`:

```python title="tests/test_my_reference.py"
"""Reference test for the Altman Z-score.

Source: Altman (1968), J. Finance 23(4): Z = 1.2 X1 + 1.4 X2 + 3.3 X3 + 0.6 X4 + 0.999 X5.
"""

import pytest

from lilavati.agents.forensics import ForensicEngine


def test_hand_computed_z() -> None:
    # X = (0.1, 0.2, 0.1, 1.5, 1.2) -> 0.12 + 0.28 + 0.33 + 0.90 + 1.1988 = 2.8288 (grey zone)
    r = ForensicEngine.calculate_altman_z_score(
        working_capital=100.0, total_assets=1000.0, retained_earnings=200.0, ebit=100.0,
        market_value_equity=900.0, total_liabilities=600.0, sales=1200.0)
    assert r.z_score == pytest.approx(2.8288, abs=1e-12)
    assert r.distress_zone == "Grey"
```

Add edge cases too: a value exactly at a threshold (floating point makes `2.1 / 0.7` equal
`3.0000000000000004`), non-finite or zero inputs, and the units the docstring promises. The
[developer skill](https://github.com/revendrat/lilavati/blob/main/.claude/skills/lilavati-dev/SKILL.md)
lists every rule with the real bug behind it.

## 4. Document what you changed

- **Units and conventions** in the docstring (decimals, compounding, day count, per-period or annual).
- **A validation page row** for each function you check against a reference: check, reference, measured tolerance, status
  (`docs/validation/<engine>.md`).
- **A tutorial** for any user-facing feature, or an update to the one it changes.
- **The changelog** (`CHANGELOG.md`, under Unreleased).
- **No number you did not produce.** Quote measured values from code you ran or a primary source;
  link to `results/ANALYSIS.md` or a validation page rather than copying numbers.

## 5. Using an AI coding agent

You are welcome to. Point the agent at the developer skill (`.claude/skills/lilavati-dev/SKILL.md`;
Claude Code loads it automatically) and, for benchmark work, `.claude/skills/lilavati-bench/`. Then
review its claims yourself: re-run the tests and the commands it reports. Several bugs in this
repository were found by checking an agent's report against the code.

## 6. Open the pull request

Use a Conventional Commit title (`fix(forensics): clear error for zero total assets`), fill in the
pull request template (formula and reference, test evidence), and keep one logical change per pull
request. CI runs everything in sections 1 and 3 on Python 3.11 and 3.12.

How it is reviewed: open pull requests are reviewed as part of the maintainers' daily routine. The
reviewer checks out your branch, runs your new tests against `main` (a fix's tests should fail there)
and against your branch (they should pass), runs the checks and the code that calls what you changed,
and posts a review listing what was checked and any findings, each marked blocking or optional. A pull
request with no blocking finding and green CI is merged; optional findings do not hold it up.

Questions: open a GitHub issue. Security problems: report privately (`SECURITY.md`).
