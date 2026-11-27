"""
Unit and Integration Tests for Search Agent, Deep Agent, and Research Agent.
"""

from __future__ import annotations

from datetime import date

import pytest

from lilavati.agents.deep import DeepFinancialAgent
from lilavati.agents.research import FinancialResearchAgent
from lilavati.agents.search import FinancialSearchAgent
from lilavati.core.graph import StatementGraph


def _sec_client():
    import json
    from pathlib import Path

    import httpx

    from lilavati.connectors.edgar import EdgarClient

    fix = Path(__file__).parent / "fixtures"
    subs = json.loads((fix / "aapl_submissions_subset.json").read_text())
    facts = json.loads((fix / "aapl_companyfacts_10k_fy2025_2026.json").read_text())

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/submissions/CIK0000320193.json"):
            return httpx.Response(200, json=subs)
        if request.url.path.endswith("/companyfacts/CIK0000320193.json"):
            return httpx.Response(200, json=facts)
        return httpx.Response(404)

    return EdgarClient(user_agent="Example Org contact@example.org", transport=httpx.MockTransport(handler))


def test_financial_search_agent_is_point_in_time_and_cited() -> None:
    # Apple's FY2026 10-K was filed 2026-11-03 (fixtures: verbatim SEC subsets). As of 2026-11-02 the
    # latest known 10-K is FY2025's; from 2026-11-03 it is FY2026's. Values: the 10-Ks, USD millions.
    agent = FinancialSearchAgent(edgar_client=_sec_client())
    before = agent.search_entity("AAPL", [], as_of_date=date(2026, 11, 2))
    after = agent.search_entity("AAPL", [], as_of_date=date(2026, 11, 3))
    rev_before = {f.metric_name: f.value for f in before.discovered_facts}["revenue"]
    rev_after = {f.metric_name: f.value for f in after.discovered_facts}["revenue"]
    assert rev_before == 416_161 and rev_after == 478_834
    assert {c.filing_date for c in after.verified_citations} == {date(2026, 11, 3)}
    assert all(c.page is None and len(c.doc_hash) == 64 for c in after.verified_citations)

    only_bs = agent.search_entity("AAPL", ["balance_sheet"], as_of_date=date(2026, 11, 3))
    assert {f.topic for f in only_bs.discovered_facts} == {"balance_sheet"}


def test_financial_search_agent_never_invents_figures(monkeypatch) -> None:
    # It used to return Apple's FY2024 figures, with made-up page numbers, for any symbol when SEC
    # could not be reached, and a fixed Indian revenue of 890,000 for any company.
    monkeypatch.delenv("LILAVATI_SEC_USER_AGENT", raising=False)
    agent = FinancialSearchAgent()
    rep = agent.search_entity("MSFT", ["revenue"], as_of_date=date(2024, 11, 1))
    assert rep.discovered_facts == [] and rep.verified_citations == []
    assert "LILAVATI_SEC_USER_AGENT" in rep.notes[0]

    rep_in = agent.search_entity("RELIANCE", ["revenue"], as_of_date=date(2024, 3, 31), jurisdiction="IN")
    assert rep_in.discovered_facts == [] and "not implemented" in rep_in.notes[0]

    early = FinancialSearchAgent(edgar_client=_sec_client()).search_entity("AAPL", [], date(2020, 1, 1))
    assert early.discovered_facts == [] and "No 10-K" in early.notes[0]


def test_deep_financial_agent_scenarios() -> None:
    deep_agent = DeepFinancialAgent()

    tree = deep_agent.analyze_deep_scenarios(
        query="Evaluate 3-year cash generation trajectory",
        baseline_graph=_scenario_baseline(),
    )

    assert tree.target_query == "Evaluate 3-year cash generation trajectory"
    assert len(tree.scenario_branches) == 3
    assert all(b.smt_invariant_verified and not b.is_pruned for b in tree.scenario_branches)
    assert tree.probability_weighted_net_income > 0.0
    assert len(tree.deep_reasoning_steps) >= 3


def _scenario_baseline(graph_type: type[StatementGraph] = StatementGraph) -> StatementGraph:
    # Opening balance sheet: 100 + 120 + 500 + 30 = 750 = (60 + 200 + 40) + (300 + 150).
    return graph_type(
        revenue=1000.0, gross_margin=0.40, sga_ratio=0.15, tax_rate=0.25, interest_rate=0.05, capex=50.0,
        depreciation=40.0, cash_start=100.0, initial_debt=200.0, initial_common_equity=300.0,
        initial_net_ppe=500.0, opening_receivables=120.0, opening_payables=60.0, opening_retained_earnings=150.0,
        dso_days=36.5, dpo_days=73.0, other_assets=30.0, other_liabilities=40.0)


