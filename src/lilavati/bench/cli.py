"""
Command-Line Interface for Līlāvatī-Bench.

Provides reproducible evaluation commands to benchmark financial AI models and agents.
Usage:
    lilavati-bench run --model <model-name> [--track <track>] [--format <markdown|rich|json>]
    lilavati-bench list-cases
"""

from __future__ import annotations

import argparse
import json
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lilavati.bench.datasets import get_cases_by_track, load_all_test_cases
from lilavati.bench.runner import BenchmarkRunner, ReferenceAgentSolver

console = Console()


def format_markdown_scorecard(card_dict: dict[str, object]) -> str:
    """Generates an academic Markdown table for pre-prints and GitHub READMEs."""
    md = [
        f"### Līlāvatī-Bench Evaluation Scorecard: `{card_dict['agent_id']}`",
        "",
        "| Metric | Score | Benchmark Target | Status |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Composite Līlāvatī Index** | **{card_dict['composite_lilavati_index']:.1f}/100** | $\\ge 90.0$ | {'✅ PASS' if float(card_dict['composite_lilavati_index']) >= 90.0 else '⚠️ SUBPAR'} |",  # type: ignore[arg-type]
        f"| **Proof-of-Citation Score (PoCS)** | {float(card_dict['proof_of_citation_score']) * 100:.1f}% | 100.0% | {'✅ PASS' if float(card_dict['proof_of_citation_score']) == 1.0 else '⚠️ DEFECT'} |",  # type: ignore[arg-type]
        f"| **Accounting Invariant Compliance (ICR)** | {float(card_dict['invariant_compliance_rate']) * 100:.1f}% | 100.0% (Z3 SMT) | {'✅ PASS' if float(card_dict['invariant_compliance_rate']) == 1.0 else '⚠️ BREACH'} |",  # type: ignore[arg-type]
        f"| **Temporal Purity Index (TPI)** | {float(card_dict['temporal_purity_index']) * 100:.1f}% | 100.0% (Zero Look-Ahead) | {'✅ PASS' if float(card_dict['temporal_purity_index']) == 1.0 else '⚠️ CONTAMINATED'} |",  # type: ignore[arg-type]
        f"| **Tool Math Purity Ratio (TMPR)** | {float(card_dict['tool_math_purity_ratio']) * 100:.1f}% | 100.0% (Zero LLM Math) | {'✅ PASS' if float(card_dict['tool_math_purity_ratio']) == 1.0 else '⚠️ HALLUCINATION'} |",  # type: ignore[arg-type]
        "",
        "#### Track Breakdown",
        "| Track | Name | Score |",
        "| :--- | :--- | :--- |",
    ]
    track_scores = card_dict.get("track_scores", {})
    if isinstance(track_scores, dict):
        for k, v in track_scores.items():
            md.append(
                f"| `{k}` | {k.replace('track', 'Track ').replace('_', ' ').title()} | {float(v) * 100:.1f}% |"
            )

    return "\n".join(md)


