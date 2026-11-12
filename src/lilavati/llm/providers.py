"""
LLM Provider Configurations and Model Registry for Project Līlāvatī.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ModelProvider(StrEnum):
    """Supported Foundation Model & LLM Providers."""

    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"
    VLLM = "vllm"
    MOCK = "mock"


class ModelSpec(BaseModel):
    """Configuration specification for a foundation model."""

    model_config = ConfigDict(frozen=True)

    provider: ModelProvider
    model_name: str
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)
    api_key_env_var: str | None = None
    base_url: str | None = None


# Pre-configured institutional model profiles
INSTITUTIONAL_MODEL_PRESETS: dict[str, ModelSpec] = {
    # Gemini Models (Google DeepMind)
    "gemini-2.5-pro": ModelSpec(
        provider=ModelProvider.GEMINI,
        model_name="gemini-2.5-pro",
        api_key_env_var="GEMINI_API_KEY",
    ),
    "gemini-2.5-flash": ModelSpec(
        provider=ModelProvider.GEMINI,
        model_name="gemini-2.5-flash",
        api_key_env_var="GEMINI_API_KEY",
    ),
    # Anthropic Claude
    "claude-3-7-sonnet": ModelSpec(
        provider=ModelProvider.ANTHROPIC,
        model_name="claude-3-7-sonnet-20250219",
        api_key_env_var="ANTHROPIC_API_KEY",
    ),
    # OpenAI
    "gpt-4o": ModelSpec(
        provider=ModelProvider.OPENAI,
        model_name="gpt-4o",
        api_key_env_var="OPENAI_API_KEY",
    ),
    "o3-mini": ModelSpec(
        provider=ModelProvider.OPENAI,
        model_name="o3-mini",
        api_key_env_var="OPENAI_API_KEY",
    ),
    # Local Open-Source Financial Foundation Models
    "llama3-fin-8b": ModelSpec(
        provider=ModelProvider.OLLAMA,
        model_name="llama3-fin:8b",
        base_url="http://localhost:11434",
    ),
    "vllm-finance-70b": ModelSpec(
        provider=ModelProvider.VLLM,
        model_name="meta-llama/Llama-3.3-70B-Instruct",
        base_url="http://localhost:8000/v1",
    ),
    # Deterministic Mock Provider for offline testing
    "mock-evaluator": ModelSpec(
        provider=ModelProvider.MOCK,
        model_name="lilavati-mock-reference",
    ),
}
