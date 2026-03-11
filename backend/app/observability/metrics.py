from __future__ import annotations

from typing import Optional

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider

# Initialize a default meter provider so metrics are always available
metrics.set_meter_provider(MeterProvider())

_meter = metrics.get_meter("codeforge")

task_counter = _meter.create_counter(
    "codeforge.tasks",
    description="Number of tasks by status",
)

task_duration = _meter.create_histogram(
    "codeforge.task_duration_ms",
    description="Total task duration in milliseconds",
    unit="ms",
)

agent_duration = _meter.create_histogram(
    "codeforge.agent_duration_ms",
    description="Per-agent execution duration in milliseconds",
    unit="ms",
)

llm_tokens = _meter.create_counter(
    "codeforge.llm_tokens",
    description="Token usage by model",
)

llm_cost = _meter.create_counter(
    "codeforge.llm_cost_usd",
    description="LLM cost in USD (scaled x10000 to avoid float issues)",
)

repair_counter = _meter.create_counter(
    "codeforge.repairs",
    description="Number of repair attempts",
)

sandbox_execution_time = _meter.create_histogram(
    "codeforge.sandbox_execution_ms",
    description="Sandbox execution time in milliseconds",
    unit="ms",
)


def record_task_completion(
    status: str,
    duration_ms: int,
    model: str,
    cost: float,
    retries: int,
) -> None:
    task_counter.add(1, {"status": status, "model": model})
    task_duration.record(duration_ms, {"status": status, "model": model})
    if retries > 0:
        repair_counter.add(retries, {"model": model})


def record_agent_execution(
    agent_type: str,
    duration_ms: int,
    tokens: int,
    cost: float,
) -> None:
    agent_duration.record(duration_ms, {"agent_type": agent_type})
    llm_tokens.add(tokens, {"agent_type": agent_type})


def record_sandbox_execution(
    duration_ms: int,
    exit_code: int,
    memory_mb: Optional[float] = None,
) -> None:
    sandbox_execution_time.record(
        duration_ms, {"exit_code": str(exit_code)}
    )
