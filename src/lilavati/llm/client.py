"""
Multi-Provider LLM Client for Financial Agent Operations.

Connects to Gemini, Anthropic, OpenAI, or local OSS financial models (via vLLM / Ollama)
with support for FastMCP tool declarations, function calling, structured outputs, and automated retries.
"""

from __future__ import annotations

import json
import os
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ConfigDict, Field

from lilavati.llm.providers import ModelProvider, ModelSpec

T = TypeVar("T", bound=BaseModel)


class LLMToolCall(BaseModel):
    """Tool invocation request emitted by the language model."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    arguments: dict[str, Any]


class LLMMessage(BaseModel):
    """Normalized chat message for LLM interactions."""

    role: str = Field(..., description="system, user, assistant, or tool")
    content: str = Field(default="")
    tool_calls: list[LLMToolCall] | None = None
    tool_call_id: str | None = None


class LLMUsage(BaseModel):
    """Token consumption metrics for auditing and cost attribution."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMResponse(BaseModel):
    """Normalized response from an LLM model."""

    content: str
    tool_calls: list[LLMToolCall] = Field(default_factory=list)
    usage: LLMUsage = Field(default_factory=LLMUsage)
    raw_response: dict[str, Any] = Field(default_factory=dict)


class BaseLLMClient:
    """Abstract interface for LLM model connectivity."""

    def generate(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        raise NotImplementedError

    def generate_structured(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
    ) -> T:
        raise NotImplementedError


class UniversalLLMClient(BaseLLMClient):
    """
    Universal HTTP-based LLM client supporting:
    - Gemini (generativelanguage.googleapis.com)
    - OpenAI / vLLM / Ollama (OpenAI-compatible /chat/completions)
    - Anthropic (/v1/messages)
    """

    def __init__(self, spec: ModelSpec, api_key: str | None = None) -> None:
        self.spec = spec
        if api_key:
            self.api_key = api_key
        elif spec.api_key_env_var:
            self.api_key = os.environ.get(spec.api_key_env_var, "")
        else:
            self.api_key = ""

    def generate(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        if self.spec.provider == ModelProvider.MOCK:
            return LLMResponse(
                content="[Mock LLM Response] Operation completed according to institutional constraints.",
                usage=LLMUsage(prompt_tokens=10, completion_tokens=10, total_tokens=20),
            )

        if self.spec.provider in (ModelProvider.OPENAI, ModelProvider.VLLM, ModelProvider.OLLAMA):
            return self._call_openai_compatible(messages, tools)
        elif self.spec.provider == ModelProvider.GEMINI:
            return self._call_gemini(messages, tools)
        elif self.spec.provider == ModelProvider.ANTHROPIC:
            return self._call_anthropic(messages, tools)
        else:
            raise ValueError(f"Unsupported provider: {self.spec.provider}")

    def generate_structured(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
    ) -> T:
        """Forces the LLM to output valid JSON conforming to a Pydantic schema."""
        schema_json = json.dumps(response_model.model_json_schema())
        system_instruction = f"You MUST respond ONLY with a valid JSON object strictly matching this schema:\n{schema_json}"
        augmented = [LLMMessage(role="system", content=system_instruction)] + messages
        response = self.generate(augmented)

        raw_text = response.content.strip()
        # Clean markdown code blocks if present
        if raw_text.startswith("```json"):
            raw_text = raw_text.removeprefix("```json").removesuffix("```").strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.removeprefix("```").removesuffix("```").strip()

        data = json.loads(raw_text)
        return response_model.model_validate(data)

    def _call_openai_compatible(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        base_url = self.spec.base_url or "https://api.openai.com/v1"
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        openai_messages: list[dict[str, Any]] = []
        for m in messages:
            entry: dict[str, Any] = {"role": m.role, "content": m.content}
            if m.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                    }
                    for tc in m.tool_calls
                ]
            if m.tool_call_id:
                entry["tool_call_id"] = m.tool_call_id
            openai_messages.append(entry)

        payload: dict[str, Any] = {
            "model": self.spec.model_name,
            "messages": openai_messages,
            "temperature": self.spec.temperature,
            "max_tokens": self.spec.max_tokens,
        }
        if tools:
            payload["tools"] = tools

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]["message"]
        content = choice.get("content") or ""
        parsed_tools: list[LLMToolCall] = []

        if "tool_calls" in choice and choice["tool_calls"]:
            for tc in choice["tool_calls"]:
                fn = tc["function"]
                args = (
                    json.loads(fn["arguments"])
                    if isinstance(fn["arguments"], str)
                    else fn["arguments"]
                )
                parsed_tools.append(LLMToolCall(id=tc["id"], name=fn["name"], arguments=args))

        usage_dict = data.get("usage", {})
        usage = LLMUsage(
            prompt_tokens=usage_dict.get("prompt_tokens", 0),
            completion_tokens=usage_dict.get("completion_tokens", 0),
            total_tokens=usage_dict.get("total_tokens", 0),
        )
        return LLMResponse(content=content, tool_calls=parsed_tools, usage=usage, raw_response=data)

    def _call_gemini(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        # Standard Gemini generateContent REST endpoint
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.spec.model_name}:generateContent?key={self.api_key}"
        )
        headers = {"Content-Type": "application/json"}

        contents: list[dict[str, Any]] = []
        for m in messages:
            role = "user" if m.role in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.spec.temperature,
                "maxOutputTokens": self.spec.max_tokens,
            },
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        candidates = data.get("candidates", [])
        if not candidates:
            return LLMResponse(content="", raw_response=data)

        parts = candidates[0].get("content", {}).get("parts", [])
        text_content = "".join(p.get("text", "") for p in parts)
        usage_md = data.get("usageMetadata", {})

        usage = LLMUsage(
            prompt_tokens=usage_md.get("promptTokenCount", 0),
            completion_tokens=usage_md.get("candidatesTokenCount", 0),
            total_tokens=usage_md.get("totalTokenCount", 0),
        )
        return LLMResponse(content=text_content, usage=usage, raw_response=data)

    def _call_anthropic(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        system_prompts = [m.content for m in messages if m.role == "system"]
        chat_messages = [
            {"role": "user" if m.role == "user" else "assistant", "content": m.content}
            for m in messages
            if m.role != "system"
        ]

        payload: dict[str, Any] = {
            "model": self.spec.model_name,
            "messages": chat_messages,
            "max_tokens": self.spec.max_tokens,
            "temperature": self.spec.temperature,
        }
        if system_prompts:
            payload["system"] = "\n\n".join(system_prompts)

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content_parts = data.get("content", [])
        text_content = "".join(
            cp.get("text", "") for cp in content_parts if cp.get("type") == "text"
        )
        usage_data = data.get("usage", {})

        usage = LLMUsage(
            prompt_tokens=usage_data.get("input_tokens", 0),
            completion_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
        )
        return LLMResponse(content=text_content, usage=usage, raw_response=data)
