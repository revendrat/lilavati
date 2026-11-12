"""
Formal Invariant & SMT Reflection Prompts for Neuro-Symbolic Self-Correction.

When Z3 SMT invariant verification fails (e.g. Assets != Liabilities + Equity),
these templates generate structured feedback containing the exact unsatisfiable core,
enabling the LLM agent to iteratively revise parameter extractions without hallucinating.
"""

from __future__ import annotations

from collections.abc import Sequence


def generate_smt_reflection_prompt(
    invariant_name: str,
    violations: Sequence[str],
    current_values: dict[str, float | str | bool],
) -> str:
    """Constructs a feedback prompt detailing formal invariant violations."""
    lines = [
        f"### CRITICAL FORMAL INVARIANT FAILURE: {invariant_name}",
        "",
        "The Z3 SMT solver proved that your extracted/projected financial model violates fundamental identities:",
        "",
    ]
    for idx, v in enumerate(violations, 1):
        lines.append(f"{idx}. {v}")

    lines.append("")
    lines.append("### EVALUATED PARAMETERS:")
    for k, val in current_values.items():
        lines.append(f"- {k}: {val}")

    lines.append("")
    lines.append("### REQUIRED ACTION:")
    lines.append(
        "Re-examine the primary source disclosures, footnotes, and adjustments. "
        "Correct the line items so that the formal mathematical invariant holds strictly (SAT). "
        "Do NOT invent numbers; cite the source snippet or footnote reconciling the difference."
    )
    return "\n".join(lines)


def generate_citation_failure_prompt(
    failed_claims: Sequence[str],
) -> str:
    """Feedback prompt when claims lack cryptographic provenance."""
    lines = [
        "### CITATION PROVENANCE REJECTION",
        "",
        "The following quantitative claims failed cryptographic provenance verification:",
    ]
    for c in failed_claims:
        lines.append(f"- {c}")

    lines.append("")
    lines.append(
        "Every numerical claim must carry a CitationRef with a valid 64-character SHA-256 document hash, "
        "page number, and verbatim snippet. Provide valid citations or retract the unverified claims."
    )
    return "\n".join(lines)
