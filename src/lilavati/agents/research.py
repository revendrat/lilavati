"""
Research workflow on one company's latest 10-K, with every input reported, cited and checked.

For a US company and an as-of date:

1. The latest 10-K filed on or before the as-of date (point in time), and only that filing's own XBRL
   facts: this year's figures and the prior-year comparatives it reports (``sec_filing``).
2. The three-statement model from that filing (``edgar.statement_model_from_filing``: reported or
   derived by a recorded formula, with balance sheet and cash checks).
3. The rule-based committee (``AdversarialCommittee``): Beneish M-score, Altman Z-score and identity
   checks on the reported inputs. Market value of equity is the caller's figure, else the public
   float on the 10-K cover page (``dei:EntityPublicFloat``, non-affiliate equity at the end of the
   second quarter), labelled as such.
4. A scenario tree (``DeepFinancialAgent``) on a statement graph calibrated from the filing. The
   scenario multipliers are assumptions and are listed.
5. Carbon intensity only when the caller supplies emissions (a 10-K does not report them).
6. Every cited value resolved against the SEC data actually read (``SourceStore`` and
   ``ProvenanceGate``).

Nothing is filled in: if the filing lacks an input, ``ValueError`` names it. Amounts are US dollars as
reported; the thesis quotes USD millions. A rule-based screen, not investment advice.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

from lilavati.agents.committee import AdversarialCommittee, InvestmentCommitteeMemo
from lilavati.agents.deep import DeepFinancialAgent, DeepReasoningTree
from lilavati.agents.search import FinancialSearchAgent
from lilavati.connectors.edgar import (
    STATEMENT_ITEMS,
    SourcedThreeStatementModel,
    statement_model_from_filing,
)
from lilavati.connectors.sec_filing import (
    FilingRef,
    IdentityCheck,
    Kind,
    extract_filing,
    fact_hash,
    filings_from_submissions,
    fiscal_year_of,
    prior_period_view,
)
from lilavati.core.graph import StatementGraph
from lilavati.core.provenance import CitationRef, SourcedValue, SourceStore
from lilavati.core.sustainability import SustainabilityEngine
from lilavati.framework import FinancialState, ProvenanceGate
from lilavati.llm.client import BaseLLMClient, UniversalLLMClient
from lilavati.llm.providers import INSTITUTIONAL_MODEL_PRESETS, ModelSpec

# Beneish and committee inputs beyond the statement model (kind, US-GAAP tags in priority order).
RESEARCH_ITEMS: dict[str, tuple[Kind, list[str]]] = {
    **STATEMENT_ITEMS,
    "current_assets": ("instant", ["AssetsCurrent"]),
    "current_liabilities": ("instant", ["LiabilitiesCurrent"]),
    "sga": ("duration", ["SellingGeneralAndAdministrativeExpense"]),
    # Microsoft reports these two lines and no SG&A total; their sum is SG&A.
    "selling_and_marketing": ("duration", ["SellingAndMarketingExpense"]),
    "general_and_administrative": ("duration", ["GeneralAndAdministrativeExpense"]),
    # Nvidia tags capex as PaymentsToAcquireProductiveAssets, which also includes intangible assets.
    "capital_expenditure": ("duration", ["PaymentsToAcquirePropertyPlantAndEquipment",
                                         "PaymentsToAcquireProductiveAssets"]),
    "depreciation": ("duration", ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization",
                                  "DepreciationAmortizationAndAccretionNet", "Depreciation"]),
}
# Beneish (1999) needs these for both years; net income and CFO for the current year only.
BENEISH_BOTH_YEARS = ("revenue", "cost_of_revenue", "accounts_receivable", "current_assets", "net_ppe",
                      "total_assets", "depreciation", "sga", "long_term_debt_noncurrent", "current_liabilities")

# The scenario multipliers of DeepFinancialAgent (assumptions, listed in the dossier).
SCENARIO_NOTE = ("scenario tree: Bull revenue x1.15 and margin +2 pts (p 0.25), Base x1.05 (p 0.50), "
                 "Bear x0.85 and margin -5 pts (p 0.25), on a one-year statement graph")


class ResearchDossier(BaseModel):
    """Research memo for one company and as-of date, built from one 10-K."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    company_name: str
    as_of_date: date
    filing: FilingRef
    recommendation: str = Field(..., description="the committee's rule-based recommendation")
    target_price: float | None = None  # no valuation model is run
    executive_thesis: str
    committee_memo: InvestmentCommitteeMemo
    statement_checks: list[IdentityCheck]
    forensic_accounting_summary: dict[str, Any]
    scenario_analysis: DeepReasoningTree
    climate_risk_summary: dict[str, Any] | None = Field(
        None, description="WACI when the caller supplied emissions; None otherwise")
    inputs_usd_millions: dict[str, float] = Field(
        default_factory=dict, description="every reported input used, '_prior' suffix for last year")
    citations_count: int
    proof_of_citation_hashes: list[str]
    citations_verified: bool = Field(..., description="every citation resolves against the SEC data read")
    provenance_violations: list[str] = Field(default_factory=list)
    data_source: str
    derived_inputs: dict[str, str] = Field(default_factory=dict, description="inputs computed from reported lines")
    assumed_inputs: list[str] = Field(default_factory=list, description="every input not taken from the filing")