def test_scenarios_keep_every_baseline_driver() -> None:
    # Each branch used to be rebuilt without receivable and payable days (always 45 and 30).
    # Base branch, revenue 1050: COGS 630, EBIT 420 - 157.5 = 262.5, pre-tax 252.5, NI 189.375;
    # receivables 1050 / 365 x 36.5 = 105 (down 15), payables 630 / 365 x 73 = 126 (up 66);
    # CFO 189.375 + 40 + 15 + 66 = 310.375; cash 100 + 310.375 - 50 = 360.375.
    tree = DeepFinancialAgent().analyze_deep_scenarios("q", _scenario_baseline())
    base = next(b for b in tree.scenario_branches if b.branch_name.startswith("Base"))
    assert base.projected_net_income == pytest.approx(189.375)
    assert base.projected_ending_cash == pytest.approx(360.375)


def test_a_branch_whose_balance_sheet_does_not_balance_is_pruned() -> None:
    # The pruning rule could never fire while the graph plugged equity.
    class ForgetsPayables(StatementGraph):
        def _operating_cash_flow(self, net_income: float, depreciation: float, change_receivables: float,
                                 change_payables: float) -> float:
            return net_income + depreciation - change_receivables

    tree = DeepFinancialAgent().analyze_deep_scenarios("q", _scenario_baseline(ForgetsPayables))
    assert all(b.is_pruned and not b.smt_invariant_verified for b in tree.scenario_branches)
    assert all("does not balance" in (b.prune_reason or "") for b in tree.scenario_branches)
    assert tree.pruned_branches_count == 3


def _research_agent(drop: tuple[str, ...] = (), company: tuple[str, str] = ("aapl", "0000320193")):
    import json
    from pathlib import Path

    import httpx

    from lilavati.connectors.edgar import EdgarClient

    fix = Path(__file__).parent / "fixtures"
    name, cik = company
    subs = json.loads((fix / f"{name}_submissions_subset.json").read_text())
    facts = json.loads((fix / f"{name}_companyfacts_research_fy2026.json").read_text())
    for tag in drop:
        facts["facts"]["us-gaap"].pop(tag)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith(f"/submissions/CIK{cik}.json"):
            return httpx.Response(200, json=subs)
        if request.url.path.endswith(f"/companyfacts/CIK{cik}.json"):
            return httpx.Response(200, json=facts)
        return httpx.Response(404)

    client = EdgarClient(user_agent="Example Org contact@example.org", transport=httpx.MockTransport(handler))
    return FinancialResearchAgent(search_agent=FinancialSearchAgent(edgar_client=client))


def test_financial_research_agent_uses_the_filing_not_assumptions() -> None:
    # Apple's FY2026 10-K (verbatim SEC subset). Figures below are from the filing's statements and
    # cover page, USD millions. The agent used to take only revenue and assets from a filing and
    # assume everything else (receivables, debt, prior year, emissions).
    d = _research_agent().conduct_deep_research(symbol="AAPL", as_of_date=date(2026, 11, 3))
    assert d.filing.accession == "0000320193-26-000026" and d.company_name == "Apple Inc."
    i = d.inputs_usd_millions
    assert (i["revenue"], i["revenue_prior"]) == (478_834, 416_161)
    assert (i["accounts_receivable"], i["accounts_receivable_prior"]) == (43_817, 39_777)
    assert (i["current_assets"], i["current_liabilities"]) == (173_857, 169_915)
    assert (i["sga"], i["sga_prior"], i["depreciation"]) == (29_774, 27_601, 13_423)
    # Altman (1968) from the printed figures; market value = cover-page public float 3,647,099.
    z = (1.2 * (173_857 - 169_915) / 404_548 + 1.4 * 13_700 / 404_548 + 3.3 * 158_063 / 404_548
         + 0.6 * 3_647_099 / 292_455 + 0.999 * 478_834 / 404_548)
    assert abs(d.committee_memo.altman_z_score.z_score - z) < 1e-9
    assert d.committee_memo.beneish_m_score.m_score < -1.78
    assert d.recommendation == "APPROVED_BUY" and d.target_price is None
    assert all(c.holds for c in d.statement_checks + d.committee_memo.checks)
    # Every cited value resolves against the SEC data read.
    assert d.citations_verified and d.provenance_violations == [] and d.citations_count == 91
    assert d.climate_risk_summary is None  # no emissions supplied: nothing invented
    assert any("public float" in a for a in d.assumed_inputs) and any("scenario" in a for a in d.assumed_inputs)
    assert d.scenario_analysis.probability_weighted_net_income > 0.0


