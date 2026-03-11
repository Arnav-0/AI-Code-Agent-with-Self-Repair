"""Cost tracking with model normalization, budget enforcement, and per-agent attribution."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("codeforge.cost_tracker")

# ---------------------------------------------------------------------------
# Comprehensive pricing table (USD per 1K tokens: input, output)
# ---------------------------------------------------------------------------
PRICING: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4": (0.03, 0.06),
    "gpt-4-turbo": (0.01, 0.03),
    "gpt-4-turbo-2024-04-09": (0.01, 0.03),
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-2024-08-06": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4o-mini-2024-07-18": (0.00015, 0.0006),
    "gpt-3.5-turbo": (0.0005, 0.0015),
    "o1": (0.015, 0.06),
    "o1-mini": (0.003, 0.012),
    "o3-mini": (0.0011, 0.0044),
    # Anthropic
    "claude-opus-4-20250514": (0.015, 0.075),
    "claude-sonnet-4-20250514": (0.003, 0.015),
    "claude-haiku-4-5-20251001": (0.0008, 0.004),
    "claude-3-opus-20240229": (0.015, 0.075),
    "claude-3-sonnet-20240229": (0.003, 0.015),
    "claude-3-haiku-20240307": (0.00025, 0.00125),
    "claude-3.5-sonnet-20241022": (0.003, 0.015),
    # Google
    "gemini-2.0-flash": (0.0001, 0.0004),
    "gemini-1.5-pro": (0.00125, 0.005),
    "gemini-1.5-flash": (0.000075, 0.0003),
    # DeepSeek
    "deepseek-chat": (0.00014, 0.00028),
    "deepseek-coder": (0.00014, 0.00028),
    "deepseek-r1": (0.00055, 0.00219),
    # Local (free)
    "llama3:8b": (0.0, 0.0),
    "llama3:70b": (0.0, 0.0),
    "llama3.1:8b": (0.0, 0.0),
    "mistral:7b": (0.0, 0.0),
    "codellama:7b": (0.0, 0.0),
    "qwen2.5-coder:7b": (0.0, 0.0),
}

_DEFAULT_PRICING = PRICING["gpt-4o-mini"]


def normalize_model_name(model: str) -> str:
    """Normalize OpenRouter-style 'provider/model' names to base model name.

    Examples:
        'openai/gpt-4o-mini' -> 'gpt-4o-mini'
        'anthropic/claude-sonnet-4-20250514' -> 'claude-sonnet-4-20250514'
        'gpt-4o' -> 'gpt-4o'
    """
    if "/" in model:
        return model.split("/", 1)[1]
    return model


@dataclass
class CostRecord:
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    agent_type: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class CostTracker:
    def __init__(self, max_cost_per_task: float = 1.0) -> None:
        self.records: list[CostRecord] = []
        self.total_cost: float = 0.0
        self.max_cost_per_task = max_cost_per_task

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        normalized = normalize_model_name(model)
        pricing = PRICING.get(normalized)
        if pricing is None:
            # Try partial match (e.g., 'gpt-4o-mini-2024-07-18' -> 'gpt-4o-mini')
            for known_model, known_pricing in PRICING.items():
                if normalized.startswith(known_model) or known_model.startswith(normalized):
                    pricing = known_pricing
                    break
        if pricing is None:
            logger.warning("Unknown model '%s' (normalized: '%s'), using gpt-4o-mini pricing", model, normalized)
            pricing = _DEFAULT_PRICING

        input_cost = (input_tokens / 1000) * pricing[0]
        output_cost = (output_tokens / 1000) * pricing[1]
        return input_cost + output_cost

    def record(self, llm_response: object, agent_type: str = "") -> CostRecord:
        model = getattr(llm_response, "model", "unknown")
        input_tokens = getattr(llm_response, "input_tokens", 0)
        output_tokens = getattr(llm_response, "output_tokens", 0)

        cost = self.calculate_cost(model, input_tokens, output_tokens)
        rec = CostRecord(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            agent_type=agent_type,
        )
        self.records.append(rec)
        self.total_cost += cost
        return rec

    def check_budget(self) -> bool:
        """Return True if within budget, False if exceeded."""
        if self.total_cost >= self.max_cost_per_task:
            logger.warning(
                "Budget exceeded: $%.4f >= $%.4f limit",
                self.total_cost, self.max_cost_per_task,
            )
            return False
        return True

    def get_summary(self) -> dict:
        cost_by_model: dict[str, float] = {}
        cost_by_agent: dict[str, float] = {}
        tokens_by_model: dict[str, int] = {}
        total_tokens = 0

        for rec in self.records:
            normalized = normalize_model_name(rec.model)
            cost_by_model[normalized] = cost_by_model.get(normalized, 0.0) + rec.cost_usd
            tokens_by_model[normalized] = (
                tokens_by_model.get(normalized, 0) + rec.input_tokens + rec.output_tokens
            )
            total_tokens += rec.input_tokens + rec.output_tokens
            if rec.agent_type:
                cost_by_agent[rec.agent_type] = cost_by_agent.get(rec.agent_type, 0.0) + rec.cost_usd

        # Estimate savings vs always using gpt-4o
        gpt4o_in, gpt4o_out = PRICING["gpt-4o"]
        hypothetical_cost = sum(
            (rec.input_tokens / 1000) * gpt4o_in + (rec.output_tokens / 1000) * gpt4o_out
            for rec in self.records
        )
        estimated_savings = hypothetical_cost - self.total_cost

        return {
            "total_cost": self.total_cost,
            "total_tokens": total_tokens,
            "records_count": len(self.records),
            "cost_by_model": cost_by_model,
            "cost_by_agent": cost_by_agent,
            "tokens_by_model": tokens_by_model,
            "estimated_savings": max(0.0, estimated_savings),
            "budget_remaining": max(0.0, self.max_cost_per_task - self.total_cost),
        }

    def reset(self) -> None:
        self.records = []
        self.total_cost = 0.0
