"""init_all_tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from __future__ import annotations

import uuid
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("complexity", sa.String(10), nullable=True),
        sa.Column("model_used", sa.String(50), nullable=True),
        sa.Column("plan", sa.JSON(), nullable=True),
        sa.Column("final_code", sa.Text(), nullable=True),
        sa.Column("final_output", sa.Text(), nullable=True),
        sa.Column("total_cost_usd", sa.Numeric(10, 6), default=0),
        sa.Column("total_time_ms", sa.Integer(), nullable=True),
        sa.Column("retry_count", sa.Integer(), default=0),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_tasks_status", "tasks", ["status"])

    op.create_table(
        "agent_traces",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "task_id",
            sa.UUID(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agent_type", sa.String(20), nullable=False),
        sa.Column("input_data", sa.JSON(), nullable=False),
        sa.Column("output_data", sa.JSON(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), default=0),
        sa.Column("cost_usd", sa.Numeric(10, 6), default=0),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("step_order", sa.Integer(), nullable=False),
    )
    op.create_index("ix_agent_traces_task_id", "agent_traces", ["task_id"])

    op.create_table(
        "execution_results",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "trace_id",
            sa.UUID(),
            sa.ForeignKey("agent_traces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("exit_code", sa.Integer(), nullable=False),
        sa.Column("stdout", sa.Text(), default=""),
        sa.Column("stderr", sa.Text(), default=""),
        sa.Column("execution_time_ms", sa.Integer(), nullable=False),
        sa.Column("memory_used_mb", sa.Float(), nullable=True),
        sa.Column("container_id", sa.String(64), nullable=True),
        sa.Column("retry_number", sa.Integer(), default=0),
    )
    op.create_index("ix_execution_results_trace_id", "execution_results", ["trace_id"])

    op.create_table(
        "benchmark_runs",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("benchmark_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("model_config_json", sa.JSON()),
        sa.Column("total_problems", sa.Integer()),
        sa.Column("passed", sa.Integer()),
        sa.Column("pass_at_1", sa.Float()),
        sa.Column("pass_at_1_repair", sa.Float(), nullable=True),
        sa.Column("avg_retries", sa.Float(), nullable=True),
        sa.Column("total_cost_usd", sa.Numeric(10, 6), default=0),
        sa.Column("total_time_ms", sa.Integer(), nullable=True),
    )

    op.create_table(
        "benchmark_results",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "run_id",
            sa.UUID(),
            sa.ForeignKey("benchmark_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("problem_id", sa.String(50), nullable=False),
        sa.Column("passed", sa.Boolean(), default=False),
        sa.Column("passed_after_repair", sa.Boolean(), default=False),
        sa.Column("retries_used", sa.Integer(), default=0),
        sa.Column("generated_code", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), default=0),
        sa.Column("time_ms", sa.Integer(), nullable=True),
    )
    op.create_index("ix_benchmark_results_run_id", "benchmark_results", ["run_id"])

    op.create_table(
        "app_settings",
        sa.Column("id", sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("key", sa.String(100), unique=True, nullable=False),
        sa.Column("value", sa.JSON()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_table("benchmark_results")
    op.drop_table("benchmark_runs")
    op.drop_table("execution_results")
    op.drop_table("agent_traces")
    op.drop_table("tasks")
