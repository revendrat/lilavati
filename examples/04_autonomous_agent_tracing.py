"""
Example 04: Autonomous Financial Agent with OpenTelemetry Tracing & Audit Trails.

Demonstrates:
1. Setting up an institutional agent with system prompts from `src/lilavati/prompts/`.
2. Registering deterministic FastMCP calculation tools.
3. Executing an agent run with SMT invariant validation.
4. Exporting an immutable JSONL audit trace for regulatory compliance.
"""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lilavati.llm.providers import INSTITUTIONAL_MODEL_PRESETS
from lilavati.prompts import FORENSIC_BEAR_PROMPT
from lilavati.runtime.agent import AgentConfig, NeuroSymbolicAgent
from lilavati.tracing.tracer import Tracer

console = Console()


def main() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Project Līlāvatī: Autonomous Agent Execution & Tracing[/bold cyan]\n"
            "Tracing agent reasoning, tool invocations, SMT verification, and audit logs.",
            title="Institutional Agent Runtime",
        )
    )

    # 1. Initialize Tracer
    tracer = Tracer()

    # 2. Configure Agent
    config = AgentConfig(
        agent_id="forensic-auditor-agent",
        role_name="Forensic Credit & Accounting Auditor",
        system_prompt=FORENSIC_BEAR_PROMPT,
        model_spec=INSTITUTIONAL_MODEL_PRESETS["mock-evaluator"],
        max_reflection_iterations=3,
    )
    agent = NeuroSymbolicAgent(config=config, tracer=tracer)

    # 3. Register Deterministic Sandbox Tools
    def compute_working_capital_gap(
        receivables: float, inventory: float, payables: float
    ) -> dict[str, float]:
        nwc = receivables + inventory - payables
        return {"net_working_capital": nwc, "cash_conversion_headwind": max(0.0, nwc)}

    agent.register_tool(
        name="compute_working_capital_gap",
        description="Calculates net working capital balance and working capital cash drag.",
        parameters_schema={
            "type": "object",
            "properties": {
                "receivables": {"type": "number"},
                "inventory": {"type": "number"},
                "payables": {"type": "number"},
            },
            "required": ["receivables", "inventory", "payables"],
        },
        fn=compute_working_capital_gap,
    )

    # 4. Execute Autonomous Agent Run
    query = (
        "Audit Company XYZ for earnings quality. Historicals: Receivables=$150M, "
        "Inventory=$80M, Payables=$60M. Check if working capital expansion creates cash flow strain."
    )
    console.print(f"\n[bold yellow]User Query:[/bold yellow] {query}\n")

    output = agent.run(query)

    # 5. Export JSONL Audit Trace
    trace_path = Path("examples/output_audit_trace.jsonl")
    tracer.export_jsonl(trace_path)

    # 6. Display Execution Summary
    table = Table(title="Agent Execution & Compliance Audit Summary", show_header=True)
    table.add_column("Audit Metric", style="cyan")
    table.add_column("Value", style="bold green", justify="right")

    summary = output.audit_summary
    table.add_row("Trace ID", summary["trace_id"])
    table.add_row("Total Captured Spans", str(summary["total_spans"]))
    table.add_row("Tool Calls Executed", str(summary["tool_calls_count"]))
    table.add_row("LLM Turns Completed", str(summary["llm_calls_count"]))
    table.add_row("SMT Formal Checks", str(summary["smt_checks_count"]))
    table.add_row(
        "Formal Compliance Status",
        "100% COMPLIANT" if summary["is_fully_compliant"] else "VIOLATIONS DETECTED",
    )
    table.add_row("Audit Trace Exported", str(trace_path))

    console.print(table)
    console.print(f"\n[bold]Final Agent Output:[/bold]\n{output.response_text}")


if __name__ == "__main__":
    main()