def run_benchmark_cli(args: argparse.Namespace) -> int:
    agent_id = args.model
    track_filter = args.track
    fmt = args.format

    if track_filter and track_filter != "all":
        cases = get_cases_by_track(track_filter)
        if not cases:
            console.print(f"[red]Error: No test cases found for track '{track_filter}'[/red]")
            return 1
    else:
        cases = load_all_test_cases()

    if fmt == "rich":
        console.print(
            Panel.fit(
                f"[bold cyan]Līlāvatī-Bench Execution Engine[/bold cyan]\n"
                f"Agent / Model: [yellow]{agent_id}[/yellow]\n"
                f"Test Cases: [green]{len(cases)}[/green] | Track: [magenta]{track_filter or 'all'}[/magenta]",
                title="Institutional Evaluation Suite",
            )
        )

    runner = BenchmarkRunner(cases=cases)
    card = runner.run_suite(agent_id=agent_id, solver_fn=ReferenceAgentSolver.solve)
    card_dict = card.model_dump()

    if fmt == "json":
        print(json.dumps(card_dict, indent=2))
        return 0

    if fmt == "markdown":
        print(format_markdown_scorecard(card_dict))
        return 0

    # Rich table output
    table = Table(
        title=f"Līlāvatī-Bench Results: {agent_id}", show_header=True, header_style="bold magenta"
    )
    table.add_column("Metric", style="cyan", width=36)
    table.add_column("Score", style="bold green", justify="right")
    table.add_column("Benchmark Target", style="dim", justify="right")
    table.add_column("Status", justify="center")

    comp = card.composite_lilavati_index
    table.add_row(
        "Composite Līlāvatī Index",
        f"{comp:.1f}/100",
        "≥ 90.0",
        "[bold green]PASS[/bold green]" if comp >= 90.0 else "[bold red]FAIL[/bold red]",
    )
    table.add_row(
        "Proof-of-Citation Score (PoCS)",
        f"{card.proof_of_citation_score * 100:.1f}%",
        "100.0%",
        "[bold green]PASS[/bold green]"
        if card.proof_of_citation_score == 1.0
        else "[bold red]FAIL[/bold red]",
    )
    table.add_row(
        "Accounting Invariant Compliance (ICR)",
        f"{card.invariant_compliance_rate * 100:.1f}%",
        "100.0%",
        "[bold green]PASS[/bold green]"
        if card.invariant_compliance_rate == 1.0
        else "[bold red]FAIL[/bold red]",
    )
    table.add_row(
        "Temporal Purity Index (TPI)",
        f"{card.temporal_purity_index * 100:.1f}%",
        "100.0%",
        "[bold green]PASS[/bold green]"
        if card.temporal_purity_index == 1.0
        else "[bold red]FAIL[/bold red]",
    )
    table.add_row(
        "Tool Math Purity Ratio (TMPR)",
        f"{card.tool_math_purity_ratio * 100:.1f}%",
        "100.0%",
        "[bold green]PASS[/bold green]"
        if card.tool_math_purity_ratio == 1.0
        else "[bold red]FAIL[/bold red]",
    )

    console.print(table)

    track_table = Table(title="Track Performance Breakdown", show_header=True)
    track_table.add_column("Track Key", style="cyan")
    track_table.add_column("Accuracy", justify="right", style="bold green")
    for tr, sc in card.track_scores.items():
        track_table.add_row(tr, f"{sc * 100:.1f}%")

    console.print(track_table)
    return 0


def list_cases_cli() -> int:
    cases = load_all_test_cases()
    table = Table(title="Available Līlāvatī-Bench Golden Test Cases", show_header=True)
    table.add_column("Case ID", style="bold yellow")
    table.add_column("Track", style="magenta")
    table.add_column("Scenario Title", style="cyan")
    table.add_column("Cutoff Date", style="dim")

    for c in cases:
        table.add_row(c.case_id, c.track, c.title, str(c.as_of_date))

    console.print(table)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="lilavati-bench",
        description="Līlāvatī-Bench: Financial AI Agent & Foundation Model Evaluation Suite",
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    run_parser = subparsers.add_parser("run", help="Run benchmark suite against an agent/model")
    run_parser.add_argument(
        "--model", "-m", default="lilavati-reference", help="Agent or model identifier"
    )
    run_parser.add_argument("--track", "-t", default="all", help="Specific track to evaluate")
    run_parser.add_argument(
        "--format",
        "-f",
        choices=["rich", "markdown", "json"],
        default="rich",
        help="Output display format",
    )

    subparsers.add_parser("list-cases", help="List all available golden test cases")

    args = parser.parse_args()

    if args.command == "run":
        sys.exit(run_benchmark_cli(args))
    elif args.command == "list-cases":
        sys.exit(list_cases_cli())
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