@pytest.mark.parametrize(("company", "symbol", "as_of"), [
    (("aapl", "0000320193"), "AAPL", date(2026, 11, 3)),
    (("msft", "0000789019"), "MSFT", date(2026, 11, 24)),
    (("nvda", "0001045810"), "NVDA", date(2026, 11, 24)),
])
def test_research_scenarios_open_at_the_filing_balance_sheet(
        company: tuple[str, str], symbol: str, as_of: date) -> None:
    # FY2026 10-Ks (fixtures, USD millions). Receivable and payable days are the filing year's, so the
    # Base branch (revenue and COGS x 1.05) grows receivables and payables by 5%: ending cash = cash + NI
    # + depreciation - capex + 0.05 x (payables - receivables). Apple: 36,305 + 137,760.54 + 13,423
    # - 9,041 + 0.05 x (82,252 - 43,817) = 180,369.29.
    d = _research_agent(company=company).conduct_deep_research(symbol=symbol, as_of_date=as_of)
    i = d.inputs_usd_millions
    base = next(b for b in d.scenario_analysis.scenario_branches if b.branch_name.startswith("Base"))
    expected = (i["cash"] + base.projected_net_income + i["depreciation"] - i["capital_expenditure"]
                + 0.05 * (i["accounts_payable"] - i["accounts_receivable"]))
    assert base.projected_ending_cash == pytest.approx(expected, rel=1e-12)
    if symbol == "AAPL":
        assert base.projected_ending_cash == pytest.approx(180_369.29, abs=0.01)
    assert all(b.smt_invariant_verified and not b.is_pruned for b in d.scenario_analysis.scenario_branches)
    assert d.derived_inputs["scenario_dso_days"].startswith("accounts_receivable / revenue")
    assert not any("exceed liabilities plus equity" in a for a in d.assumed_inputs)  # all three balance


def test_financial_research_agent_refuses_instead_of_filling(monkeypatch) -> None:
    import pytest

    with pytest.raises(ValueError, match="sga"):
        _research_agent(drop=("SellingGeneralAndAdministrativeExpense",)).conduct_deep_research("AAPL", date(2026, 11, 3))
    with pytest.raises(ValueError, match="emissions_source"):
        _research_agent().conduct_deep_research("AAPL", date(2026, 11, 3), scope12_emissions_tco2e=50_000.0)
    d = _research_agent().conduct_deep_research("AAPL", date(2026, 11, 3), scope12_emissions_tco2e=50_000.0,
                                                emissions_source="test value")
    assert d.climate_risk_summary is not None and d.climate_risk_summary["emissions_source"] == "test value"

    # Without SEC access there is no dossier (it used to fall back to an illustrative baseline).
    monkeypatch.delenv("LILAVATI_SEC_USER_AGENT", raising=False)
    with pytest.raises(ValueError, match="LILAVATI_SEC_USER_AGENT"):
        FinancialResearchAgent().conduct_deep_research(symbol="MSFT", as_of_date=date(2024, 11, 1))
    with pytest.raises(ValueError, match="Ind AS"):
        FinancialResearchAgent().conduct_deep_research("RELIANCE", date(2024, 3, 31), jurisdiction="IN")


def test_research_sga_is_the_sum_of_its_lines_when_no_total_is_tagged() -> None:
    # Microsoft's FY2026 10-K reports sales and marketing and general and administrative, no SG&A
    # total (verbatim SEC subset, USD millions).
    d = _research_agent(company=("msft", "0000789019")).conduct_deep_research("MSFT", date(2026, 11, 24))
    assert d.inputs_usd_millions["sga"] == 26_710 + 7_956
    assert d.inputs_usd_millions["sga_prior"] == 25_654 + 7_223
    assert "SellingAndMarketingExpense + GeneralAndAdministrativeExpense" in d.derived_inputs["sga"]
    assert d.citations_verified and all(c.holds for c in d.statement_checks + d.committee_memo.checks)


def test_research_flags_high_growth_through_beneish() -> None:
    # Nvidia FY2026 (verbatim SEC subset): revenue 215,938 vs 130,497. The sales growth index alone
    # (SGI = 215,938 / 130,497 = 1.6547, weight 0.892; Beneish 1999) lifts M above -1.78, so the
    # rule-based committee rejects it. A known false-positive pattern of the screen for fast growers,
    # not evidence of manipulation. Capex is tagged PaymentsToAcquireProductiveAssets (6,042), which
    # also includes intangible assets; the dossier says so.
    d = _research_agent(company=("nvda", "0001045810")).conduct_deep_research("NVDA", date(2026, 11, 24))
    b = d.committee_memo.beneish_m_score
    assert abs(b.sgi - 215_938 / 130_497) < 1e-12 and b.m_score > -1.78
    assert d.recommendation == "REJECTED_ACCOUNTING_ANOMALY"
    assert all(c.holds for c in d.statement_checks + d.committee_memo.checks)  # identities are fine
    assert d.inputs_usd_millions["capital_expenditure"] == 6_042
    assert "intangible" in d.derived_inputs["capital_expenditure"]
