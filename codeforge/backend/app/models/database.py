from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Task(Base):
    __tablename__ = "tasks"

    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    complexity: Mapped[Optional[str]] = mapped_column(String(10))
    model_used: Mapped[Optional[str]] = mapped_column(String(50))
    plan: Mapped[Optional[dict]] = mapped_column(JSON)
    final_code: Mapped[Optional[str]] = mapped_column(Text)
    final_output: Mapped[Optional[str]] = mapped_column(Text)
    total_cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0)
    total_time_ms: Mapped[Optional[int]]
    retry_count: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    traces: Mapped[list["AgentTrace"]] = relationship(
        "AgentTrace",
        back_populates="task",
        cascade="all, delete-orphan",
    )


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    agent_type: Mapped[str] = mapped_column(String(20), nullable=False)
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON)
    reasoning: Mapped[Optional[str]] = mapped_column(Text)
    tokens_used: Mapped[int] = mapped_column(default=0)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0)
    duration_ms: Mapped[Optional[int]]
    step_order: Mapped[int] = mapped_column(nullable=False)

    task: Mapped["Task"] = relationship("Task", back_populates="traces")
    execution_results: Mapped[list["ExecutionResult"]] = relationship(
        "ExecutionResult",
        back_populates="trace",
        cascade="all, delete-orphan",
    )


class ExecutionResult(Base):
    __tablename__ = "execution_results"

    trace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_traces.id", ondelete="CASCADE"), index=True
    )
    exit_code: Mapped[int] = mapped_column(nullable=False)
    stdout: Mapped[str] = mapped_column(Text, default="")
    stderr: Mapped[str] = mapped_column(Text, default="")
    execution_time_ms: Mapped[int] = mapped_column(nullable=False)
    memory_used_mb: Mapped[Optional[float]]
    container_id: Mapped[Optional[str]] = mapped_column(String(64))
    retry_number: Mapped[int] = mapped_column(default=0)

    trace: Mapped["AgentTrace"] = relationship(
        "AgentTrace", back_populates="execution_results"
    )


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    benchmark_type: Mapped[str] = mapped_column(String(20), nullable=False)
    model_config_json: Mapped[dict] = mapped_column(JSON)
    total_problems: Mapped[int]
    passed: Mapped[int]
    pass_at_1: Mapped[float]
    pass_at_1_repair: Mapped[Optional[float]]
    avg_retries: Mapped[Optional[float]]
    total_cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0)
    total_time_ms: Mapped[Optional[int]]

    results: Mapped[list["BenchmarkResult"]] = relationship(
        "BenchmarkResult",
        back_populates="run",
        cascade="all, delete-orphan",
    )


class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"

    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("benchmark_runs.id", ondelete="CASCADE"), index=True
    )
    problem_id: Mapped[str] = mapped_column(String(50), nullable=False)
    passed: Mapped[bool] = mapped_column(default=False)
    passed_after_repair: Mapped[bool] = mapped_column(default=False)
    retries_used: Mapped[int] = mapped_column(default=0)
    generated_code: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0)
    time_ms: Mapped[Optional[int]]

    run: Mapped["BenchmarkRun"] = relationship("BenchmarkRun", back_populates="results")


class AppSettings(Base):
    __tablename__ = "app_settings"

    # Override the inherited UUID primary key with a string key
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid4)  # type: ignore[assignment]
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
