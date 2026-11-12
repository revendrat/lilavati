"""Prompt templates and system instructions for Project Līlāvatī."""

from lilavati.prompts.committee import (
    BULL_RESEARCHER_PROMPT,
    FORENSIC_BEAR_PROMPT,
    PORTFOLIO_MANAGER_PROMPT,
    SUSTAINABILITY_ANALYST_PROMPT,
)
from lilavati.prompts.reflection import (
    generate_citation_failure_prompt,
    generate_smt_reflection_prompt,
)
from lilavati.prompts.system import (
    LILAVATI_CORE_SYSTEM_PROMPT,
    get_agent_system_prompt,
)

__all__ = [
    "LILAVATI_CORE_SYSTEM_PROMPT",
    "get_agent_system_prompt",
    "BULL_RESEARCHER_PROMPT",
    "FORENSIC_BEAR_PROMPT",
    "SUSTAINABILITY_ANALYST_PROMPT",
    "PORTFOLIO_MANAGER_PROMPT",
    "generate_smt_reflection_prompt",
    "generate_citation_failure_prompt",
]
