from __future__ import annotations

from datetime import datetime
from typing import Generic, Literal, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 20

    @field_validator("page")
    @classmethod
    def page_ge_1(cls, v: int) -> int:
        if v < 1:
            raise ValueError("page must be >= 1")
        return v

    @field_validator("per_page")
    @classmethod
    def per_page_range(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("per_page must be between 1 and 100")
        return v


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int


# ─── Task schemas ───────────────────────────────────────────────────────────


class TaskCreate(BaseSchema):
    prompt: str
    context_code: Optional[str] = None  # Previous task's code for multi-turn refinement
    research_enabled: bool = True  # Enable research-driven pipeline

    @field_validator("prompt")
    @classmethod
    def prompt_not_empty(cls, v: str) -> str:
        if len(v) < 1:
            raise ValueError("prompt must not be empty")
        if len(v) > 10000:
            raise ValueError("prompt must be at most 10000 characters")
        return v


class TaskResponse(BaseSchema):
    id: UUID
    prompt: str
    status: str
    complexity: Optional[str] = None
    model_used: Optional[str] = None
    total_cost_usd: float = 0.0
    total_time_ms: Optional[int] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AgentTraceResponse(BaseSchema):
    id: UUID
    task_id: UUID
    agent_type: str
    input_data: dict
    output_data: Optional[dict] = None
    reasoning: Optional[str] = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    duration_ms: Optional[int] = None
    step_order: int
    created_at: datetime


class TaskDetail(TaskResponse):
    plan: Optional[dict] = None
    final_code: Optional[str] = None
    final_output: Optional[str] = None
    traces: list[AgentTraceResponse] = []
    research_findings: Optional[dict] = None
    questions: Optional[list] = None


TaskListResponse = PaginatedResponse[TaskResponse]


# ─── Execution schemas ───────────────────────────────────────────────────────


class ExecutionResultResponse(BaseSchema):
    id: UUID
    trace_id: UUID
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: int
    memory_used_mb: Optional[float] = None
    container_id: Optional[str] = None
    retry_number: int = 0
    created_at: datetime


# ─── Benchmark schemas ───────────────────────────────────────────────────────


class BenchmarkRunRequest(BaseSchema):
    type: Literal["humaneval", "mbpp", "custom"]
    with_repair: bool = True


class BenchmarkRunResponse(BaseSchema):
    id: UUID
    benchmark_type: str
    total_problems: int
    passed: int
    pass_at_1: float
    pass_at_1_repair: Optional[float] = None
    avg_retries: Optional[float] = None
    total_cost_usd: float = 0.0
    total_time_ms: Optional[int] = None
    created_at: datetime


class BenchmarkResultResponse(BaseSchema):
    id: UUID
    run_id: UUID
    problem_id: str
    passed: bool
    passed_after_repair: bool
    retries_used: int
    generated_code: Optional[str] = None
    error_message: Optional[str] = None
    cost_usd: float = 0.0
    time_ms: Optional[int] = None


class BenchmarkRunDetail(BenchmarkRunResponse):
    results: list[BenchmarkResultResponse] = []


# ─── Settings schemas ─────────────────────────────────────────────────────────


class LLMProviderSettings(BaseModel):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_endpoint: str = "http://localhost:11434"


class RoutingSettings(BaseModel):
    simple_threshold: float = 0.3
    complex_threshold: float = 0.7
    simple_model: str = "llama3:8b"
    complex_model: str = "gpt-4"

    @field_validator("simple_threshold", "complex_threshold")
    @classmethod
    def threshold_range(cls, v: float) -> float:
        if v < 0 or v > 1:
            raise ValueError("threshold must be between 0 and 1")
        return v


class SandboxSettingsSchema(BaseModel):
    timeout_seconds: int = 30
    memory_limit_mb: int = 512
    max_retries: int = 3

    @field_validator("timeout_seconds")
    @classmethod
    def timeout_range(cls, v: int) -> int:
        if v < 5 or v > 120:
            raise ValueError("timeout_seconds must be between 5 and 120")
        return v

    @field_validator("memory_limit_mb")
    @classmethod
    def memory_range(cls, v: int) -> int:
        if v < 128 or v > 2048:
            raise ValueError("memory_limit_mb must be between 128 and 2048")
        return v

    @field_validator("max_retries")
    @classmethod
    def retries_range(cls, v: int) -> int:
        if v < 0 or v > 10:
            raise ValueError("max_retries must be between 0 and 10")
        return v


class AppSettingsResponse(BaseModel):
    llm: LLMProviderSettings
    routing: RoutingSettings
    sandbox: SandboxSettingsSchema


class AppSettingsUpdate(BaseModel):
    llm: Optional[LLMProviderSettings] = None
    routing: Optional[RoutingSettings] = None
    sandbox: Optional[SandboxSettingsSchema] = None


class ConnectionTestRequest(BaseModel):
    provider: Literal["openai", "anthropic", "ollama", "openrouter"]
    api_key: Optional[str] = None
    endpoint: Optional[str] = None


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    latency_ms: Optional[int] = None


# ─── WebSocket event schemas ──────────────────────────────────────────────────


class WSEvent(BaseModel):
    event: str
    timestamp: datetime
    data: dict


class WSAgentStarted(BaseModel):
    agent_type: str
    step_order: int
    input_summary: str


class WSAgentThinking(BaseModel):
    agent_type: str
    chunk: str


class WSAgentCompleted(BaseModel):
    agent_type: str
    output_summary: str
    tokens_used: int
    cost_usd: float
    duration_ms: int


class WSCodeGenerated(BaseModel):
    code: str
    language: str
    subtask_index: int


class WSExecutionStarted(BaseModel):
    container_id: Optional[str] = None
    retry_number: int


class WSExecutionOutput(BaseModel):
    stream: Literal["stdout", "stderr"]
    line: str


class WSExecutionCompleted(BaseModel):
    exit_code: int
    execution_time_ms: int
    memory_used_mb: Optional[float] = None


class WSRepairStarted(BaseModel):
    retry_number: int
    error_summary: str


class WSRepairFixApplied(BaseModel):
    fixed_code: str
    change_summary: str


class WSTaskCompleted(BaseModel):
    final_code: str
    final_output: str
    total_cost: float
    total_time_ms: int
    retry_count: int


class WSTaskFailed(BaseModel):
    error_message: str
    retry_count: int


# ─── History filter schemas ───────────────────────────────────────────────────


class HistoryFilter(BaseModel):
    status: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = "created_at"
    order: Literal["asc", "desc"] = "desc"


# ─── Analytics schemas ────────────────────────────────────────────────────────


class DailyCost(BaseModel):
    date: str
    cost: float


class CostSummary(BaseModel):
    total_cost_usd: float
    cost_by_model: dict
    cost_by_agent: dict
    daily_costs: list[DailyCost]


class PerformanceSummary(BaseModel):
    total_tasks: int
    success_rate: float
    avg_time_ms: float
    avg_retries: float
    tasks_by_status: dict


class ModelEntry(BaseModel):
    model: str
    count: int
    percentage: float


class ModelDistribution(BaseModel):
    distribution: list[ModelEntry]


class ErrorPattern(BaseModel):
    error_type: str
    count: int
    repair_success_rate: float


class ComplexityBreakdown(BaseModel):
    complexity: str
    total: int
    succeeded: int
    repaired: int
    failed: int
    avg_retries: float
    avg_cost_usd: float


class SelfRepairSummary(BaseModel):
    total_tasks: int
    tasks_with_retries: int
    repair_success_rate: float
    first_try_success_rate: float
    avg_retries_when_repairing: float
    max_retries_seen: int
    total_repair_cost_usd: float
    complexity_breakdown: list[ComplexityBreakdown]
    error_patterns: list[ErrorPattern]
    daily_repair_rate: list[DailyCost]
