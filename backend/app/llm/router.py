"""Intelligent model router — cost-aware selection with escalation and fallback."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from app.llm.classifier import ComplexityLevel, TaskClassifier
from app.llm.providers import BaseLLMProvider, LLMProviderFactory

logger = logging.getLogger("codeforge.router")


@dataclass
class ModelConfig:
    provider: str
    model: str
    cost_per_1k_input: float
    cost_per_1k_output: float


# ---------------------------------------------------------------------------
# Model tiers — the WHOLE POINT of smart routing
# ---------------------------------------------------------------------------

# Default models when provider-specific keys are available
DEFAULT_MODEL_CONFIGS: dict[ComplexityLevel, ModelConfig] = {
    ComplexityLevel.SIMPLE: ModelConfig(
        provider="openai",
        model="gpt-4o-mini",
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
    ),
    ComplexityLevel.MEDIUM: ModelConfig(
        provider="openai",
        model="gpt-4o-mini",
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
    ),
    ComplexityLevel.HARD: ModelConfig(
        provider="openai",
        model="gpt-4o",
        cost_per_1k_input=0.0025,
        cost_per_1k_output=0.01,
    ),
}

# OpenRouter model tiers — DIFFERENT models per complexity
OPENROUTER_MODELS: dict[ComplexityLevel, str] = {
    ComplexityLevel.SIMPLE: "openai/gpt-4o-mini",
    ComplexityLevel.MEDIUM: "openai/gpt-4o-mini",
    ComplexityLevel.HARD: "openai/gpt-4o",
}

# Escalation chain: when a model fails on retries, upgrade to a stronger one
ESCALATION_CHAIN: list[str] = [
    "openai/gpt-4o-mini",      # Tier 1: cheap & fast
    "openai/gpt-4o",           # Tier 2: more capable
    "anthropic/claude-sonnet-4-20250514",  # Tier 3: strongest
]

# Fallback chains by complexity tier
_SIMPLE_FALLBACK = ["openrouter", "ollama", "openai", "anthropic"]
_COMPLEX_FALLBACK = ["openrouter", "openai", "anthropic", "ollama"]

# Provider health cache: {provider_name: (is_healthy, timestamp)}
_health_cache: dict[str, tuple[bool, float]] = {}
_HEALTH_TTL = 300.0  # 5 minutes


class ModelRouter:
    def __init__(self, settings: object) -> None:
        self._settings = settings
        self._classifier = TaskClassifier(use_llm=False)

    # ------------------------------------------------------------------
    # Primary routing
    # ------------------------------------------------------------------

    async def route(
        self, prompt: str
    ) -> tuple[BaseLLMProvider, ModelConfig, ComplexityLevel]:
        """Classify prompt complexity and route to the best available model."""
        level, confidence = self._classifier.classify(prompt)
        config = DEFAULT_MODEL_CONFIGS[level]

        available = self.get_available_providers()
        if not available:
            raise RuntimeError("No LLM providers configured. Set an API key in .env")

        fallback_chain = _SIMPLE_FALLBACK if level == ComplexityLevel.SIMPLE else _COMPLEX_FALLBACK

        # Build ordered list: preferred provider first, then fallback chain
        tried: set[str] = set()
        for provider_name in [config.provider, *fallback_chain]:
            if provider_name in tried or provider_name not in available:
                continue
            tried.add(provider_name)

            model = self._get_model_for_tier(provider_name, level)
            provider = self._create_provider(provider_name, model)
            actual_config = ModelConfig(
                provider=provider_name,
                model=model,
                cost_per_1k_input=config.cost_per_1k_input,
                cost_per_1k_output=config.cost_per_1k_output,
            )
            logger.info(
                "%s (conf=%.2f) -> %s/%s",
                level.name, confidence, provider_name, model,
            )
            return (provider, actual_config, level)

        raise RuntimeError(f"No available LLM providers for {level.name} task")

    # ------------------------------------------------------------------
    # Model escalation for retries
    # ------------------------------------------------------------------

    def get_escalated_provider(
        self, current_model: str, retry_count: int
    ) -> tuple[BaseLLMProvider, str] | None:
        """Get a stronger model for retry attempts.

        Returns (provider, model_name) or None if no escalation available.
        """
        available = self.get_available_providers()

        # Find current position in escalation chain
        current_idx = -1
        for i, model in enumerate(ESCALATION_CHAIN):
            if model == current_model or current_model.endswith(model.split("/")[-1]):
                current_idx = i
                break

        # Try next tier up
        for model in ESCALATION_CHAIN[current_idx + 1:]:
            provider_name = model.split("/")[0] if "/" in model else "openrouter"
            # OpenRouter can access all models
            if "openrouter" in available:
                provider = self._create_provider("openrouter", model)
                logger.info(
                    "Escalating model: %s -> %s (retry #%d)",
                    current_model, model, retry_count,
                )
                return (provider, model)
            # Direct provider access
            if provider_name in available:
                base_model = model.split("/")[-1] if "/" in model else model
                provider = self._create_provider(provider_name, base_model)
                logger.info(
                    "Escalating model: %s -> %s/%s (retry #%d)",
                    current_model, provider_name, base_model, retry_count,
                )
                return (provider, model)

        return None

    # ------------------------------------------------------------------
    # Provider creation and model mapping
    # ------------------------------------------------------------------

    def get_provider(self, provider_name: str, model: str) -> BaseLLMProvider:
        """Create a provider instance (public API for orchestrator)."""
        return self._create_provider(provider_name, model)

    def _create_provider(self, provider_name: str, model: str) -> BaseLLMProvider:
        kwargs: dict[str, object] = {}
        if provider_name == "openai":
            kwargs = {"api_key": getattr(self._settings, "openai_api_key", ""), "model": model}
        elif provider_name == "anthropic":
            kwargs = {"api_key": getattr(self._settings, "anthropic_api_key", ""), "model": model}
        elif provider_name == "openrouter":
            kwargs = {"api_key": getattr(self._settings, "openrouter_api_key", ""), "model": model}
        elif provider_name == "ollama":
            kwargs = {
                "base_url": getattr(self._settings, "ollama_base_url", "http://localhost:11434"),
                "model": model,
            }
        return LLMProviderFactory.create(provider_name, **kwargs)

    def _get_model_for_tier(self, provider_name: str, level: ComplexityLevel) -> str:
        """Get the right model for a provider + complexity tier."""
        if provider_name == "openrouter":
            # Read from settings first, fall back to tier defaults
            settings = self._settings
            if level == ComplexityLevel.HARD:
                custom = getattr(settings, "default_complex_model", "")
                if custom:
                    return custom
            else:
                custom = getattr(settings, "default_simple_model", "")
                if custom:
                    return custom
            return OPENROUTER_MODELS.get(level, "openai/gpt-4o-mini")

        defaults: dict[str, dict[ComplexityLevel, str]] = {
            "openai": {
                ComplexityLevel.SIMPLE: "gpt-4o-mini",
                ComplexityLevel.MEDIUM: "gpt-4o-mini",
                ComplexityLevel.HARD: "gpt-4o",
            },
            "anthropic": {
                ComplexityLevel.SIMPLE: "claude-haiku-4-5-20251001",
                ComplexityLevel.MEDIUM: "claude-sonnet-4-20250514",
                ComplexityLevel.HARD: "claude-sonnet-4-20250514",
            },
            "ollama": {
                ComplexityLevel.SIMPLE: "llama3:8b",
                ComplexityLevel.MEDIUM: "llama3:8b",
                ComplexityLevel.HARD: "llama3:70b",
            },
        }
        provider_defaults = defaults.get(provider_name, {})
        return provider_defaults.get(level, "gpt-4o-mini")

    # ------------------------------------------------------------------
    # Provider availability
    # ------------------------------------------------------------------

    def get_available_providers(self) -> list[str]:
        available = []
        openai_key = getattr(self._settings, "openai_api_key", "") or ""
        anthropic_key = getattr(self._settings, "anthropic_api_key", "") or ""
        openrouter_key = getattr(self._settings, "openrouter_api_key", "") or ""
        ollama_url = getattr(self._settings, "ollama_base_url", "") or ""

        if openai_key and not openai_key.startswith("sk-your"):
            available.append("openai")
        if anthropic_key and not anthropic_key.startswith("sk-ant-your"):
            available.append("anthropic")
        if openrouter_key and openrouter_key not in ("sk-or-your-key-here", ""):
            available.append("openrouter")
        if ollama_url and ollama_url != "":
            available.append("ollama")
        return available

    # ------------------------------------------------------------------
    # Cost estimation
    # ------------------------------------------------------------------

    async def estimate_cost(self, prompt: str, model_config: ModelConfig) -> float:
        token_estimate = len(prompt.split()) * 1.3
        return (token_estimate / 1000) * model_config.cost_per_1k_input
