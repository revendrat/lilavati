"""Foundation Model Connectivity & Multi-Provider LLM Client for Project Līlāvatī."""

from lilavati.llm.client import (
    BaseLLMClient,
    LLMMessage,
    LLMResponse,
    LLMToolCall,
    LLMUsage,
    UniversalLLMClient,
)
from lilavati.llm.providers import (
    INSTITUTIONAL_MODEL_PRESETS,
    ModelProvider,
    ModelSpec,
)

__all__ = [
    "ModelProvider",
    "ModelSpec",
    "INSTITUTIONAL_MODEL_PRESETS",
    "BaseLLMClient",
    "UniversalLLMClient",
    "LLMMessage",
    "LLMToolCall",
    "LLMResponse",
    "LLMUsage",
]