def _public_float(facts: dict[str, Any], filing: FilingRef) -> SourcedValue | None:
    """``dei:EntityPublicFloat`` from the filing's cover page, cited."""
    for e in facts.get("facts", {}).get("dei", {}).get("EntityPublicFloat", {}).get("units", {}).get("USD", []):
        if e.get("accn") == filing.accession:
            return SourcedValue(value=float(e["val"]), unit="USD", scale=1, citation=CitationRef(
                doc_hash=fact_hash(e), filing_type=filing.form, filing_date=date.fromisoformat(e["filed"]),
                period_end=date.fromisoformat(e["end"]), page=None, table_id="xbrl",
                xbrl_tag="dei:EntityPublicFloat", raw_snippet=f"{float(e['val']):,.0f} USD ({filing.accession})"))
    return None


def scenario_graph_from_filing(model: SourcedThreeStatementModel, v: dict[str, float], assumed: list[str],
                               derived: dict[str, str]) -> StatementGraph:
    """
    The one-year scenario graph (USD millions), opening at the filing's closing balance sheet.

    Drivers from the filing year: gross margin, operating-expense ratio, effective tax rate (income tax /
    pre-tax income), interest rate (interest expense / total debt; 0 and listed in ``assumed`` when no
    interest line is reported), capex and depreciation, receivable days (receivables / revenue × 365) and
    payable days (payables / cost of revenue × 365), so revenue held flat leaves working capital flat.
    Opening lines the graph does not model are held constant: other assets (total assets − cash −
    receivables − net PP&E), other liabilities (total liabilities − payables − debt) and equity other than
    retained earnings (total equity − retained earnings). Each derivation is recorded in ``derived``. If
    the filing's assets differ from its liabilities plus equity (temporary equity, for example), the
    difference is held as an other liability and listed in ``assumed``.
    """
    m = 1e6
    inc, bs = model.statement_model.income_statement, model.statement_model.balance_sheet
    interest_rate = 0.0
    if "interest_expense" in v and bs.total_debt:
        interest_rate = v["interest_expense"] / bs.total_debt
    else:
        assumed.append("interest rate 0 in the scenario graph: the filing reports no interest expense line")
    if "accounts_payable" in model.not_reported:
        assumed.append("payable days 0 in the scenario graph: the filing reports no payables line "
                       "(payables are in other liabilities, held constant)")
    gap = bs.total_assets - bs.total_liabilities - bs.total_equity
    if abs(gap) > 0.5:
        assumed.append(f"scenario graph: the filing's total assets exceed liabilities plus equity by "
                       f"{gap / m:,.0f} (USD millions; temporary equity, for example), held as an other liability")
    derived.update({
        "scenario_dso_days": "accounts_receivable / revenue x 365 (filing year)",
        "scenario_dpo_days": "accounts_payable / cost_of_revenue x 365 (filing year)",
        "scenario_other_assets": "total_assets - cash - accounts_receivable - net_ppe (held constant)",
        "scenario_other_liabilities": "total_liabilities - accounts_payable - total_debt "
                                      "(+ total_assets - total_liabilities - total_equity if not zero; held constant)",
        "scenario_equity_other_than_retained_earnings": "total_equity - retained_earnings (held constant)",
    })
    return StatementGraph(
        revenue=inc.revenue / m, gross_margin=inc.gross_profit / inc.revenue,
        sga_ratio=(inc.gross_profit - inc.operating_income) / inc.revenue,
        tax_rate=v["income_tax"] / v["pretax_income"], interest_rate=interest_rate,
        capex=v["capital_expenditure"] / m, depreciation=v["depreciation"] / m,
        cash_start=bs.cash_and_equivalents / m, initial_debt=bs.total_debt / m,
        initial_common_equity=(bs.total_equity - bs.retained_earnings) / m, initial_net_ppe=bs.net_ppe / m,
        opening_receivables=bs.accounts_receivable / m, opening_payables=bs.accounts_payable / m,
        opening_retained_earnings=bs.retained_earnings / m,
        dso_days=bs.accounts_receivable / inc.revenue * 365.0, dpo_days=bs.accounts_payable / inc.cogs * 365.0,
        other_assets=(bs.total_assets - bs.cash_and_equivalents - bs.accounts_receivable - bs.net_ppe) / m,
        other_liabilities=(bs.total_liabilities - bs.accounts_payable - bs.total_debt + gap) / m,
    )


