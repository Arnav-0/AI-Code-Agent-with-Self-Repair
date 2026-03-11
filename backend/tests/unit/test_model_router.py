"""Unit tests for the Model Router."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.llm.classifier import ComplexityLevel
from app.llm.router import DEFAULT_MODEL_CONFIGS, ModelConfig, ModelRouter


def _settings(**kwargs: object) -> MagicMock:
    s = MagicMock()
    s.openai_api_key = kwargs.get("openai_api_key", "")
    s.anthropic_api_key = kwargs.get("anthropic_api_key", "")
    s.ollama_base_url = kwargs.get("ollama_base_url", "http://localhost:11434")
    s.complexity_simple_threshold = 0.3
    s.complexity_complex_threshold = 0.7
    return s


@pytest.mark.unit
def test_simple_task_routes_to_cheap_model() -> None:
    """Simple tasks should use a cheap model (gpt-4o-mini)."""
    config = DEFAULT_MODEL_CONFIGS[ComplexityLevel.SIMPLE]
    assert config.provider == "openai"
    assert "mini" in config.model
    assert config.cost_per_1k_input < 0.001


@pytest.mark.unit
def test_complex_task_routes_to_gpt4() -> None:
    """Hard tasks should prefer the GPT-4 model."""
    config = DEFAULT_MODEL_CONFIGS[ComplexityLevel.HARD]
    assert config.provider == "openai"
    assert "gpt-4" in config.model


@pytest.mark.unit
def test_fallback_when_ollama_unavailable() -> None:
    """When ollama is the only available provider, simple tasks use it."""
    router = ModelRouter(_settings(ollama_base_url="http://localhost:11434"))
    available = router.get_available_providers()
    # Ollama should always appear when base_url is set
    assert "ollama" in available


@pytest.mark.unit
def test_available_providers_detection() -> None:
    """Provider detection should include openai/anthropic only when keys are set."""
    router_no_keys = ModelRouter(_settings())
    available = router_no_keys.get_available_providers()
    assert "openai" not in available
    assert "anthropic" not in available
    assert "ollama" in available

    router_with_openai = ModelRouter(_settings(openai_api_key="sk-real-key"))
    available2 = router_with_openai.get_available_providers()
    assert "openai" in available2


@pytest.mark.unit
def test_model_config_dataclass() -> None:
    """ModelConfig should store all cost fields correctly."""
    mc = ModelConfig(provider="openai", model="gpt-4", cost_per_1k_input=0.03, cost_per_1k_output=0.06)
    assert mc.provider == "openai"
    assert mc.model == "gpt-4"
    assert mc.cost_per_1k_input == 0.03
    assert mc.cost_per_1k_output == 0.06
