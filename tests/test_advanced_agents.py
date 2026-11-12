"""
Unit and Integration Tests for Search Agent, Deep Agent, and Research Agent.
"""

from __future__ import annotations

from datetime import date

from lilavati.agents.deep import DeepFinancialAgent
from lilavati.agents.research import FinancialResearchAgent
from lilavati.agents.search import FinancialSearchAgent
from lilavati.core.graph import StatementGraph


def test_financial_search_agent() -> None:
    search_agent = FinancialSearchAgent()
    rep = search_agent.search_entity(
        symbol="AAPL",
        topics=["revenue", "assets"],
        as_of_date=date(2024, 11, 1),
        jurisdiction="US",
    )

    assert rep.entity_symbol == "AAPL"
    assert len(rep.discovered_facts) >= 2
    assert len(rep.verified_citations) >= 2
    assert rep.as_of_date == date(2024, 11, 1)

    # Test India jurisdiction
    rep_in = search_agent.search_entity(
        symbol="RELIANCE",
        topics=["revenue"],
        as_of_date=date(2024, 3, 31),
        jurisdiction="IN",
    )
    assert rep_in.entity_symbol == "RELIANCE"
    assert len(rep_in.discovered_facts) >= 1


def test_deep_financial_agent_scenarios() -> None:
    deep_agent = DeepFinancialAgent()

    graph = StatementGraph(
        revenue=1000.0,
        gross_margin=0.40,
        sga_ratio=0.15,
        tax_rate=0.20,
        interest_rate=0.05,
        capex=50.0,
        depreciation=40.0,
        cash_start=100.0,
        initial_debt=200.0,
        initial_common_equity=300.0,
        initial_net_ppe=500.0,
    )

    tree = deep_agent.analyze_deep_scenarios(
        query="Evaluate 3-year cash generation trajectory",
        baseline_graph=graph,
    )

    assert tree.target_query == "Evaluate 3-year cash generation trajectory"
    assert len(tree.scenario_branches) == 3
    assert tree.probability_weighted_net_income > 0.0
    assert len(tree.deep_reasoning_steps) >= 3


def test_financial_research_agent_dossier() -> None:
    research_agent = FinancialResearchAgent()
    dossier = research_agent.conduct_deep_research(
        symbol="AAPL",
        as_of_date=date(2024, 11, 1),
    )

    assert dossier.symbol == "AAPL"
    assert dossier.recommendation in ("OVERWEIGHT", "NEUTRAL", "UNDERWEIGHT")
    assert dossier.citations_count >= 2
    assert len(dossier.proof_of_citation_hashes) >= 2
    assert dossier.scenario_analysis.probability_weighted_net_income > 0.0
    assert "beneish_m_score" in dossier.forensic_accounting_summary
