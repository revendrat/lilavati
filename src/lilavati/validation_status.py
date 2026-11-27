"""Validation status of every engine and MCP tool: the single source for docs and tool results.

Each engine has one status:

- ``reference-checked``: compared in tests with an independent reference (original paper, textbook,
  QuantLib, statsmodels), with a validation page stating the reference and the tolerance measured.
- ``piloted on real data``: checked against real filings named on its validation page; the pilot is
  small, so results outside it are not validated.
- ``rule-based``: a fixed decision rule over reference-checked components; no external reference
  applies to the rule itself.
- ``not reference-checked``: unit and property tests only. Treat results as unvalidated.

``docs/validation/status.md`` and the pillar table on the docs home page are generated from this
module (``scripts/render_validation_status.py``); every MCP tool result carries its engine's status
(``with_validation_status``), so an agent can tell a checked engine from an unchecked one.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal, TypeVar

Status = Literal["reference-checked", "piloted on real data", "rule-based", "not reference-checked"]

MEANING: dict[str, str] = {
    "reference-checked": "compared with an independent reference (paper, textbook or reference library) "
                         "within a stated tolerance",
    "piloted on real data": "checked against the real filings named on the validation page; a small pilot",
    "rule-based": "a fixed decision rule over reference-checked components",
    "not reference-checked": "unit and property tests only; treat results as unvalidated",
}
ICON: dict[str, str] = {"reference-checked": "✅", "piloted on real data": "🟡", "rule-based": "✅",
                        "not reference-checked": "🟡"}
DOCS_URL = "https://revendrat.github.io/lilavati/"
PILLARS = {
    "I": "Three-Statement Modeling & Accounting Checks",
    "II": "Fixed Income, Credit & Debt Covenants",
    "III": "Financial Econometrics & Stationarity",
    "IV": "Financial ML (de Prado Paradigm)",
    "V": "Derivatives, Volatility Surfaces & Greeks",
    "VI": "Market Microstructure, Execution & Portfolio",
    "VII": "Sustainable Finance & Climate Risk",
    "Filings & agents": "Filing Connectors, Forensics & Agents",
}


@dataclass(frozen=True)
class Engine:
    """One engine: what it is, where it lives, how far it is checked, and which MCP tools expose it."""

    key: str
    name: str
    pillar: str
    module: str
    status: Status
    page: str  # docs-relative path of the validation page
    tools: tuple[str, ...] = ()
    open_items: str = ""
    readme_row: str = ""  # a substring identifying the engine's row in the README capability table
    extra: dict[str, str] = field(default_factory=dict)


ENGINES: tuple[Engine, ...] = (
    Engine("invariants", "Accounting identities, diagnosis and covenant checks (Z3)", "I", "core/invariants.py",
           "reference-checked", "validation/invariants.md",
           ("diagnose_accounting_identities", "find_minimum_debt_repayment", "check_covenants_over_ranges"),
           open_items="the debt-repayment model assumes interest proportional to debt; ranges are independent",
           readme_row="Covenant checks (net leverage, interest coverage); smallest"),
    Engine("statement_graph", "Statement graph with driver shocks", "I", "core/graph.py",
           "not reference-checked", "validation/statement_graph.md",
           open_items="hand-checked; no published worked example yet; debt and dividends held constant",
           readme_row="Statement DAG with driver shocks"),
    Engine("bonds", "Bond price, durations, convexity, DV01", "II", "core/fixed_income.py",
           "reference-checked", "validation/fixed_income.md", ("analyze_bond",),
           open_items="maturities off the coupon grid are rounded (#27)",
           readme_row="Bond price, Macaulay/modified duration"),
    Engine("nelson_siegel", "Nelson-Siegel curve fit", "II", "core/fixed_income.py",
           "reference-checked", "validation/fixed_income.md", ("fit_yield_curve",),
           open_items="clearer error for an out-of-bounds start guess (#8)", readme_row="Nelson-Siegel curve fit"),
    Engine("merton", "Merton structural default model", "II", "core/fixed_income.py",
           "reference-checked", "validation/fixed_income.md", ("evaluate_credit_risk_merton",),
           readme_row="Merton structural default model"),
    Engine("covenant_paths", "Multi-period covenant paths (linked interest, cash sweep), over ranges (Z3)", "II",
           "core/covenant_paths.py", "reference-checked", "validation/invariants.md",
           ("check_covenant_path", "find_minimum_upfront_repayment_for_path"),
           open_items="annual periods; covenant EBITDA is the period's; a rate range can leave Z3 undecided",
           readme_row="Covenant checks (net leverage, interest coverage); smallest"),
    Engine("econometrics", "ADF, Engle-Granger with OU half-life, GARCH(p, q)", "III", "core/econometrics.py",
           "reference-checked", "validation/econometrics.md",
           ("analyze_stationarity", "analyze_cointegration", "fit_garch_volatility"),
           readme_row="ADF stationarity test"),
    Engine("financial_ml", "Fractional differencing, minimal-d search, triple barrier", "IV",
           "core/financial_ml.py", "reference-checked", "validation/financial_ml.md",
           ("find_optimal_fractional_diff", "apply_triple_barrier_labels"),
           readme_row="Fractional differentiation + minimal-d search"),
    Engine("backtest_statistics", "Probabilistic and Deflated Sharpe ratios, probability of backtest overfitting",
           "IV", "core/backtest_overfitting.py", "reference-checked", "validation/financial_ml.md",
           ("compute_deflated_sharpe_ratio", "estimate_probability_of_backtest_overfitting"),
           open_items="the number of independent trials is the caller's estimate",
           readme_row="Deflated Sharpe ratio"),
    Engine("purged_cv", "Purged and embargoed K-fold, combinatorial purged cross-validation", "IV",
           "core/backtest_overfitting.py", "not reference-checked", "validation/financial_ml.md",
           open_items="checked against the definitions, not yet against AFML's code or a reference library",
           readme_row="Purged and embargoed K-fold"),
    Engine("derivatives", "Black-Scholes-Merton, Greeks, CRR, implied vol, SABR, butterfly check", "V",
           "core/derivatives.py", "reference-checked", "validation/derivatives.md",
           ("price_european_option", "price_american_option", "calculate_option_greeks",
            "calibrate_sabr_volatility_model", "check_butterfly_arbitrage"),
           open_items="American Greeks are European BSM Greeks; calendar arbitrage not checked",
           readme_row="Black-Scholes price and Greeks"),
    Engine("almgren_chriss", "Almgren-Chriss liquidation schedule", "VI", "core/execution.py",
           "reference-checked", "validation/execution.md", ("compute_almgren_chriss_liquidation_schedule",),
           readme_row="Almgren-Chriss schedule"),
    Engine("order_book", "Order-book snapshot (spread, microprice, order-flow imbalance)", "VI",
           "core/execution.py", "not reference-checked", "validation/execution.md",
           ("analyze_order_book_microstructure",), open_items="reference audit open (#14)",
           readme_row="Order-book snapshot"),
    Engine("black_litterman", "Black-Litterman posterior and weights", "VI", "core/execution.py",
           "not reference-checked", "validation/execution.md", ("optimize_portfolio_black_litterman",),
           open_items="reference audit open (#15); weights checked against the closed form",
           readme_row="Black-Litterman (weights by CVXPY"),
    Engine("hrp", "Hierarchical risk parity", "VI", "core/execution.py", "not reference-checked",
           "validation/execution.md", ("optimize_portfolio_hierarchical_risk_parity",),
           open_items="reference audit open (#16); cluster variance by covariance trace",
           readme_row="solver status checked), hierarchical risk parity"),
    Engine("sustainability", "WACI, carbon-tax stress test, sustainability-linked bond", "VII",
           "core/sustainability.py", "reference-checked", "validation/sustainability.md",
           ("calculate_portfolio_carbon_intensity", "stress_test_carbon_tax_impact",
            "evaluate_sustainability_linked_bond_covenant"),
           readme_row="WACI, carbon-tax stress test"),
    Engine("forensics", "Beneish M-score, Altman Z-score", "Filings & agents", "agents/forensics.py",
           "reference-checked", "validation/forensics.md", ("compute_forensic_beneish_m_score",),
           open_items="Beneish flags fast growers"),
    Engine("committee", "Rule-based investment committee", "Filings & agents", "agents/committee.py",
           "rule-based", "validation/forensics.md", ("evaluate_investment_committee_memo",)),
    Engine("sec_xbrl", "SEC XBRL filing-anchored extraction and three-statement model", "Filings & agents",
           "connectors/sec_filing.py, connectors/edgar.py", "piloted on real data", "validation/connectors.md",
           ("get_filing_figures", "get_company_filing_statements", "extract_single_line_item"),
           open_items="5-company pilot; 10-Q, banks and restatements open",
           readme_row="SEC EDGAR XBRL: filing-anchored extraction"),
    Engine("pdf_10k", "10-K PDF parser", "Filings & agents", "connectors/pdf_10k.py", "piloted on real data",
           "validation/connectors.md", open_items="one filing (Apple FY2026); labels are Apple's"),
    Engine("ind_as", "Ind AS crosswalk", "Filings & agents", "connectors/india_filings.py", "piloted on real data",
           "validation/connectors.md", open_items="one company (Maruti Suzuki FY2025-26, consolidated)"),
    Engine("nse_integrated_filing", "NSE Integrated Filing (Financial) page reader, Ind AS", "Filings & agents",
           "connectors/nse_integrated_filing.py", "piloted on real data", "validation/connectors.md",
           open_items="one filing (Maruti Suzuki FY2025-26, consolidated); reads NSE's rendered page by label",
           readme_row="NSE Integrated Filing (Financial) reader"),
)

_BY_TOOL = {tool: e for e in ENGINES for tool in e.tools}


def status_for_tool(tool_name: str) -> dict[str, str]:
    """The ``validation`` block an MCP tool returns: status, its meaning, open items, the page URL."""
    e = _BY_TOOL[tool_name]
    out = {"status": e.status, "meaning": MEANING[e.status],
           "page": DOCS_URL + e.page.removesuffix(".md") + "/"}
    if e.open_items:
        out["open_items"] = e.open_items
    return out


F = TypeVar("F", bound=Callable[..., Any])


def with_validation_status(fn: F) -> F:
    """Add the engine's ``validation`` block to a tool's dict result (place under ``@mcp.tool``).

    Raises ``KeyError`` at import time if the tool has no entry in ``ENGINES``, so a new tool cannot
    ship without a status.
    """
    block = status_for_tool(fn.__name__)

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = fn(*args, **kwargs)
        return {**result, "validation": block} if isinstance(result, dict) else result

    return wrapper  # type: ignore[return-value]


def render_status_page() -> str:
    """Markdown for ``docs/validation/status.md``."""
    lines = [
        "# Validation status",
        "",
        "<!-- Generated by scripts/render_validation_status.py from src/lilavati/validation_status.py; "
        "do not edit by hand. -->",
        "",
        "Every engine has one status, and every MCP tool returns its engine's status in a `validation` field, "
        "so an agent can tell a checked engine from an unchecked one.",
        "",
        "| Status | Meaning |",
        "| :--- | :--- |",
        *[f"| {ICON[s]} {s} | {m} |" for s, m in MEANING.items()],
        "",
        "| Engine | Pillar | Status | MCP tools | Open items | Page |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for e in ENGINES:
        tools = ", ".join(f"`{t}`" for t in e.tools) or "none"
        page = e.page.removeprefix("validation/")
        lines.append(f"| {e.name} (`{e.module}`) | {e.pillar} | {ICON[e.status]} {e.status} | {tools} | "
                     f"{e.open_items or 'none'} | [{page.removesuffix('.md')}]({page}) |")
    return "\n".join(lines) + "\n"


def render_pillar_table() -> str:
    """Markdown for the pillar table on the docs home page (between the generated-block markers)."""
    lines = ["| Pillar | Capability | Engines and validation status |", "| :--- | :--- | :--- |"]
    for pillar, title in PILLARS.items():
        engines = [e for e in ENGINES if e.pillar == pillar]
        cell = "; ".join(f"{e.name} {ICON[e.status]} [{e.status}]({e.page})" for e in engines)
        label = f"**Pillar {pillar}**" if pillar in ("I", "II", "III", "IV", "V", "VI", "VII") else f"**{pillar}**"
        lines.append(f"| {label} | {title} | {cell} |")
    lines.append("")
    lines.append("Status meanings and every MCP tool: [validation status](validation/status.md).")
    return "\n".join(lines) + "\n"
