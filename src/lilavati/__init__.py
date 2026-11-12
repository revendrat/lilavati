"""
Līlāvatī (लीलावती)
==================
An open-source, neuro-symbolic agentic framework and benchmark suite
for quantitative finance, credit, financial econometrics, and algorithmic execution.
"""

from lilavati.core.invariants import SuvarnaEngine
from lilavati.core.provenance import CitationRef, SourcedValue
from lilavati.framework.agent import FinancialAgent
from lilavati.framework.gates import (
    CovenantGate,
    ProvenanceGate,
    SMTBalanceGate,
    TemporalPurityGate,
)
from lilavati.framework.graph import END, CompiledFinancialGraph, FinancialStateGraph
from lilavati.framework.state import FinancialState
from lilavati.tracing.tracer import Tracer

__version__ = "0.1.0"

__all__ = [
    "FinancialAgent",
    "FinancialStateGraph",
    "CompiledFinancialGraph",
    "FinancialState",
    "END",
    "SMTBalanceGate",
    "CovenantGate",
    "ProvenanceGate",
    "TemporalPurityGate",
    "CitationRef",
    "SourcedValue",
    "SuvarnaEngine",
    "Tracer",
    "__version__",
]
