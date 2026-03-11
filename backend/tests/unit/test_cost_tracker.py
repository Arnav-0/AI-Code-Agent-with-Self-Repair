"""Unit tests for the Cost Tracker."""

from __future__ import annotations

import pytest

from app.llm.cost_tracker import CostTracker
from app.llm.providers import LLMResponse


def _resp(model: str, input_tokens: int, output_tokens: int) -> LLMResponse:
    return LLMResponse(
        content="test",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        latency_ms=100,
    )


@pytest.mark.unit
def test_gpt4_cost_calculation() -> None:
    """GPT-4 calls should have non-zero cost."""
    tracker = CostTracker()
    record = tracker.record(_resp("gpt-4", 1000, 500))
    assert record.cost_usd > 0
    # 1000 * 0.03/1000 + 500 * 0.06/1000 = 0.03 + 0.03 = 0.06
    assert abs(record.cost_usd - 0.06) < 0.001


@pytest.mark.unit
def test_llama_free_cost() -> None:
    """Local llama3 model should have zero cost."""
    tracker = CostTracker()
    record = tracker.record(_resp("llama3:8b", 1000, 500))
    assert record.cost_usd == 0.0


@pytest.mark.unit
def test_unknown_model_uses_default() -> None:
    """Unknown models should fall back to a default estimate (non-negative)."""
    tracker = CostTracker()
    record = tracker.record(_resp("unknown-model-xyz", 500, 200))
    assert record.cost_usd >= 0.0  # Should not raise, and should be non-negative


@pytest.mark.unit
def test_summary_aggregation() -> None:
    """Summary should correctly aggregate total cost and tokens."""
    tracker = CostTracker()
    tracker.record(_resp("gpt-4", 500, 200))
    tracker.record(_resp("llama3:8b", 300, 100))
    summary = tracker.get_summary()
    assert summary["records_count"] == 2
    assert summary["total_cost"] > 0
    assert summary["total_tokens"] == 1100


@pytest.mark.unit
def test_cost_by_model_breakdown() -> None:
    """Cost summary should break down costs per model."""
    tracker = CostTracker()
    tracker.record(_resp("gpt-4", 1000, 500))
    tracker.record(_resp("gpt-4o-mini", 2000, 1000))
    summary = tracker.get_summary()
    assert "gpt-4" in summary["cost_by_model"]
    assert "gpt-4o-mini" in summary["cost_by_model"]
    assert summary["cost_by_model"]["gpt-4"] > summary["cost_by_model"]["gpt-4o-mini"]


@pytest.mark.unit
def test_savings_calculation() -> None:
    """Using cheaper models should show positive estimated savings vs gpt-4."""
    tracker = CostTracker()
    tracker.record(_resp("llama3:8b", 1000, 500))
    summary = tracker.get_summary()
    assert summary["estimated_savings"] > 0


@pytest.mark.unit
def test_reset_clears_all() -> None:
    """Resetting the tracker should zero out all records and totals."""
    tracker = CostTracker()
    tracker.record(_resp("gpt-4", 1000, 500))
    assert tracker.total_cost > 0
    assert len(tracker.records) > 0

    tracker.reset()
    assert tracker.total_cost == 0.0
    assert len(tracker.records) == 0
    summary = tracker.get_summary()
    assert summary["records_count"] == 0
    assert summary["total_cost"] == 0.0
