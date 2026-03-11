"""LLM provider abstraction layer with streaming, retry, JSON mode, and timeout."""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("codeforge.llm.providers")


@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: int
    raw_response: dict | None = None


# ---------------------------------------------------------------------------
# Retry helper
# ---------------------------------------------------------------------------

def _is_retryable(exc: Exception) -> bool:
    """Determine if an exception is transient and worth retrying."""
    msg = str(exc).lower()
    retryable_signals = [
        "rate limit", "429", "500", "502", "503", "504",
        "timeout", "timed out", "connection", "temporarily",
        "overloaded", "capacity", "throttl",
    ]
    return any(s in msg for s in retryable_signals)


async def _retry_async(fn, *args, max_attempts: int = 3, base_delay: float = 1.0, **kwargs) -> Any:
    """Retry an async function with exponential backoff + jitter."""
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if not _is_retryable(e) or attempt >= max_attempts - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            logger.warning(
                "LLM call failed (attempt %d/%d): %s — retrying in %.1fs",
                attempt + 1, max_attempts, e, delay,
            )
            await asyncio.sleep(delay)
    raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Base provider
# ---------------------------------------------------------------------------

class BaseLLMProvider(ABC):
    """Abstract LLM provider with generate, stream, and structured output."""

    MAX_RETRIES: int = 3
    TIMEOUT_SECONDS: float = 120.0

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> LLMResponse: ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        schema: dict | None = None,
    ) -> LLMResponse:
        """Generate with JSON output enforcement (uses native JSON mode where available)."""
        ...

    async def astream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream response chunks. Default: falls back to buffered generate()."""
        response = await self.generate(prompt, system_prompt, temperature, max_tokens)
        yield response.content

    @abstractmethod
    async def health_check(self) -> bool: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        from langchain_openai import ChatOpenAI

        self.llm = ChatOpenAI(
            api_key=api_key,
            model=model,
            temperature=0,
            request_timeout=self.TIMEOUT_SECONDS,
        )
        self._model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> LLMResponse:
        from langchain_core.messages import HumanMessage, SystemMessage

        messages: list = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        llm = self.llm
        bind_kwargs: dict[str, Any] = {}
        if temperature != 0.0:
            bind_kwargs["temperature"] = temperature
        if max_tokens != 4096:
            bind_kwargs["max_tokens"] = max_tokens
        if response_format:
            bind_kwargs["response_format"] = response_format
        if bind_kwargs:
            llm = llm.bind(**bind_kwargs)

        async def _invoke():
            return await asyncio.wait_for(
                llm.ainvoke(messages),
                timeout=self.TIMEOUT_SECONDS,
            )

        start = time.perf_counter()
        response = await _retry_async(_invoke, max_attempts=self.MAX_RETRIES)
        latency_ms = int((time.perf_counter() - start) * 1000)

        usage = getattr(response, "usage_metadata", None) or {}
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        total_tokens = usage.get("total_tokens", input_tokens + output_tokens)

        return LLMResponse(
            content=response.content,
            model=self._model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
        )

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        schema: dict | None = None,
    ) -> LLMResponse:
        # Use native JSON mode
        response = await self.generate(
            prompt,
            system_prompt + "\n\nRespond ONLY with valid JSON. No markdown fences.",
            response_format={"type": "json_object"},
        )
        try:
            json.loads(response.content)
        except json.JSONDecodeError:
            # Retry with stronger instruction (no JSON mode — some models don't support it)
            response = await self.generate(
                prompt,
                system_prompt + "\n\nCRITICAL: Output ONLY a raw JSON object. Nothing else. No markdown.",
            )
        return response

    async def astream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        from langchain_core.messages import HumanMessage, SystemMessage

        messages: list = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        async for chunk in self.llm.astream(messages):
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content

    async def health_check(self) -> bool:
        try:
            await asyncio.wait_for(self.generate("Say OK", max_tokens=5), timeout=10)
            return True
        except Exception:
            return False

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "openai"


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        from langchain_anthropic import ChatAnthropic

        self.llm = ChatAnthropic(
            api_key=api_key,
            model=model,
            temperature=0,
            timeout=self.TIMEOUT_SECONDS,
            max_tokens=4096,
        )
        self._model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> LLMResponse:
        from langchain_core.messages import HumanMessage, SystemMessage

        messages: list = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        llm = self.llm
        bind_kwargs: dict[str, Any] = {}
        if max_tokens != 4096:
            bind_kwargs["max_tokens"] = max_tokens
        if bind_kwargs:
            llm = llm.bind(**bind_kwargs)

        async def _invoke():
            return await asyncio.wait_for(
                llm.ainvoke(messages),
                timeout=self.TIMEOUT_SECONDS,
            )

        start = time.perf_counter()
        response = await _retry_async(_invoke, max_attempts=self.MAX_RETRIES)
        latency_ms = int((time.perf_counter() - start) * 1000)

        usage = getattr(response, "usage_metadata", None) or {}
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        total_tokens = usage.get("total_tokens", input_tokens + output_tokens)

        return LLMResponse(
            content=response.content if isinstance(response.content, str) else str(response.content),
            model=self._model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
        )

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        schema: dict | None = None,
    ) -> LLMResponse:
        json_sys = system_prompt + "\n\nRespond ONLY with valid JSON. No markdown fences, no explanation."
        response = await self.generate(prompt, json_sys)
        try:
            json.loads(response.content)
        except json.JSONDecodeError:
            response = await self.generate(
                prompt,
                json_sys + "\nCRITICAL: Output ONLY a raw JSON object. Nothing else.",
            )
        return response

    async def astream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        from langchain_core.messages import HumanMessage, SystemMessage

        messages: list = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        async for chunk in self.llm.astream(messages):
            content = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
            if content:
                yield content

    async def health_check(self) -> bool:
        try:
            await asyncio.wait_for(self.generate("Say OK", max_tokens=5), timeout=10)
            return True
        except Exception:
            return False

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "anthropic"


# ---------------------------------------------------------------------------
# Ollama (local)
# ---------------------------------------------------------------------------

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3:8b") -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> LLMResponse:
        import httpx

        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if system_prompt:
            payload["system"] = system_prompt
        # Native JSON mode for Ollama
        if response_format and response_format.get("type") == "json_object":
            payload["format"] = "json"

        async def _invoke():
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                resp = await client.post(f"{self._base_url}/api/generate", json=payload)
                resp.raise_for_status()
                return resp.json()

        start = time.perf_counter()
        data = await _retry_async(_invoke, max_attempts=self.MAX_RETRIES)
        latency_ms = int((time.perf_counter() - start) * 1000)

        content = data.get("response", "")
        input_tokens = data.get("prompt_eval_count") or max(1, len(prompt.split()))
        output_tokens = data.get("eval_count") or max(1, len(content.split()))

        return LLMResponse(
            content=content,
            model=self._model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
            raw_response=data,
        )

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        schema: dict | None = None,
    ) -> LLMResponse:
        # Ollama supports native JSON format
        response = await self.generate(
            prompt,
            system_prompt + "\n\nRespond ONLY with valid JSON.",
            response_format={"type": "json_object"},
        )
        try:
            json.loads(response.content)
        except json.JSONDecodeError:
            response = await self.generate(
                prompt,
                system_prompt + "\n\nCRITICAL: Output ONLY a raw JSON object. Nothing else.",
            )
        return response

    async def astream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        import httpx

        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
            async with client.stream("POST", f"{self._base_url}/api/generate", json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if chunk.get("response"):
                                yield chunk["response"]
                        except json.JSONDecodeError:
                            pass

    async def health_check(self) -> bool:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                if resp.status_code != 200:
                    return False
                tags = resp.json()
                models = [m.get("name", "") for m in tags.get("models", [])]
                return any(self._model in m for m in models) or len(models) > 0
        except Exception:
            return False

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "ollama"


# ---------------------------------------------------------------------------
# OpenRouter (primary gateway for this project)
# ---------------------------------------------------------------------------

class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter — OpenAI-compatible gateway to 200+ models.

    Supports JSON mode, streaming, and automatic model routing.
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str, model: str = "openai/gpt-4o-mini") -> None:
        from langchain_openai import ChatOpenAI

        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=self.BASE_URL,
            model=model,
            temperature=0,
            request_timeout=self.TIMEOUT_SECONDS,
            default_headers={
                "HTTP-Referer": "https://codeforge.dev",
                "X-Title": "CodeForge AI Code Agent",
            },
        )
        self._model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> LLMResponse:
        from langchain_core.messages import HumanMessage, SystemMessage

        messages: list = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        llm = self.llm
        bind_kwargs: dict[str, Any] = {}
        if temperature != 0.0:
            bind_kwargs["temperature"] = temperature
        if max_tokens != 4096:
            bind_kwargs["max_tokens"] = max_tokens
        if response_format:
            bind_kwargs["response_format"] = response_format
        if bind_kwargs:
            llm = llm.bind(**bind_kwargs)

        async def _invoke():
            return await asyncio.wait_for(
                llm.ainvoke(messages),
                timeout=self.TIMEOUT_SECONDS,
            )

        start = time.perf_counter()
        response = await _retry_async(_invoke, max_attempts=self.MAX_RETRIES)
        latency_ms = int((time.perf_counter() - start) * 1000)

        usage = getattr(response, "usage_metadata", None) or {}
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        total_tokens = usage.get("total_tokens", input_tokens + output_tokens)

        return LLMResponse(
            content=response.content,
            model=self._model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
        )

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        schema: dict | None = None,
    ) -> LLMResponse:
        # OpenRouter passes through response_format to underlying model
        json_sys = system_prompt + "\n\nRespond ONLY with valid JSON. No markdown fences."
        response = await self.generate(
            prompt,
            json_sys,
            response_format={"type": "json_object"},
        )
        try:
            json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback without response_format (some models don't support it)
            response = await self.generate(
                prompt,
                json_sys + "\nCRITICAL: Output ONLY a raw JSON object. Nothing else.",
            )
        return response

    async def astream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        from langchain_core.messages import HumanMessage, SystemMessage

        messages: list = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        async for chunk in self.llm.astream(messages):
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content

    async def health_check(self) -> bool:
        try:
            await asyncio.wait_for(self.generate("Say OK", max_tokens=5), timeout=15)
            return True
        except Exception:
            return False

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "openrouter"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

class LLMProviderFactory:
    _PROVIDERS = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
        "openrouter": OpenRouterProvider,
    }

    @staticmethod
    def create(provider: str, **kwargs: object) -> BaseLLMProvider:
        cls = LLMProviderFactory._PROVIDERS.get(provider)
        if cls is None:
            raise ValueError(f"Unknown provider: {provider}. Available: {list(LLMProviderFactory._PROVIDERS)}")
        return cls(**kwargs)  # type: ignore[arg-type]