class FinancialResearchAgent:
    """Filing → statement model → committee → scenarios → citation check, for one company and date."""

    def __init__(
        self,
        model_spec: ModelSpec | None = None,
        llm_client: BaseLLMClient | None = None,
        search_agent: FinancialSearchAgent | None = None,
    ) -> None:
        self.spec = model_spec or INSTITUTIONAL_MODEL_PRESETS["mock-evaluator"]
        self.llm = llm_client or UniversalLLMClient(spec=self.spec)
        self.search_agent = search_agent or FinancialSearchAgent(model_spec=self.spec, llm_client=self.llm)
        self.deep_agent = DeepFinancialAgent(model_spec=self.spec, llm_client=self.llm)

    def conduct_deep_research(
        self,
        symbol: str,
        as_of_date: date,
        jurisdiction: str = "US",
        growth_target: float = 0.05,
        market_value_equity: float | None = None,
        scope12_emissions_tco2e: float | None = None,
        emissions_source: str = "",
    ) -> ResearchDossier:
        """Build the dossier from the latest 10-K filed on or before ``as_of_date``.

        ``growth_target``: the committee's revenue-growth hurdle (a decimal), the caller's choice.
        ``market_value_equity`` (US dollars): defaults to the 10-K cover page's public float.
        ``scope12_emissions_tco2e`` with ``emissions_source``: enables the carbon-intensity line.
        Raises ``ValueError`` when SEC cannot be reached, no 10-K was filed by the date, or the
        filing lacks an input (named in the message).
        """
        if jurisdiction.upper() != "US":
            raise ValueError("Only US (SEC) filings are retrieved; for Ind AS, parse a disclosure you hold with "
                             "IndiaFilingsClient.parse_ind_as_disclosure.")
        edgar = self.search_agent.edgar
        try:
            filings = [f for f in filings_from_submissions(edgar.fetch_submissions(symbol))
                       if f.filing_date <= as_of_date]
            if not filings:
                raise ValueError(f"No 10-K for {symbol} filed on or before {as_of_date} in SEC's recent index.")
            filing = filings[0]
            facts = edgar.fetch_company_facts(filing.cik)
        except (FileNotFoundError, RuntimeError, httpx.HTTPError) as e:
            raise ValueError(f"SEC EDGAR unavailable for {symbol}: {e}") from e

        fy = fiscal_year_of(facts, filing)
        model: SourcedThreeStatementModel = statement_model_from_filing(facts, filing, ticker=symbol.upper(),
                                                                        fiscal_year=fy)
        cur = extract_filing(facts, filing, RESEARCH_ITEMS)
        prior = extract_filing(facts, prior_period_view(facts, filing), RESEARCH_ITEMS)
        v = {k: sv.value for k, sv in cur.values.items()}
        p = {k: sv.value for k, sv in prior.values.items()}
        derived: dict[str, str] = {}
        for year in (v, p):
            if "sga" not in year and "selling_and_marketing" in year and "general_and_administrative" in year:
                year["sga"] = year["selling_and_marketing"] + year["general_and_administrative"]
                derived["sga"] = "SellingAndMarketingExpense + GeneralAndAdministrativeExpense (no SG&A total tagged)"
        if cur.tags_used.get("capital_expenditure") == "PaymentsToAcquireProductiveAssets":
            derived["capital_expenditure"] = "PaymentsToAcquireProductiveAssets (includes intangible assets)"
        lacking = [k for k in BENEISH_BOTH_YEARS if k not in v] + \
                  [f"{k} (prior year)" for k in BENEISH_BOTH_YEARS if k not in p] + \
                  [k for k in ("net_income", "operating_cash_flow", "capital_expenditure", "income_tax",
                               "pretax_income") if k not in v]
        float_sv = _public_float(facts, filing)
        if market_value_equity is None and float_sv is None:
            lacking.append("public float (dei:EntityPublicFloat); pass market_value_equity")
        if lacking:
            raise ValueError(f"{symbol} {filing.form} {filing.accession} does not report {', '.join(lacking)}, "
                             "needed for the research workflow.")

        sm = model.statement_model
        assumed = [f"revenue growth target {growth_target:.0%} (caller's choice)", SCENARIO_NOTE]
        if market_value_equity is None:
            assert float_sv is not None
            mve = float_sv.value
            assumed.append(f"market value of equity: public float {mve / 1e6:,.0f} (USD millions) as of "
                           f"{float_sv.citation.period_end}, a proxy (non-affiliate equity only)")
        else:
            mve = market_value_equity
            assumed.append(f"market value of equity {mve / 1e6:,.0f} (USD millions), supplied by the caller")

        memo = AdversarialCommittee.evaluate_company(
            symbol=symbol, fiscal_year=fy, bull_revenue_growth_target=growth_target,
            revenue_t=v["revenue"], revenue_t_minus_1=p["revenue"],
            cogs_t=v["cost_of_revenue"], cogs_t_minus_1=p["cost_of_revenue"],
            receivables_t=v["accounts_receivable"], receivables_t_minus_1=p["accounts_receivable"],
            current_assets_t=v["current_assets"], current_assets_t_minus_1=p["current_assets"],
            ppe_t=v["net_ppe"], ppe_t_minus_1=p["net_ppe"],
            total_assets_t=v["total_assets"], total_assets_t_minus_1=p["total_assets"],
            depreciation_t=v["depreciation"], depreciation_t_minus_1=p["depreciation"],
            sga_t=v["sga"], sga_t_minus_1=p["sga"],
            long_term_debt_t=v["long_term_debt_noncurrent"], long_term_debt_t_minus_1=p["long_term_debt_noncurrent"],
            current_liabilities_t=v["current_liabilities"], current_liabilities_t_minus_1=p["current_liabilities"],
            net_income_t=v["net_income"], cfo_t=v["operating_cash_flow"],
            cfi_t=v["investing_cash_flow"], cff_t=v["financing_cash_flow"], market_value_equity=mve,
            total_liabilities_t=sm.balance_sheet.total_liabilities, shareholders_equity_t=sm.balance_sheet.total_equity,
            retained_earnings_t=v["retained_earnings"], operating_income_t=v["operating_income"],
            cash_start_t=next(sv.value for k, sv in model.sourced_facts.items() if k.endswith("_opening")),
            cash_end_t=v["cash_incl_restricted"] if "cash_incl_restricted" in v else v["cash"],
            fx_effect_on_cash_t=v.get("fx_effect_on_cash", 0.0),
        )

        m = 1e6
        inc = sm.income_statement
        graph = scenario_graph_from_filing(model, v, assumed, derived)
        tree = self.deep_agent.analyze_deep_scenarios(
            query=f"One-year scenarios for {symbol} from its FY{fy} 10-K", baseline_graph=graph)

        climate: dict[str, Any] | None = None
        if scope12_emissions_tco2e is not None:
            if not emissions_source.strip():
                raise ValueError("emissions_source is required with scope12_emissions_tco2e (where the figure is from)")
            waci = SustainabilityEngine.calculate_waci(
                portfolio_weights=[1.0], emissions=[scope12_emissions_tco2e], revenues_millions=[inc.revenue / m])
            climate = {"waci": waci.waci, "carbon_intensity_clean": waci.carbon_intensity_clean,
                       "emissions_source": emissions_source}

        # Every cited value, resolved against the SEC data read.
        cited: list[SourcedValue] = [*model.sourced_facts.values(), *cur.values.values(), *prior.values.values()]
        if market_value_equity is None and float_sv is not None:
            cited.append(float_sv)
        store = SourceStore()
        store.add_xbrl_company_facts(facts)
        state = ProvenanceGate(store)(FinancialState(sourced_values=cited))
        hashes = sorted({sv.citation.doc_hash for sv in cited})

        inputs = {k: x / m for k, x in v.items()} | {f"{k}_prior": x / m for k, x in p.items()}
        data_source = (f"{filing.form} {filing.accession} filed {filing.filing_date}, period ended "
                       f"{filing.report_date} (SEC XBRL); prior year from the same filing's comparatives")
        failed = [c.name for c in [*model.checks, *memo.checks] if not c.holds]
        thesis = (
            f"{cur.company} FY{fy} ({data_source}). Revenue {v['revenue'] / m:,.0f} vs {p['revenue'] / m:,.0f} "
            f"(growth {v['revenue'] / p['revenue'] - 1:.1%}, target {growth_target:.0%}); Beneish M-score "
            f"{memo.beneish_m_score.m_score:.2f} (threshold -1.78); Altman Z-score {memo.altman_z_score.z_score:.2f} "
            f"({memo.altman_z_score.distress_zone}); identity checks "
            + ("hold" if not failed else "fail: " + ", ".join(failed))
            + f"; citations {'resolve' if state.is_valid else 'do not all resolve'} against the SEC data read. "
            f"Committee (rule-based): {memo.recommendation.value}. A screen on reported figures, not investment advice."
        )
        return ResearchDossier(
            symbol=symbol.upper(), company_name=cur.company, as_of_date=as_of_date, filing=filing,
            recommendation=memo.recommendation.value, executive_thesis=thesis, committee_memo=memo,
            statement_checks=model.checks,
            forensic_accounting_summary={
                "beneish_m_score": memo.beneish_m_score.m_score,
                "is_manipulator": memo.beneish_m_score.is_likely_manipulator,
                "dsri": memo.beneish_m_score.dsri, "tata": memo.beneish_m_score.tata,
                "altman_z_score": memo.altman_z_score.z_score, "altman_zone": memo.altman_z_score.distress_zone,
            },
            scenario_analysis=tree, climate_risk_summary=climate, inputs_usd_millions=inputs,
            citations_count=len(cited), proof_of_citation_hashes=hashes,
            citations_verified=state.is_valid, provenance_violations=state.gate_violations,
            data_source=data_source, derived_inputs=derived, assumed_inputs=assumed,
        )
