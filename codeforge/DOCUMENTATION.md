# CodeForge - AI Code Agent with Self-Repair

## Complete Project Documentation

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Tech Stack](#3-tech-stack)
4. [How It Works — The Multi-Agent Pipeline](#4-how-it-works--the-multi-agent-pipeline)
5. [Backend — FastAPI](#5-backend--fastapi)
   - [5.1 Application Entry Point](#51-application-entry-point)
   - [5.2 Configuration System](#52-configuration-system)
   - [5.3 Database Layer](#53-database-layer)
   - [5.4 Dependency Injection](#54-dependency-injection)
   - [5.5 API Routes (21 Endpoints)](#55-api-routes-21-endpoints)
   - [5.6 Services Layer](#56-services-layer)
6. [LLM Layer — Providers, Classification & Routing](#6-llm-layer--providers-classification--routing)
   - [6.1 LLM Providers](#61-llm-providers)
   - [6.2 Task Complexity Classifier](#62-task-complexity-classifier)
   - [6.3 Model Router](#63-model-router)
   - [6.4 Cost Tracker](#64-cost-tracker)
7. [Agent System — The Core Intelligence](#7-agent-system--the-core-intelligence)
   - [7.1 Base Agent (Template Method Pattern)](#71-base-agent-template-method-pattern)
   - [7.2 Planner Agent](#72-planner-agent)
   - [7.3 Coder Agent](#73-coder-agent)
   - [7.4 Reviewer Agent](#74-reviewer-agent)
   - [7.5 Orchestrator — LangGraph State Machine](#75-orchestrator--langgraph-state-machine)
8. [Sandbox Execution — Docker Isolation](#8-sandbox-execution--docker-isolation)
9. [Real-Time Communication — WebSocket](#9-real-time-communication--websocket)
10. [Observability — Logging, Tracing & Metrics](#10-observability--logging-tracing--metrics)
11. [Frontend — Next.js 16](#11-frontend--nextjs-16)
    - [11.1 Pages](#111-pages)
    - [11.2 Components](#112-components)
    - [11.3 Custom Hooks](#113-custom-hooks)
    - [11.4 API Client & WebSocket Client](#114-api-client--websocket-client)
    - [11.5 TypeScript Types](#115-typescript-types)
12. [Testing](#12-testing)
    - [12.1 Unit Tests](#121-unit-tests)
    - [12.2 Integration Tests](#122-integration-tests)
    - [12.3 End-to-End Tests](#123-end-to-end-tests)
13. [Project Structure](#13-project-structure)
14. [Environment Variables](#14-environment-variables)
15. [Running the Project](#15-running-the-project)
16. [Known Limitations](#16-known-limitations)

---

## 1. Project Overview

**CodeForge** is a full-stack AI-powered code generation system with **self-repair capabilities**. Given a natural language description of a coding task, CodeForge:

1. **Plans** — Decomposes the task into ordered subtasks with a dependency graph
2. **Codes** — Generates Python code for each subtask using LLMs
3. **Executes** — Runs the generated code inside an isolated Docker sandbox
4. **Self-Repairs** — If execution fails, automatically analyzes the error, generates a fix, and retries (up to N times)

### The Problem It Solves

Traditional AI code generation (e.g., ChatGPT) generates code but never validates it. The user must manually copy, run, debug, and fix errors. CodeForge closes this loop automatically:

```
User Prompt → Plan → Generate Code → Execute → [If Error → Analyze → Fix → Re-Execute] → Working Code
```

This **self-repair loop** is what makes CodeForge unique. It doesn't just generate code — it ensures the code actually works.

### Key Features

- **Multi-Agent Architecture** — Specialized agents (Planner, Coder, Reviewer) collaborate through a LangGraph state machine
- **Intelligent Model Routing** — Routes simple tasks to cheap/fast models and complex tasks to powerful models, minimizing cost
- **Docker Sandboxing** — All generated code runs in isolated containers with memory/CPU/network limits
- **Real-Time Streaming** — WebSocket-based live updates as agents think, generate code, and execute
- **Cost Tracking** — Tracks every LLM call's token usage and cost, with savings calculations vs. always using GPT-4
- **Benchmarking** — Built-in HumanEval/MBPP benchmark support to measure pass@1 rates
- **Full Observability** — OpenTelemetry tracing, structured logging, and analytics dashboards

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 16)                     │
│  ┌──────┐ ┌─────────┐ ┌────────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Chat │ │ History │ │ Benchmarks │ │ Settings │ │Analytics │ │
│  └──┬───┘ └────┬────┘ └─────┬──────┘ └────┬─────┘ └────┬─────┘ │
│     │          │            │              │            │        │
│     └──────────┴────────────┴──────────────┴────────────┘        │
│                          │ HTTP/WS                                │
└──────────────────────────┼───────────────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────────────┐
│                    BACKEND (FastAPI)                              │
│                          │                                       │
│  ┌───────────────────────┴────────────────────────────┐          │
│  │              API Layer (21 Routes)                  │          │
│  │  /tasks  /history  /benchmarks  /settings  /ws     │          │
│  └───────────────────────┬────────────────────────────┘          │
│                          │                                       │
│  ┌───────────────────────┴────────────────────────────┐          │
│  │           Orchestrator (LangGraph)                  │          │
│  │                                                     │          │
│  │   classify → plan → code → execute ─┐               │          │
│  │                                     │               │          │
│  │                          success → finalize → END   │          │
│  │                          failure → review ──┐       │          │
│  │                                    retry → apply_fix │         │
│  │                                    abort → fail→END │          │
│  └──────┬──────────┬──────────┬───────────────────────┘          │
│         │          │          │                                   │
│  ┌──────┴───┐ ┌────┴────┐ ┌──┴───────┐                          │
│  │ Planner  │ │  Coder  │ │ Reviewer │    ← Specialized Agents   │
│  │  Agent   │ │  Agent  │ │  Agent   │                           │
│  └──────┬───┘ └────┬────┘ └──┬───────┘                          │
│         └──────────┼─────────┘                                   │
│                    │                                             │
│  ┌─────────────────┴──────────────────────┐                      │
│  │          LLM Layer                      │                     │
│  │  Router → Classifier → Provider         │                     │
│  │  ┌────────┐ ┌──────────┐ ┌────────┐    │                     │
│  │  │OpenAI  │ │Anthropic │ │Ollama  │    │                     │
│  │  │OpenRouter│           │         │    │                     │
│  │  └────────┘ └──────────┘ └────────┘    │                     │
│  └────────────────────────────────────────┘                      │
│                                                                  │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐        │
│  │   SQLite /   │  │   Docker    │  │  OpenTelemetry   │        │
│  │  PostgreSQL  │  │   Sandbox   │  │  Tracing + Logs  │        │
│  └──────────────┘  └─────────────┘  └──────────────────┘        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Tech Stack

### Backend

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12+ | Runtime |
| FastAPI | 0.104+ | REST API framework |
| SQLAlchemy | 2.0+ | ORM (async) |
| Alembic | 1.13+ | Database migrations |
| LangChain | 0.1+ | LLM integration framework |
| LangGraph | 0.0.40+ | Agent state machine orchestration |
| Docker SDK | 7.0+ | Sandbox container management |
| Redis | 5.0+ | Caching (optional) |
| OpenTelemetry | 1.22+ | Distributed tracing |
| Pydantic | 2.5+ | Data validation & settings |
| uvicorn | 0.24+ | ASGI server |
| aiosqlite | 0.19+ | SQLite async driver |
| asyncpg | 0.29+ | PostgreSQL async driver |
| httpx | 0.25+ | Async HTTP client |

### Frontend

| Technology | Version | Purpose |
|-----------|---------|---------|
| Next.js | 16.1.6 | React framework (App Router) |
| React | 19.2.3 | UI library |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 4.x | Utility-first styling |
| shadcn/ui | new-york | Component library (Radix UI primitives) |
| Recharts | 3.7.0 | Charts (bar, line, pie) |
| ReactFlow | 11.11.4 | Agent flow diagram visualization |
| Monaco Editor | 4.7.0 | Code display with syntax highlighting |
| sonner | 2.0.7 | Toast notifications |
| next-themes | 0.4.6 | Dark/light theme support |
| lucide-react | 0.577.0 | Icon library |

---

## 4. How It Works — The Multi-Agent Pipeline

### What "Multi-Agent" Means

CodeForge uses three **specialized AI agents**, each with a distinct role and custom prompt. They are not three separate models — they are three different *roles* that use an LLM (potentially the same model) with different system prompts and validation logic.

### The Pipeline (Step by Step)

#### Step 1: Task Classification
When a user submits a prompt like *"Write a Python function for binary search with tests"*:
- The **Heuristic Classifier** scores the task's complexity using keyword matching, length analysis, and requirement counting
- Classification result: `SIMPLE`, `MEDIUM`, or `HARD`
- The **Model Router** selects the optimal LLM model based on complexity:
  - SIMPLE → cheap/fast model (e.g., Ollama llama3, gpt-4o-mini)
  - HARD → powerful model (e.g., GPT-4, Claude Sonnet)

#### Step 2: Planning (Planner Agent)
The Planner Agent receives the user's prompt and:
- Decomposes it into 2-6 ordered **subtasks**
- Defines **dependencies** between subtasks (a DAG — Directed Acyclic Graph)
- Estimates each subtask's complexity
- The final subtask is always an **integration step** that combines everything into a runnable script
- Validates the plan: checks for missing keys, circular dependencies, valid IDs

**Example Plan:**
```json
{
  "subtasks": [
    {"id": 1, "description": "Write binary_search(arr, target) function", "dependencies": [], "estimated_complexity": "simple"},
    {"id": 2, "description": "Write unit tests for binary_search", "dependencies": [1], "estimated_complexity": "simple"},
    {"id": 3, "description": "Integrate into runnable script with main()", "dependencies": [1, 2], "estimated_complexity": "simple"}
  ],
  "reasoning": "Binary search is a single algorithm. Tests verify correctness. Integration combines both."
}
```

#### Step 3: Code Generation (Coder Agent)
For each subtask (in dependency order):
- The Coder Agent generates Python code with type hints, docstrings, and edge case handling
- Each subtask receives context: the plan, prior code from completed subtasks, and dependency info
- Generated code is **syntax-validated** via `compile()` — if invalid, the agent retries once
- The final integration subtask produces a complete runnable script with `main()` and `if __name__ == "__main__"`

#### Step 4: Sandbox Execution
The integrated code is executed inside a **Docker container**:
- Isolated environment with memory/CPU limits
- Network disabled by default (security)
- Configurable timeout (default: 30 seconds)
- Captures stdout, stderr, exit code, execution time, and memory usage

#### Step 5: Self-Repair Loop (If Execution Fails)
If the code fails (non-zero exit code, runtime error, timeout):

1. **Reviewer Agent** analyzes the failure:
   - Identifies root cause from the traceback
   - Classifies error type (syntax, runtime, logic, import, timeout, memory)
   - Generates a **minimal fix** (fewest line changes)
   - Provides the complete fixed code
   - Rates confidence (0.0 to 1.0)

2. **Apply Fix** — The fixed code replaces the broken code (with exponential backoff)

3. **Re-Execute** — The fixed code runs in the sandbox again

4. **Loop or Exit:**
   - If execution succeeds → task completes
   - If max retries reached → task fails
   - If reviewer confidence < 0.3 on retry 2+ → task aborts early

```
execute ──→ success? ──yes──→ COMPLETED
              │
              no
              │
          review ──→ can retry? ──no──→ FAILED
              │
              yes
              │
          apply_fix ──→ execute (loop back)
```

---

## 5. Backend — FastAPI

### 5.1 Application Entry Point

**File:** `backend/app/main.py`

The `create_app()` factory function builds the FastAPI application:

**Startup (Lifespan):**
1. Structured logging setup (configurable level and format)
2. OpenTelemetry tracing initialization (OTLP exporter)
3. Redis connection (optional, graceful failure)

**Shutdown:**
1. Redis disconnection

**Middleware:**
- **CORS** — Allows `http://localhost:3000` (configurable), credentials, all methods/headers
- **Correlation ID** — Adds request tracking IDs for observability

**Exception Handlers:**
- `404` → `{"detail": "Not found"}`
- `422` → `{"detail": "<validation error>"}`
- `500` → `{"detail": "Internal server error"}` (logged)

**Root Endpoint:**
- `GET /` → `{"name": "CodeForge", "version": "0.1.0", "status": "running"}`

---

### 5.2 Configuration System

**File:** `backend/app/config.py`

All configuration is managed through **Pydantic Settings** with environment variable and `.env` file support.

**Main Settings Class Fields:**

| Category | Setting | Type | Default | Description |
|----------|---------|------|---------|-------------|
| Database | `database_url` | str | `postgresql+asyncpg://...` | Async DB connection string |
| Database | `database_sync_url` | str | `postgresql://...` | Sync DB connection string |
| Redis | `redis_url` | str | `redis://localhost:6379/0` | Redis connection |
| LLM | `openai_api_key` | str? | None | OpenAI API key |
| LLM | `anthropic_api_key` | str? | None | Anthropic API key |
| LLM | `openrouter_api_key` | str? | None | OpenRouter API key |
| LLM | `ollama_base_url` | str | `http://localhost:11434` | Ollama server URL |
| LLM | `default_simple_model` | str | `llama3:8b` | Model for simple tasks |
| LLM | `default_complex_model` | str | `gpt-4` | Model for complex tasks |
| LLM | `complexity_simple_threshold` | float | 0.3 | Score threshold for SIMPLE |
| LLM | `complexity_complex_threshold` | float | 0.7 | Score threshold for HARD |
| Sandbox | `sandbox_image` | str | `codeforge-sandbox-python:latest` | Docker image name |
| Sandbox | `sandbox_timeout_seconds` | int | 30 | Execution timeout |
| Sandbox | `sandbox_memory_limit_mb` | int | 512 | Container memory limit |
| Sandbox | `sandbox_cpu_limit` | float | 1.0 | Container CPU limit |
| Sandbox | `sandbox_network_disabled` | bool | True | Disable container networking |
| Sandbox | `max_repair_retries` | int | 2 | Max self-repair attempts |
| Sandbox | `docker_host` | str | `unix:///var/run/docker.sock` | Docker socket path |
| Observability | `otel_exporter_otlp_endpoint` | str | `http://localhost:4317` | OTLP endpoint |
| Observability | `otel_service_name` | str | `codeforge-backend` | Service name for traces |
| Observability | `log_level` | str | `INFO` | Logging level |
| Observability | `log_format` | str | `json` | Log format (json/text) |
| Server | `host` | str | `0.0.0.0` | Bind host |
| Server | `port` | int | 8000 | Bind port |
| Server | `cors_origins` | str | `http://localhost:3000` | Comma-separated CORS origins |
| Server | `secret_key` | str | `change-me-in-production` | App secret key |

Settings are loaded once via `@lru_cache` singleton pattern.

---

### 5.3 Database Layer

#### Session Management

**File:** `backend/app/db/session.py`

- Creates an `AsyncEngine` using the configured `database_url`
- For SQLite: no connection pooling (not needed)
- For PostgreSQL: `pool_size=10`, `max_overflow=20`, `pool_recycle=3600`
- `async_session_factory` creates `AsyncSession` instances with `expire_on_commit=False`

#### Database Models (6 Tables)

**File:** `backend/app/models/database.py`

##### Table: `tasks`

The main task table storing user prompts and execution results.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, default uuid4 | Unique task ID |
| `prompt` | Text | NOT NULL | User's natural language prompt |
| `status` | String(20) | NOT NULL, default "pending", indexed | Current status |
| `complexity` | String(10) | nullable | Classified complexity (simple/medium/hard) |
| `model_used` | String(50) | nullable | LLM model that was used |
| `plan` | JSON | nullable | Decomposed subtask plan |
| `final_code` | Text | nullable | Final integrated Python code |
| `final_output` | Text | nullable | Execution stdout output |
| `total_cost_usd` | Numeric(10,6) | default 0 | Total LLM cost |
| `total_time_ms` | Integer | nullable | Total execution time |
| `retry_count` | Integer | default 0 | Number of repair retries used |
| `error_message` | Text | nullable | Error message if failed |
| `created_at` | DateTime(tz) | server default now() | Creation timestamp |
| `updated_at` | DateTime(tz) | auto-updates on change | Last update timestamp |

**Relationships:** `traces` → List of AgentTrace (cascade delete)

**Possible Statuses:** `pending`, `classifying`, `planning`, `coding`, `executing`, `reviewing`, `repairing`, `completed`, `failed`

##### Table: `agent_traces`

Records each agent's execution within a task.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Trace ID |
| `task_id` | UUID | FK→tasks.id, CASCADE, indexed | Parent task |
| `agent_type` | String(20) | NOT NULL | planner/coder/reviewer |
| `input_data` | JSON | NOT NULL | Input given to agent |
| `output_data` | JSON | nullable | Agent's output |
| `reasoning` | Text | nullable | Agent's reasoning |
| `tokens_used` | Integer | default 0 | Tokens consumed |
| `cost_usd` | Numeric(10,6) | default 0 | LLM cost for this step |
| `duration_ms` | Integer | nullable | Execution duration |
| `step_order` | Integer | NOT NULL | Order within task |
| `created_at` | DateTime(tz) | server default now() | Timestamp |

**Relationships:** `task` → Task, `execution_results` → List of ExecutionResult

##### Table: `execution_results`

Records sandbox execution outputs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Result ID |
| `trace_id` | UUID | FK→agent_traces.id, CASCADE | Parent trace |
| `exit_code` | Integer | NOT NULL | Process exit code |
| `stdout` | Text | default "" | Standard output |
| `stderr` | Text | default "" | Standard error |
| `execution_time_ms` | Integer | NOT NULL | Time in milliseconds |
| `memory_used_mb` | Float | nullable | Memory consumption |
| `container_id` | String(64) | nullable | Docker container ID |
| `retry_number` | Integer | default 0 | Which retry attempt |
| `created_at` | DateTime(tz) | server default now() | Timestamp |

##### Table: `benchmark_runs`

Stores benchmark execution metadata.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Run ID |
| `benchmark_type` | String(20) | humaneval/mbpp/custom |
| `model_config_json` | JSON | Model configuration used |
| `total_problems` | Integer | Number of problems |
| `passed` | Integer | Problems passed |
| `pass_at_1` | Float | Pass@1 rate (0.0 - 1.0) |
| `pass_at_1_repair` | Float | Pass@1 with self-repair |
| `avg_retries` | Float | Average retries per problem |
| `total_cost_usd` | Numeric(10,6) | Total cost |
| `total_time_ms` | Integer | Total time |
| `created_at` | DateTime(tz) | Timestamp |

**Relationships:** `results` → List of BenchmarkResult

##### Table: `benchmark_results`

Individual benchmark problem results.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Result ID |
| `run_id` | UUID | FK→benchmark_runs.id |
| `problem_id` | String(50) | Problem identifier |
| `passed` | Boolean | Passed on first attempt |
| `passed_after_repair` | Boolean | Passed after self-repair |
| `retries_used` | Integer | Number of retries |
| `generated_code` | Text | Generated solution |
| `error_message` | Text | Error if failed |
| `cost_usd` | Numeric(10,6) | Cost for this problem |
| `time_ms` | Integer | Time for this problem |

##### Table: `app_settings`

Key-value store for application settings.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Setting ID |
| `key` | String(100) | Unique setting key |
| `value` | JSON | Setting value |
| `created_at` | DateTime(tz) | Created |
| `updated_at` | DateTime(tz) | Last updated |

---

### 5.4 Dependency Injection

**File:** `backend/app/dependencies.py`

FastAPI dependency injection functions:

| Function | Returns | Description |
|----------|---------|-------------|
| `get_settings_dep()` | `Settings` | Cached application settings |
| `get_db()` | `AsyncSession` | Database session with auto-commit/rollback |
| `get_redis()` | `RedisManager` or None | Redis connection (optional) |
| `get_task_service(db)` | `TaskService` | Task CRUD operations |
| `get_settings_service(db)` | `SettingsService` | Settings CRUD operations |
| `get_benchmark_service(db)` | `BenchmarkService` | Benchmark operations |
| `get_sandbox_executor()` | `CodeExecutor` | Docker sandbox executor |

**Important:** `get_db()` commits on success and rolls back on exception. This is critical — without the commit, changes are never persisted to the database.

---

### 5.5 API Routes (21 Endpoints)

All routes are prefixed with `/api/v1`.

#### Health Check

| Method | Path | Response | Description |
|--------|------|----------|-------------|
| `GET` | `/health` | `{status, database, redis, docker}` | Service health status |

#### Tasks

| Method | Path | Request Body | Response | Description |
|--------|------|-------------|----------|-------------|
| `POST` | `/tasks/` | `{"prompt": "..."}` (1-10000 chars) | `TaskResponse` (201) | Create task, starts orchestrator as background job |
| `GET` | `/tasks/{task_id}` | — | `TaskDetail` | Full task with plan, code, output, traces |
| `GET` | `/tasks/{task_id}/traces` | — | `AgentTrace[]` | All agent traces for a task |
| `DELETE` | `/tasks/{task_id}` | — | `{success: bool}` | Delete task (cascades) |

**Background Processing:** After `POST /tasks/`, the orchestrator runs as an `asyncio.create_task()` background job. It updates the task record in the database as it progresses through each stage.

#### History

| Method | Path | Query Params | Response | Description |
|--------|------|-------------|----------|-------------|
| `GET` | `/history/` | `status`, `search`, `date_from`, `date_to`, `sort_by`, `order`, `page`, `per_page` | `{items[], total, page, per_page, total_pages}` | Paginated task history with filtering |

#### Benchmarks

| Method | Path | Request | Response | Description |
|--------|------|---------|----------|-------------|
| `POST` | `/benchmarks/run` | `{type: "humaneval"|"mbpp"|"custom", with_repair: bool}` | `BenchmarkRunResponse` (202) | Trigger benchmark (async) |
| `GET` | `/benchmarks/runs` | — | `BenchmarkRun[]` | List all benchmark runs |
| `GET` | `/benchmarks/runs/{run_id}` | — | `BenchmarkRunDetail` | Run with all problem results |

#### Settings

| Method | Path | Request | Response | Description |
|--------|------|---------|----------|-------------|
| `GET` | `/settings/` | — | `{llm, routing, sandbox}` | Get all settings |
| `PUT` | `/settings/` | Partial `{llm?, routing?, sandbox?}` | `{llm, routing, sandbox}` | Update settings |
| `POST` | `/settings/test-connection` | `{provider, api_key?, endpoint?}` | `{success, message, latency_ms?}` | Test LLM provider connectivity |

#### Analytics

| Method | Path | Query | Response | Description |
|--------|------|-------|----------|-------------|
| `GET` | `/analytics/cost` | `days=30` | `{total_cost_usd, cost_by_model, cost_by_agent, daily_costs[]}` | Cost breakdown |
| `GET` | `/analytics/performance` | `days=30` | `{total_tasks, success_rate, avg_time_ms, avg_retries, tasks_by_status}` | Performance metrics |
| `GET` | `/analytics/models` | `days=30` | `{distribution[{model, count, percentage}]}` | Model usage distribution |

#### WebSocket

| Protocol | Path | Description |
|----------|------|-------------|
| `WS` | `/ws/tasks/{task_id}` | Real-time task execution updates |

---

### 5.6 Services Layer

**Task Service** (`app/services/task_service.py`) — CRUD operations for tasks, filtering, pagination, search.

**Settings Service** (`app/services/settings_service.py`) — Read/write app_settings key-value store, maps to structured settings objects.

**Benchmark Service** (`app/services/benchmark_service.py`) — Creates benchmark runs, records individual results, computes pass@1 metrics.

---

## 6. LLM Layer — Providers, Classification & Routing

### 6.1 LLM Providers

**File:** `backend/app/llm/providers.py`

#### LLMResponse

Every LLM call returns this standardized response:

```python
@dataclass
class LLMResponse:
    content: str           # Generated text
    model: str             # Model identifier
    input_tokens: int      # Input tokens consumed
    output_tokens: int     # Output tokens generated
    total_tokens: int      # Sum of input + output
    latency_ms: int        # Request latency in milliseconds
    raw_response: dict?    # Optional raw API response
```

#### Provider Implementations

All providers inherit from `BaseLLMProvider` and implement three methods:

| Method | Purpose |
|--------|---------|
| `generate()` | Unstructured text generation |
| `generate_structured()` | JSON-enforced generation (with retry on parse failure) |
| `health_check()` | Test provider connectivity |

##### OpenAI Provider
- Uses `langchain_openai.ChatOpenAI`
- Default model: `gpt-4`
- Extracts tokens from `response.usage_metadata`

##### Anthropic Provider
- Uses `langchain_anthropic.ChatAnthropic`
- Default model: `claude-sonnet-4-20250514`
- Same interface as OpenAI provider

##### Ollama Provider
- Direct HTTP calls to Ollama REST API (`/api/generate`)
- Default model: `llama3:8b`
- No API key required (local)
- 120-second timeout
- Estimates tokens if not provided by API (word count * 1.3)

##### OpenRouter Provider
- Uses `langchain_openai.ChatOpenAI` with `base_url="https://openrouter.ai/api/v1"`
- Gateway to 200+ models via single API key
- Default model: `openai/gpt-4o-mini`

##### Provider Factory

```python
LLMProviderFactory.create("openai", api_key="...", model="gpt-4")
LLMProviderFactory.create("anthropic", api_key="...", model="claude-sonnet-4-20250514")
LLMProviderFactory.create("ollama", base_url="http://localhost:11434", model="llama3:8b")
LLMProviderFactory.create("openrouter", api_key="...", model="openai/gpt-4o-mini")
```

#### Structured Generation (JSON)

All providers share the same retry pattern for JSON output:
1. First attempt: Append "Respond ONLY with valid JSON" to system prompt
2. Parse response as JSON
3. If `JSONDecodeError`: retry with stronger instruction
4. If second attempt fails: raise error

---

### 6.2 Task Complexity Classifier

**File:** `backend/app/llm/classifier.py`

#### Complexity Levels

```python
class ComplexityLevel(Enum):
    SIMPLE = "simple"    # Single function, basic operations
    MEDIUM = "medium"    # Multiple functions, standard libraries
    HARD = "hard"        # Multi-step, complex logic, advanced algorithms
```

#### Heuristic Classifier (Default)

Fast, no-LLM classification using keyword matching and text analysis:

**Scoring Signals:**

| Signal | Simple Score | Hard Score |
|--------|-------------|------------|
| Simple keyword match (e.g., "hello world", "fibonacci") | +0.2 each | — |
| Hard keyword match (e.g., "database", "algorithm", "async") | — | +0.15 each |
| Word count < 50 | +0.3 | — |
| Word count > 200 | — | +0.3 |
| Sentence count > 5 | — | +0.2 |
| Requirement markers >= 5 ("and", "also", "include"...) | — | +0.2 |
| Requirement markers <= 1 | +0.1 | — |

**Classification Logic:**
- If `hard_score >= complex_threshold` (default 0.7) → **HARD**
- Else if `simple_score >= simple_threshold` (default 0.3) AND `hard_score < 0.2` → **SIMPLE**
- Else → **MEDIUM**

**Simple Keywords (34):** hello world, print, fizzbuzz, string manipulation, basic math, single function, reverse string, palindrome, factorial, fibonacci, swap, addition, subtraction, multiplication...

**Hard Keywords (30):** multiple files, database, api, rest api, graphql, concurrent, distributed, algorithm, optimize, machine learning, neural, deep learning, microservice, websocket, authentication, encryption, parser, compiler, async, threading, redis, kafka, docker...

#### LLM Classifier (Optional)

Uses a cheap LLM to classify with higher accuracy. Falls back to heuristic on failure. Asks the LLM to respond with:
```json
{"level": "SIMPLE|MEDIUM|HARD", "confidence": 0.0-1.0, "reasoning": "brief"}
```

---

### 6.3 Model Router

**File:** `backend/app/llm/router.py`

#### Default Model Mapping

| Complexity | Provider | Model | Input Cost/1K | Output Cost/1K |
|-----------|----------|-------|--------------|----------------|
| SIMPLE | ollama | llama3:8b | $0.00 | $0.00 |
| MEDIUM | openai | gpt-4o-mini | $0.00015 | $0.0006 |
| HARD | openai | gpt-4 | $0.03 | $0.06 |

#### Fallback Chains

When the preferred provider is unavailable, the router tries alternatives:

- **Simple tasks:** ollama → openrouter → openai → anthropic
- **Complex tasks:** openai → openrouter → anthropic → ollama

#### Provider Availability Detection

| Provider | Available When |
|----------|---------------|
| OpenAI | `openai_api_key` is set and not placeholder |
| Anthropic | `anthropic_api_key` is set and not placeholder |
| OpenRouter | `openrouter_api_key` is set and not placeholder/empty |
| Ollama | `ollama_base_url` is truthy |

#### Routing Flow

```
prompt → classify(prompt) → complexity level
                               │
                         look up default model
                               │
                         check available providers
                               │
                    ┌──── preferred available? ────┐
                    yes                            no
                    │                              │
              use preferred                  try fallback chain
                    │                              │
              return (provider, config, level)
```

---

### 6.4 Cost Tracker

**File:** `backend/app/llm/cost_tracker.py`

#### Pricing Database (USD per 1K tokens)

| Model | Input | Output |
|-------|-------|--------|
| gpt-4 | $0.030 | $0.060 |
| gpt-4-turbo | $0.010 | $0.030 |
| gpt-4o | $0.005 | $0.015 |
| gpt-4o-mini | $0.00015 | $0.0006 |
| gpt-3.5-turbo | $0.0005 | $0.0015 |
| claude-sonnet-4-20250514 | $0.003 | $0.015 |
| claude-haiku-4-5-20251001 | $0.0008 | $0.004 |
| claude-3-opus-20240229 | $0.015 | $0.075 |
| llama3:8b | $0.00 | $0.00 |
| llama3:70b | $0.00 | $0.00 |
| mistral:7b | $0.00 | $0.00 |
| codellama:7b | $0.00 | $0.00 |

Unknown models fall back to gpt-4o-mini pricing with a warning log.

#### Cost Tracking Features

- **Per-call recording:** Every LLM call creates a `CostRecord` with model, tokens, cost, timestamp
- **Running totals:** Accumulated cost and token counts
- **Summary report:** Cost breakdown by model, token breakdown by model, total records
- **Savings estimation:** Calculates how much was saved vs. always using GPT-4 (the most expensive model)

---

## 7. Agent System — The Core Intelligence

### 7.1 Base Agent (Template Method Pattern)

**File:** `backend/app/agents/base.py`

All agents inherit from `BaseAgent` which implements the **Template Method** design pattern:

```python
class BaseAgent(ABC):
    def __init__(self, llm, cost_tracker, callback=None)

    # Template method (public API)
    async def run(self, input_data: AgentInput) -> AgentOutput:
        callback.on_agent_start()
        try:
            output = await self._execute(input_data)  # subclass implements
            callback.on_agent_complete()
            return output
        except Exception:
            callback.on_agent_error()
            return AgentOutput(success=False, error=str(exc))

    # Abstract methods (subclasses implement)
    async def _execute(self, input_data) -> AgentOutput
    def _build_system_prompt(self) -> str
    def _build_user_prompt(self, input_data) -> str
```

**Helper Methods:**
- `_call_llm(prompt, system_prompt, structured)` — Calls the LLM, records cost, notifies callback
- `_parse_json_response(text)` — Strips markdown fences, extracts JSON via regex fallback

#### Agent Types

```python
class AgentType(Enum):
    PLANNER = "planner"
    CODER = "coder"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
```

#### Agent I/O

```python
@dataclass
class AgentInput:
    data: dict          # Task-specific input
    task_id: str        # Unique task ID
    step_order: int     # Execution order (1, 2, 3...)

@dataclass
class AgentOutput:
    data: dict          # Task-specific output
    reasoning: str      # Explanation
    tokens_used: int    # Total tokens
    cost_usd: float     # USD cost
    duration_ms: int    # Execution time
    success: bool       # Whether it worked
    error: str?         # Error message if failed
```

---

### 7.2 Planner Agent

**File:** `backend/app/agents/planner.py`
**Prompt:** `backend/app/agents/prompts/planner.py`

**Purpose:** Decomposes a user's coding task into ordered subtasks with dependencies.

**System Prompt Key Instructions:**
- Break task into 2-6 subtasks
- Each subtask must be independently implementable
- Define dependencies (DAG)
- Estimate each subtask's complexity
- Final subtask must be an integration step with `main()`
- Output pure JSON (no markdown)

**Output Schema:**
```json
{
  "subtasks": [
    {
      "id": 1,
      "description": "Write a function that...",
      "dependencies": [],
      "estimated_complexity": "simple"
    }
  ],
  "reasoning": "Explanation of decomposition strategy"
}
```

**Validation Rules:**
1. Must have `subtasks` key with non-empty list
2. Each subtask must have: `id`, `description`, `dependencies`, `estimated_complexity`
3. All IDs must be unique integers
4. Dependencies must reference valid existing IDs
5. No self-dependencies
6. No circular dependencies (verified via **Kahn's topological sort** algorithm)

If validation fails, the agent retries once with error feedback.

---

### 7.3 Coder Agent

**File:** `backend/app/agents/coder.py`
**Prompt:** `backend/app/agents/prompts/coder.py`

**Purpose:** Generates Python code for each subtask.

**System Prompt Key Instructions:**
- Write Python 3.11+ with type hints
- Google-style docstrings
- Handle edge cases (empty inputs, None, type mismatches)
- Only standard library + allowed packages (numpy, pandas, matplotlib, scipy, sklearn, requests, bs4, sympy, PIL, networkx)
- PEP 8 compliant
- Integration subtask: complete runnable script with `main()` and `if __name__ == "__main__"`

**Output Schema:**
```json
{
  "code": "<complete Python code>",
  "imports": ["list", "of", "required", "packages"],
  "explanation": "Brief description of approach"
}
```

**Context Provided to Coder:**
- Current subtask description and complexity
- Full plan context (all subtasks)
- Previously generated code from completed dependency subtasks
- Dependency information

**Validation:**
- Syntax validation via `compile(code, "<generated>", "exec")`
- If syntax error: retries once with error feedback

**Code Merging:**
- Extracts and deduplicates imports from all code segments
- Preserves function/class definitions from all segments
- Combines with integration code into a single file

---

### 7.4 Reviewer Agent

**File:** `backend/app/agents/reviewer.py`
**Prompt:** `backend/app/agents/prompts/reviewer.py`

**Purpose:** Analyzes execution failures and generates minimal fixes.

**System Prompt Key Instructions:**
- Identify ROOT CAUSE from traceback
- Classify error type: `syntax_error`, `runtime_error`, `logic_error`, `import_error`, `timeout`, `memory_error`
- Suggest MINIMAL fix (fewest line changes)
- Provide COMPLETE fixed code (not just changed lines)
- Rate confidence 0.0 to 1.0
- If confidence < 0.5, suggest a completely different approach

**Input Context:**
- Original task description
- Failed code
- Exit code, stdout, stderr
- Attempt number (X of Y)

**Output Schema:**
```json
{
  "root_cause": "Description of why the code failed",
  "error_type": "runtime_error",
  "fix_description": "What the fix does and why",
  "fixed_code": "<complete corrected Python code>",
  "confidence": 0.85,
  "changes_made": ["Line 12: changed dict['key'] to dict.get('key', default)"]
}
```

**Validation:**
1. Must have keys: `root_cause`, `fixed_code`, `confidence`
2. Confidence must be a number between 0.0 and 1.0
3. Fixed code must pass syntax validation via `compile()`

---

### 7.5 Orchestrator — LangGraph State Machine

**File:** `backend/app/agents/orchestrator.py`

The orchestrator ties all agents together using a **LangGraph compiled state machine**.

#### State Object (AgentState)

```python
class AgentState(TypedDict):
    # Input
    prompt: str                      # User's task prompt
    task_id: str                     # Unique task ID

    # Classification
    complexity: str                  # "simple" / "medium" / "hard"
    model_used: str                  # Model identifier

    # Planning
    plan: Optional[dict]             # Decomposed subtask plan
    current_subtask_index: int       # Current subtask being processed

    # Coding
    code_segments: dict              # {subtask_id → generated code}
    integrated_code: str             # Final merged runnable code

    # Execution
    execution_result: Optional[dict] # {exit_code, stdout, stderr, time, memory, timed_out}
    execution_success: bool          # True if exit_code == 0

    # Review / Repair
    review_result: Optional[dict]    # Reviewer's analysis and fix
    retry_count: int                 # Repair attempts made
    max_retries: int                 # Maximum allowed retries

    # Metadata
    total_cost_usd: float            # Accumulated LLM cost
    total_tokens: int                # Accumulated tokens
    traces: list                     # Agent execution traces
    error_message: Optional[str]     # Error if failed
    status: str                      # Current pipeline status
```

#### Graph Nodes (8 Nodes)

| Node | Purpose | Key Logic |
|------|---------|-----------|
| `classify` | Classify complexity, select model | Routes via ModelRouter, returns complexity + model_used |
| `plan` | Decompose into subtasks | Creates PlannerAgent, validates DAG |
| `code` | Generate code per subtask | Creates CoderAgent, iterates subtasks with context |
| `execute` | Run code in Docker sandbox | Creates CodeExecutor, captures output |
| `review` | Analyze failure | Creates ReviewerAgent, identifies root cause + fix |
| `apply_fix` | Apply the fix | Replaces integrated_code, exponential backoff |
| `finalize` | Mark success | Sets status="completed" |
| `fail` | Mark failure | Sets status="failed" with error_message |

#### Graph Edges

```
classify ──→ plan ──→ code ──→ execute
                                  │
                        ┌─────────┴─────────┐
                   success=true        success=false
                        │                   │
                    finalize             review
                        │                   │
                       END          ┌───────┴──────┐
                                retry=true    retry=false
                                    │              │
                                apply_fix        fail
                                    │              │
                                 execute          END
                                (loop back)
```

#### Conditional Edge Functions

**`check_execution(state)`:**
- Returns `"success"` if `execution_success == True`
- Returns `"failure"` otherwise

**`should_retry(state)`:**
- Returns `"abort"` if `retry_count >= max_retries`
- Returns `"abort"` if reviewer confidence < 0.3 AND retry_count >= 2 (early abort)
- Returns `"retry"` otherwise

#### Exponential Backoff

Before re-execution, `apply_fix` sleeps with exponential backoff:
- Retry 1: 1 second
- Retry 2: 2 seconds
- Retry 3: 4 seconds
- Capped at 8 seconds

---

## 8. Sandbox Execution — Docker Isolation

**Files:** `backend/app/sandbox/executor.py`, `backend/app/sandbox/manager.py`

### How It Works

1. The `CodeExecutor` receives generated Python code
2. Creates a Docker container from the `codeforge-sandbox-python:latest` image
3. Writes code to a temporary file inside the container
4. Executes `python3 <file>` with resource limits
5. Captures stdout, stderr, exit code, execution time, memory usage
6. Destroys the container

### Security Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Image | `codeforge-sandbox-python:latest` | Pre-built image with Python + common packages |
| Timeout | 30 seconds | Maximum execution time |
| Memory | 512 MB | Container memory limit |
| CPU | 1.0 core | CPU allocation |
| Network | Disabled | No internet access from sandbox |

### Execution Output

```python
@dataclass
class ExecutionOutput:
    exit_code: int           # 0 = success
    stdout: str              # Standard output
    stderr: str              # Standard error
    execution_time_ms: int   # Execution duration
    memory_used_mb: float?   # Memory consumption
    timed_out: bool          # True if timeout exceeded
    success: bool            # True if exit_code == 0
```

---

## 9. Real-Time Communication — WebSocket

**File:** `backend/app/api/websocket.py`

### Connection Management

The `ConnectionManager` maintains a dictionary of active WebSocket connections per task:
```python
active_connections: dict[str, list[WebSocket]]  # task_id → [connections]
```

### WebSocket Events

Events are broadcast to all connected clients for a given task_id:

#### Agent Events
| Event | Data | When |
|-------|------|------|
| `agent.started` | `{agent_type, step_order, input_summary}` | Agent begins execution |
| `agent.thinking` | `{agent_type, chunk}` | LLM generates partial response |
| `agent.completed` | `{agent_type, output_summary, tokens_used, cost_usd, duration_ms}` | Agent finishes |
| `agent.error` | `{agent_type, error}` | Agent encounters error |

#### Code Events
| Event | Data | When |
|-------|------|------|
| `code.generated` | `{code, language, subtask_index}` | Coder produces code |

#### Execution Events
| Event | Data | When |
|-------|------|------|
| `execution.started` | `{container_id, retry_number}` | Sandbox execution begins |
| `execution.stdout` | `{line}` | Stdout output line |
| `execution.stderr` | `{line}` | Stderr output line |
| `execution.completed` | `{exit_code, execution_time_ms, memory_used_mb}` | Execution finishes |

#### Repair Events
| Event | Data | When |
|-------|------|------|
| `repair.started` | `{retry_number, error_summary}` | Self-repair begins |
| `repair.fix_applied` | `{fixed_code, change_summary}` | Fix applied to code |

#### Task Events
| Event | Data | When |
|-------|------|------|
| `task.completed` | `{final_code, final_output, total_cost, total_time_ms, retry_count}` | Task succeeds |
| `task.failed` | `{error_message, retry_count}` | Task fails permanently |
| `task.status_changed` | `{new_status}` | Status transitions |

### WebSocket Callback

The `WebSocketAgentCallback` class implements the agent callback interface, translating agent lifecycle events into WebSocket broadcasts. It is injected into the Orchestrator when a task is created.

---

## 10. Observability — Logging, Tracing & Metrics

### Structured Logging
- Configurable level (DEBUG, INFO, WARNING, ERROR)
- Configurable format (json for production, text for development)
- Logger hierarchy: `codeforge.router`, `codeforge.classifier`, `codeforge.agent.planner`, etc.

### OpenTelemetry Tracing
- Service name: `codeforge-backend`
- OTLP exporter to configurable endpoint (default: `localhost:4317`)
- FastAPI auto-instrumentation

### Correlation ID Middleware
- Adds unique request tracking IDs
- Propagated through log entries and traces

---

## 11. Frontend — Next.js 16

### 11.1 Pages

#### Chat Page (`/`)
The main interaction page. Users type a coding task and see real-time execution:
- **ChatInput** — Auto-expanding textarea, Enter to submit, Shift+Enter for newline
- **TaskStream** — Renders agent progress, code blocks, terminal output, repair diffs in real-time
- WebSocket connects after task creation for live streaming

#### History Page (`/history`)
Browse and inspect past tasks with a 40/60 split layout:
- **Left panel:** Filtered, paginated task list with status badges
- **Right panel:** Full task detail — metadata, agent timeline, plan JSON, final code, output
- **Filters:** Status, search text, date range, sort by (date/cost/duration), ascending/descending

#### Benchmarks Page (`/benchmarks`)
Dashboard for evaluating system performance:
- **Stats cards:** Latest pass@1 rate, total cost, average retries
- **PassRateChart** — Bar chart comparing baseline vs. with-repair
- **CostAnalysis** — Pie chart of cost by model
- **ModelDistribution** — Horizontal bar chart of model usage
- **HistoricalTrend** — Line chart of pass rates over time
- **Recent Runs Table** — Last 10 runs with metrics
- **Trigger buttons:** Run humaneval, mbpp, or custom benchmarks

#### Settings Page (`/settings`)
Configuration UI with three tabs:
- **LLM Providers** — API key inputs for OpenAI, Anthropic, Ollama with connection test buttons
- **Routing** — Complexity threshold sliders (0-1) with visual tier breakdown
- **Sandbox** — Timeout, memory limit, max retries sliders, network toggle

---

### 11.2 Components

#### Layout Components

| Component | Purpose |
|-----------|---------|
| `ThemeProvider` | Dark/light theme via next-themes (default: dark) |
| `Sidebar` | Collapsible left navigation with page links, theme toggle, collapse toggle |
| `Header` | Page title + backend connection status indicator (polls `/health` every 10s) |

#### Chat Components

| Component | Props | Purpose |
|-----------|-------|---------|
| `ChatInput` | `onSubmit, disabled` | Prompt input with auto-height |
| `TaskStream` | `events, isLoading` | Full task execution rendering |
| `CodeBlock` | `code, language?, filename?` | Monaco editor (read-only) with copy/download |

#### Agent Components

| Component | Props | Purpose |
|-----------|-------|---------|
| `StatusBadge` | `status` | Color-coded status pills with pulse animation |
| `AgentCard` | `agentType, status, thinking?, duration?, cost?, tokens?` | Expandable agent execution card |
| `AgentTimeline` | `traces` | Duration bar chart showing agent execution distribution |
| `AgentFlowDiagram` | `activeAgent?, status?, retryCount?` | ReactFlow diagram of the pipeline |

#### Execution Components

| Component | Props | Purpose |
|-----------|-------|---------|
| `TerminalOutput` | `lines[], exitCode?, executionTime?, memoryUsage?` | Terminal emulator (green stdout, red stderr) |
| `RepairDiff` | `attempts[]` | Side-by-side original vs. fixed code in Monaco |

#### History Components

| Component | Props | Purpose |
|-----------|-------|---------|
| `FilterBar` | `params, onChange` | Search, status/sort dropdowns |
| `TaskList` | `tasks[], selectedId?, onSelect, pagination...` | Paginated task list |
| `TaskDetail` | `task` | Full task display with timeline, plan, code, output |

#### Benchmark Components

| Component | Props | Purpose |
|-----------|-------|---------|
| `PassRateChart` | `runs[]` | Recharts BarChart (baseline vs. repair) |
| `CostAnalysis` | `data` | PieChart cost by model |
| `ModelDistribution` | `data` | Horizontal bar chart model usage |
| `HistoricalTrend` | `runs[]` | LineChart pass rate over time |

#### Settings Components

| Component | Props | Purpose |
|-----------|-------|---------|
| `LLMProviderForm` | `value, onChange` | API key inputs + test buttons |
| `RoutingConfig` | `value, onChange` | Threshold sliders |
| `SandboxConfig` | `value, onChange` | Timeout/memory/retries sliders |

#### UI Library (shadcn/ui + Radix)

15 base components in `src/components/ui/`: button, card, input, textarea, badge, tabs, separator, scroll-area, dialog, alert, dropdown-menu, select, slider, switch, label, sonner (toasts).

---

### 11.3 Custom Hooks

| Hook | Returns | Purpose |
|------|---------|---------|
| `useTask` | `{submitTask, currentTaskId, taskDetail, isLoading, error, events, connected, reset}` | Task lifecycle: create → WebSocket → poll for completion |
| `useBenchmarks` | `{runs, currentRun, isLoading, error, triggerRun, selectRun, refresh}` | Benchmark run management |
| `useWebSocket` | `{connected, events, lastEvent, error, clearEvents}` | Low-level WebSocket with auto-reconnect (exponential backoff, 3 retries) |

---

### 11.4 API Client & WebSocket Client

#### API Client (`src/lib/api.ts`)

Base URL: `process.env.NEXT_PUBLIC_API_URL` or `http://localhost:8000`

All functions use a shared `apiFetch<T>()` wrapper that:
- Prepends `/api/v1` to all paths
- Sets `Content-Type: application/json`
- Throws with HTTP status + response text on non-2xx

| Function | Method | Path | Purpose |
|----------|--------|------|---------|
| `createTask(prompt)` | POST | `/tasks/` | Create new task |
| `getTask(taskId)` | GET | `/tasks/{id}` | Get task detail |
| `getTaskTraces(taskId)` | GET | `/tasks/{id}/traces` | Get agent traces |
| `deleteTask(taskId)` | DELETE | `/tasks/{id}` | Delete task |
| `getHistory(params)` | GET | `/history/` | Filtered task list |
| `getSettings()` | GET | `/settings/` | Get app settings |
| `updateSettings(settings)` | PUT | `/settings/` | Update settings |
| `testConnection(provider, key?, endpoint?)` | POST | `/settings/test-connection` | Test LLM connection |
| `triggerBenchmark(type, withRepair)` | POST | `/benchmarks/run` | Start benchmark |
| `getBenchmarkRuns()` | GET | `/benchmarks/runs` | List benchmarks |
| `getBenchmarkRun(runId)` | GET | `/benchmarks/runs/{id}` | Benchmark detail |
| `getCostSummary(days)` | GET | `/analytics/cost` | Cost analytics |
| `getPerformanceSummary(days)` | GET | `/analytics/performance` | Performance analytics |
| `getModelDistribution(days)` | GET | `/analytics/models` | Model distribution |
| `checkHealth()` | GET | `/health` | Backend health check |

#### WebSocket Client (`src/lib/ws.ts`)

Base URL: `process.env.NEXT_PUBLIC_WS_URL` or `ws://localhost:8000`

Builds WebSocket URL: `{baseUrl}/api/v1/ws/tasks/{taskId}`

Event constants (`WS_EVENTS`): `task.started`, `task.completed`, `task.failed`, `agent.started`, `agent.thinking`, `agent.completed`, `code.generated`, `execution.started`, `execution.stdout`, `execution.stderr`, `execution.completed`, `repair.started`, `repair.fix_applied`, `status.change`

---

### 11.5 TypeScript Types

**File:** `src/lib/types.ts`

```typescript
type TaskStatus = 'pending' | 'classifying' | 'planning' | 'coding' | 'executing'
               | 'reviewing' | 'repairing' | 'completed' | 'failed'

interface Task {
  id: string; prompt: string; status: TaskStatus; complexity: string | null;
  model_used: string | null; total_cost_usd: number; total_time_ms: number | null;
  retry_count: number; error_message: string | null;
  created_at: string; updated_at: string;
}

interface TaskDetail extends Task {
  plan: object | null; final_code: string | null;
  final_output: string | null; traces: AgentTrace[];
}

interface AgentTrace {
  id: string; task_id: string; agent_type: string;
  input_data: object; output_data: object | null; reasoning: string | null;
  tokens_used: number; cost_usd: number; duration_ms: number | null;
  step_order: number; created_at: string;
}

interface BenchmarkRun {
  id: string; benchmark_type: string; total_problems: number;
  passed: number; pass_at_1: number; pass_at_1_repair: number | null;
  avg_retries: number | null; total_cost_usd: number;
  total_time_ms: number | null; created_at: string;
}

interface AppSettings {
  llm: { openai_api_key, anthropic_api_key, ollama_endpoint }
  routing: { simple_threshold, complex_threshold, simple_model, complex_model }
  sandbox: { timeout_seconds, memory_limit_mb, max_retries }
}

interface WSEvent {
  event: string; timestamp: string; data: Record<string, unknown>;
}
```

---

## 12. Testing

### 12.1 Unit Tests (32 tests)

**Location:** `backend/tests/unit/`

#### Planner Tests (`test_planner.py` — 7 tests)

| Test | Validates |
|------|-----------|
| `test_planner_system_prompt_contains_key_instructions` | System prompt includes "subtasks", "JSON", "dependencies" |
| `test_planner_user_prompt_includes_task` | User prompt embeds task description |
| `test_validate_plan_valid` | Valid plan with dependencies passes |
| `test_validate_plan_missing_subtasks` | Missing "subtasks" key fails |
| `test_validate_plan_circular_dependency` | Circular deps (A→B→A) rejected |
| `test_validate_plan_invalid_dependency_id` | Reference to non-existent ID fails |
| `test_validate_plan_empty_subtasks` | Empty subtasks list fails |

#### Coder Tests (`test_coder.py` — 7 tests)

| Test | Validates |
|------|-----------|
| `test_coder_user_prompt_includes_subtask` | Prompt contains subtask ID and description |
| `test_coder_user_prompt_includes_prior_code` | Prior dependency code included |
| `test_validate_code_valid_python` | Valid syntax passes |
| `test_validate_code_syntax_error` | Syntax errors detected |
| `test_merge_code_deduplicates_imports` | Import deduplication works |
| `test_merge_code_preserves_functions` | Function definitions preserved |
| `test_coder_prompt_for_integration_subtask` | Integration instructions present |

#### Reviewer Tests (`test_reviewer.py` — 6 tests)

| Test | Validates |
|------|-----------|
| `test_reviewer_prompt_includes_error` | Error output (stderr, exit_code) in prompt |
| `test_reviewer_prompt_includes_attempt_info` | "X of Y" attempt count shown |
| `test_validate_review_valid` | All required keys pass |
| `test_validate_review_missing_keys` | Missing fields fail |
| `test_validate_review_invalid_confidence` | Confidence outside [0,1] fails |
| `test_validate_review_broken_fixed_code` | Invalid syntax in fix fails |

#### Model Router Tests (`test_model_router.py` — 5 tests)

| Test | Validates |
|------|-----------|
| `test_simple_task_routes_to_ollama` | SIMPLE → ollama |
| `test_complex_task_routes_to_gpt4` | HARD → openai/gpt-4 |
| `test_fallback_when_ollama_unavailable` | Fallback chain works |
| `test_available_providers_detection` | API key detection works |
| `test_model_config_dataclass` | ModelConfig stores data correctly |

#### Cost Tracker Tests (`test_cost_tracker.py` — 7 tests)

| Test | Expected |
|------|----------|
| `test_gpt4_cost_calculation` | 1000 in + 500 out = $0.06 |
| `test_llama_free_cost` | $0.00 |
| `test_unknown_model_uses_default` | Falls back gracefully |
| `test_summary_aggregation` | Totals correct |
| `test_cost_by_model_breakdown` | Per-model breakdown |
| `test_savings_calculation` | Savings vs GPT-4 > 0 |
| `test_reset_clears_all` | Reset works |

---

### 12.2 Integration Tests

**Location:** `backend/tests/integration/`

#### Self-Repair Tests (`test_self_repair.py` — 4 tests)

Uses mock LLM provider and mock sandbox executor to test the full repair loop:

| Test | Scenario | Expected |
|------|----------|----------|
| `test_successful_execution_no_repair` | Code succeeds first try | status=completed, retries=0 |
| `test_self_repair_fixes_on_first_retry` | Fails once, fixed by reviewer | status=completed, retries=1 |
| `test_self_repair_exhausts_retries` | All retries fail | status=failed, retries=max |
| `test_low_confidence_early_abort` | Reviewer low confidence | status=failed, retries=2 (early) |

#### Sandbox Execution Tests (`test_sandbox_execution.py` — 10 tests)

Requires Docker and the sandbox image:

| Test | Code Executed | Expected |
|------|--------------|----------|
| `test_execute_simple_print` | `print("Hello CodeForge")` | success, "Hello CodeForge" in stdout |
| `test_execute_math_computation` | `math.factorial(10)` | "3628800" in stdout |
| `test_execute_with_imports` | numpy array sum | "6" in stdout |
| `test_execute_pandas` | DataFrame shape | "(3, 1)" in stdout |
| `test_execute_syntax_error` | Invalid syntax | "SyntaxError" in stderr |
| `test_execute_runtime_error` | Division by zero | "ZeroDivisionError" in stderr |
| `test_execute_import_error` | Nonexistent module | "ModuleNotFoundError" in stderr |
| `test_execute_timeout` | `time.sleep(60)` | timed_out=True |
| `test_execute_stderr_capture` | Print to stderr | stderr captured |
| `test_execute_multiline_output` | Loop printing | Multiple lines captured |

---

### 12.3 End-to-End Tests (7+ tests)

**Location:** `backend/tests/e2e/test_full_pipeline.py`

Uses in-memory SQLite with `StaticPool`, httpx `AsyncClient` with ASGI transport, mocked Redis and orchestrator.

| Test | Endpoints | Validates |
|------|-----------|-----------|
| `test_health_endpoint` | GET /health | Returns 200 with status |
| `test_full_task_lifecycle` | POST + GET + GET traces | Task creation → retrieval → traces |
| `test_task_not_found` | GET /tasks/{fake} | Returns 404 |
| `test_history_endpoint` | POST (3x) + GET /history/ | Tasks appear, no duplicates |
| `test_history_filtering` | GET /history/?status=pending | Filter works |
| `test_history_search` | GET /history/?search=fibonacci | Search works |
| `test_settings_crud` | GET + PUT + GET /settings/ | Read, update, persist, retrieve |
| `test_task_validation` | POST with empty prompt | Returns 400/422 |
| `test_task_delete` | POST + DELETE + GET | Delete succeeds, 404 after |

### Running Tests

```bash
cd codeforge/backend

# All tests
python3 -m pytest tests/ -v

# Unit tests only
python3 -m pytest tests/unit/ -v

# Integration tests (requires Docker)
python3 -m pytest tests/integration/ -v

# E2E tests
python3 -m pytest tests/e2e/ -v

# With coverage
python3 -m pytest tests/ --cov=app --cov-report=term-missing
```

---

## 13. Project Structure

```
codeforge/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app factory + lifespan
│   │   ├── config.py                  # Pydantic Settings (all env vars)
│   │   ├── dependencies.py            # Dependency injection
│   │   │
│   │   ├── api/                       # API Routes
│   │   │   ├── router.py              # Main router (prefix /api/v1)
│   │   │   ├── health.py              # GET /health
│   │   │   ├── tasks.py               # POST/GET/DELETE /tasks/
│   │   │   ├── history.py             # GET /history/
│   │   │   ├── benchmarks.py          # POST/GET /benchmarks/
│   │   │   ├── settings.py            # GET/PUT /settings/
│   │   │   ├── analytics.py           # GET /analytics/{cost,performance,models}
│   │   │   └── websocket.py           # WS /ws/tasks/{task_id}
│   │   │
│   │   ├── models/
│   │   │   ├── database.py            # SQLAlchemy ORM (6 tables)
│   │   │   └── schemas.py             # Pydantic v2 schemas (30+ schemas)
│   │   │
│   │   ├── db/
│   │   │   ├── session.py             # Async engine + session factory
│   │   │   └── redis.py               # Redis connection manager
│   │   │
│   │   ├── services/
│   │   │   ├── task_service.py         # Task CRUD + filtering
│   │   │   ├── settings_service.py     # Settings CRUD
│   │   │   └── benchmark_service.py    # Benchmark operations
│   │   │
│   │   ├── llm/                        # LLM Integration Layer
│   │   │   ├── providers.py            # 4 LLM providers + factory
│   │   │   ├── classifier.py           # Complexity classification
│   │   │   ├── router.py              # Model routing + fallback chains
│   │   │   └── cost_tracker.py         # Token/cost tracking
│   │   │
│   │   ├── agents/                     # Multi-Agent System
│   │   │   ├── base.py                # BaseAgent (template method)
│   │   │   ├── planner.py             # Task decomposition agent
│   │   │   ├── coder.py              # Code generation agent
│   │   │   ├── reviewer.py            # Failure analysis agent
│   │   │   ├── orchestrator.py         # LangGraph state machine
│   │   │   └── prompts/
│   │   │       ├── planner.py          # Planner system + user prompts
│   │   │       ├── coder.py           # Coder system + user prompts
│   │   │       └── reviewer.py         # Reviewer system + user prompts
│   │   │
│   │   ├── sandbox/                    # Docker Sandbox
│   │   │   ├── executor.py             # CodeExecutor interface
│   │   │   └── manager.py             # SandboxManager (Docker)
│   │   │
│   │   └── observability/              # Observability
│   │       ├── logging.py              # Structured logging setup
│   │       ├── tracing.py             # OpenTelemetry setup
│   │       └── middleware.py           # Correlation ID middleware
│   │
│   ├── tests/
│   │   ├── conftest.py                # Shared fixtures
│   │   ├── unit/                      # 32 unit tests
│   │   │   ├── test_planner.py
│   │   │   ├── test_coder.py
│   │   │   ├── test_reviewer.py
│   │   │   ├── test_model_router.py
│   │   │   └── test_cost_tracker.py
│   │   ├── integration/               # 14 integration tests
│   │   │   ├── test_self_repair.py
│   │   │   └── test_sandbox_execution.py
│   │   └── e2e/                       # 7+ E2E tests
│   │       └── test_full_pipeline.py
│   │
│   ├── alembic/                       # Database migrations
│   ├── alembic.ini
│   ├── requirements.txt               # 20 Python packages
│   ├── pyproject.toml                 # Project config + ruff + pytest
│   ├── Dockerfile
│   └── .env                           # Environment variables
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx             # Root layout (Geist font, ThemeProvider)
│   │   │   ├── page.tsx               # Chat page (/)
│   │   │   ├── history/page.tsx       # History page
│   │   │   ├── benchmarks/page.tsx    # Benchmarks page
│   │   │   └── settings/page.tsx      # Settings page
│   │   │
│   │   ├── components/
│   │   │   ├── layout/               # ThemeProvider, Sidebar, Header
│   │   │   ├── chat/                 # ChatInput, TaskStream, CodeBlock
│   │   │   ├── agents/              # StatusBadge, AgentCard, Timeline, FlowDiagram
│   │   │   ├── execution/           # TerminalOutput, RepairDiff
│   │   │   ├── history/             # FilterBar, TaskList, TaskDetail
│   │   │   ├── benchmarks/          # PassRateChart, CostAnalysis, etc.
│   │   │   ├── settings/            # LLMProviderForm, RoutingConfig, SandboxConfig
│   │   │   └── ui/                  # 15 shadcn/ui base components
│   │   │
│   │   ├── hooks/
│   │   │   ├── useTask.ts            # Task lifecycle management
│   │   │   ├── useBenchmarks.ts      # Benchmark management
│   │   │   └── useWebSocket.ts       # WebSocket with auto-reconnect
│   │   │
│   │   └── lib/
│   │       ├── api.ts                # HTTP API client (15 functions)
│   │       ├── ws.ts                 # WebSocket client + events
│   │       ├── types.ts              # TypeScript type definitions
│   │       └── utils.ts              # cn() utility (clsx + tailwind-merge)
│   │
│   ├── package.json
│   ├── next.config.ts                # output: 'standalone'
│   ├── tsconfig.json
│   ├── postcss.config.mjs
│   ├── components.json               # shadcn/ui config (new-york style)
│   └── Dockerfile
│
└── DOCUMENTATION.md                   # This file
```

---

## 14. Environment Variables

**File:** `backend/.env`

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./codeforge_dev.db
DATABASE_SYNC_URL=sqlite:///./codeforge_dev.db

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# LLM API Keys (set at least one)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OPENROUTER_API_KEY=sk-or-v1-...
OLLAMA_BASE_URL=

# Model Defaults
DEFAULT_SIMPLE_MODEL=openai/gpt-4o-mini
DEFAULT_COMPLEX_MODEL=openai/gpt-4o-mini

# Complexity Thresholds
COMPLEXITY_SIMPLE_THRESHOLD=0.3
COMPLEXITY_COMPLEX_THRESHOLD=0.7

# Docker Sandbox
SANDBOX_IMAGE=codeforge-sandbox-python:latest
SANDBOX_TIMEOUT_SECONDS=30
SANDBOX_MEMORY_LIMIT_MB=512
SANDBOX_CPU_LIMIT=1.0
SANDBOX_NETWORK_DISABLED=true

# Self-Repair
MAX_REPAIR_RETRIES=2

# Docker
DOCKER_HOST=unix:///var/run/docker.sock

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=codeforge-backend
LOG_LEVEL=INFO
LOG_FORMAT=text

# Server
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000
SECRET_KEY=codeforge-dev-secret-2024
```

---

## 15. Running the Project

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker (for sandbox execution)
- Docker image: `codeforge-sandbox-python:latest`

### Backend

```bash
cd codeforge/backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env   # Edit with your API keys

# Create database tables
python3 -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.models.database import Base

async def init():
    engine = create_async_engine('sqlite+aiosqlite:///./codeforge_dev.db')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

asyncio.run(init())
"

# Start server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Backend available at:** http://localhost:8000
**API docs (Swagger):** http://localhost:8000/docs

### Frontend

```bash
cd codeforge/frontend

# Install dependencies
npm install

# Start dev server
npm run dev -- -p 3000
```

**Frontend available at:** http://localhost:3000

### Quick Test

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Create a task
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a Python function to check if a number is prime"}'
```

---

## 16. Known Limitations

1. **Single Model Routing** — Both `OPENROUTER_SIMPLE_MODEL` and `OPENROUTER_COMPLEX_MODEL` default to the same model (`openai/gpt-4o-mini`). For true cost optimization, set them to different models (e.g., simple=gpt-4o-mini, complex=gpt-4o or claude-sonnet).

2. **Classifier Thresholds** — If set to 0.0, everything classifies as HARD. Use the defaults (0.3 / 0.7) for proper routing.

3. **SQLite Limitations** — Alembic migrations are configured for PostgreSQL (`asyncpg` string replacement in `env.py`). With SQLite, use `Base.metadata.create_all` directly.

4. **No Redis** — Redis is optional. Without it, there is no caching layer.

5. **Agent Traces** — Traces are recorded in the orchestrator state but may not always persist to the database `agent_traces` table (the orchestrator updates the task record but trace persistence depends on the task service implementation).

6. **Sandbox Network** — Network is disabled by default. Code that requires internet access (e.g., `requests.get()`) will fail in the sandbox.

7. **Exponential Backoff** — The apply_fix node sleeps up to 8 seconds between retries, which adds latency to the self-repair loop.

---

*Generated on 2026-03-06. This documentation covers the complete CodeForge codebase including all backend services, LLM integrations, agent system, sandbox execution, frontend pages, components, hooks, API client, WebSocket system, and test suite.*
