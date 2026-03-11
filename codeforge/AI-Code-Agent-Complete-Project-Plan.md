# AI Code Agent with Self-Repair — Complete Project Plan

> **Project Codename:** CodeForge  
> **Target Timeline:** 4 weeks (3–4 hrs/day)  
> **Author:** AI/ML Engineer Candidate  
> **Goal:** Production-grade multi-agent system demonstrating orchestration, tool use, error recovery, evaluation rigor, cost optimization, and observability.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Directory Structure](#2-directory-structure)
3. [Database Schema](#3-database-schema)
4. [API Specification](#4-api-specification)
5. [WebSocket Event Specification](#5-websocket-event-specification)
6. [Agent Specifications](#6-agent-specifications)
7. [LangGraph State Machine](#7-langgraph-state-machine)
8. [Frontend Component Tree](#8-frontend-component-tree)
9. [Task Breakdown](#9-task-breakdown)
10. [Docker Compose Configuration](#10-docker-compose-configuration)
11. [Environment Variables](#11-environment-variables)
12. [Testing Strategy](#12-testing-strategy)
13. [Benchmark Evaluation Plan](#13-benchmark-evaluation-plan)
14. [README Structure](#14-readme-structure)

---

## 1. System Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Next.js 14)                            │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐  ┌──────────┐  ┌────────┐ │
│  │Chat Panel│  │Agent Viz Flow│  │Exec Output│  │Benchmarks│  │Settings│ │
│  └────┬─────┘  └──────┬───────┘  └─────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │               │               │              │             │      │
│       └───────────┬───┴───────────────┴──────────────┴─────────────┘      │
│                   │  WebSocket (real-time)  +  REST API                    │
└───────────────────┼───────────────────────────────────────────────────────┘
                    │
┌───────────────────┼───────────────────────────────────────────────────────┐
│                   │         API GATEWAY  (FastAPI + uvicorn)              │
│                   ▼                                                       │
│  ┌────────────────────────┐    ┌──────────────────────────┐              │
│  │  WebSocket Manager     │    │  REST Router              │              │
│  │  (real-time streaming) │    │  /tasks, /history,        │              │
│  └────────┬───────────────┘    │  /benchmarks, /settings   │              │
│           │                    └──────────┬───────────────┘              │
│           ▼                               ▼                              │
│  ┌─────────────────────────────────────────────────────────┐             │
│  │              ORCHESTRATOR  (LangGraph State Machine)     │             │
│  │                                                          │             │
│  │   ┌─────────┐   ┌───────┐   ┌──────────┐   ┌────────┐  │             │
│  │   │ Planner │──▶│ Coder │──▶│ Executor │──▶│Reviewer│  │             │
│  │   │  Agent  │   │ Agent │   │  Agent   │   │ Agent  │  │             │
│  │   └─────────┘   └───┬───┘   └──────────┘   └───┬────┘  │             │
│  │                     ▲                           │       │             │
│  │                     │    Self-Repair Loop       │       │             │
│  │                     └───────────────────────────┘       │             │
│  └─────────────────────────────────────────────────────────┘             │
│           │              │               │                               │
│           ▼              ▼               ▼                               │
│  ┌──────────────┐ ┌───────────┐  ┌──────────────────┐                   │
│  │Model Router  │ │  Docker   │  │  OpenTelemetry   │                   │
│  │              │ │  Sandbox  │  │  Collector        │                   │
│  │ simple→Llama│ │  Manager  │  │       │           │                   │
│  │ complex→GPT4│ │           │  │       ▼           │                   │
│  └──────┬───────┘ └─────┬────┘  │  ┌─────────┐     │                   │
│         │               │       │  │  Jaeger  │     │                   │
│         ▼               ▼       │  └─────────┘     │                   │
│  ┌────────────┐  ┌──────────┐  └──────────────────┘                    │
│  │ Ollama     │  │Sandboxed │                                           │
│  │ (Llama-3)  │  │Container │                                           │
│  │            │  │ (Python) │                                           │
│  │ OpenAI API │  │ 30s TO   │                                           │
│  │ Claude API │  │ 512MB    │                                           │
│  └────────────┘  │ No net   │                                           │
│                  └──────────┘                                           │
│                                                                         │
│  ┌──────────────┐  ┌───────┐  ┌────────────────────┐                   │
│  │ PostgreSQL   │  │ Redis │  │ Background Worker  │                   │
│  │ (persistence)│  │(cache)│  │ (asyncio tasks)    │                   │
│  └──────────────┘  └───────┘  └────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Interaction Sequence (Single Task)

```
User ──▶ POST /api/tasks {prompt}
              │
              ▼
         Orchestrator
              │
     ┌────────┴────────┐
     ▼                 ▼
  Model Router     Planner Agent
  (classify         (break into
   complexity)       subtasks)
     │                 │
     │        ┌────────┴─── plan = [{subtask, deps}]
     ▼        ▼
         Coder Agent ◀─── (for each subtask)
              │
              ▼
         Executor Agent ──▶ Docker Sandbox
              │                    │
              ▼                    ▼
         Result? ◄──────── stdout/stderr/exit_code
              │
         ┌────┴────┐
         │         │
      Success    Failure
         │         │
         ▼         ▼
       Done    Reviewer Agent
                   │
                   ▼
              Self-Repair Loop (≤3 retries)
              Coder ──▶ Executor ──▶ Review
                   │
              ┌────┴────┐
              │         │
           Fixed     Max retries
              │         │
              ▼         ▼
            Done      Failed
```

---

## 2. Directory Structure

```
codeforge/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Lint, type-check, unit tests
│       ├── integration.yml           # Integration tests (Docker required)
│       └── benchmark.yml             # Weekly benchmark runs
│
├── backend/
│   ├── alembic/                      # DB migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app factory, lifespan
│   │   ├── config.py                 # Pydantic settings, env loading
│   │   ├── dependencies.py           # FastAPI dependency injection
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py             # Aggregate all routers
│   │   │   ├── tasks.py              # POST /tasks, GET /tasks/{id}
│   │   │   ├── history.py            # GET /history, filters, search
│   │   │   ├── benchmarks.py         # GET /benchmarks, POST /benchmarks/run
│   │   │   ├── settings.py           # GET/PUT /settings
│   │   │   └── websocket.py          # WS /ws/tasks/{task_id}
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # BaseAgent abstract class
│   │   │   ├── planner.py            # PlannerAgent
│   │   │   ├── coder.py              # CoderAgent
│   │   │   ├── executor.py           # ExecutorAgent
│   │   │   ├── reviewer.py           # ReviewerAgent
│   │   │   ├── orchestrator.py       # LangGraph state machine
│   │   │   └── prompts/
│   │   │       ├── __init__.py
│   │   │       ├── planner.py        # Planner system/user prompts
│   │   │       ├── coder.py          # Coder system/user prompts
│   │   │       └── reviewer.py       # Reviewer system/user prompts
│   │   │
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── router.py             # Model router (complexity → model)
│   │   │   ├── providers.py          # OpenAI, Anthropic, Ollama wrappers
│   │   │   ├── classifier.py         # Task complexity classifier
│   │   │   └── cost_tracker.py       # Token/cost accounting
│   │   │
│   │   ├── sandbox/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py            # Docker container lifecycle
│   │   │   ├── executor.py           # Code execution in sandbox
│   │   │   └── security.py           # Validation, resource limits
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── database.py           # SQLAlchemy models
│   │   │   └── schemas.py            # Pydantic request/response models
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── task_service.py       # Business logic for tasks
│   │   │   ├── benchmark_service.py  # Benchmark execution logic
│   │   │   └── settings_service.py   # Settings CRUD
│   │   │
│   │   ├── observability/
│   │   │   ├── __init__.py
│   │   │   ├── tracing.py            # OpenTelemetry setup
│   │   │   ├── metrics.py            # Custom metrics
│   │   │   └── logging.py            # Structured JSON logging
│   │   │
│   │   └── db/
│   │       ├── __init__.py
│   │       ├── session.py            # Async session factory
│   │       └── repository.py         # Generic CRUD repository
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py               # Fixtures, test DB, mock LLM
│   │   ├── unit/
│   │   │   ├── test_planner.py
│   │   │   ├── test_coder.py
│   │   │   ├── test_reviewer.py
│   │   │   ├── test_model_router.py
│   │   │   ├── test_cost_tracker.py
│   │   │   └── test_sandbox.py
│   │   ├── integration/
│   │   │   ├── test_orchestrator.py
│   │   │   ├── test_sandbox_execution.py
│   │   │   └── test_self_repair.py
│   │   └── e2e/
│   │       └── test_full_pipeline.py
│   │
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx            # Root layout
│   │   │   ├── page.tsx              # Main chat page
│   │   │   ├── benchmarks/
│   │   │   │   └── page.tsx
│   │   │   ├── history/
│   │   │   │   └── page.tsx
│   │   │   └── settings/
│   │   │       └── page.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   └── ThemeProvider.tsx
│   │   │   │
│   │   │   ├── chat/
│   │   │   │   ├── ChatInput.tsx
│   │   │   │   ├── ChatMessage.tsx
│   │   │   │   ├── TaskStream.tsx
│   │   │   │   └── CodeBlock.tsx
│   │   │   │
│   │   │   ├── agents/
│   │   │   │   ├── AgentFlowDiagram.tsx
│   │   │   │   ├── AgentTimeline.tsx
│   │   │   │   ├── AgentCard.tsx
│   │   │   │   └── StatusBadge.tsx
│   │   │   │
│   │   │   ├── execution/
│   │   │   │   ├── TerminalOutput.tsx
│   │   │   │   ├── RepairDiff.tsx
│   │   │   │   └── ResourceUsage.tsx
│   │   │   │
│   │   │   ├── benchmarks/
│   │   │   │   ├── PassRateChart.tsx
│   │   │   │   ├── CostAnalysis.tsx
│   │   │   │   ├── ModelDistribution.tsx
│   │   │   │   └── HistoricalTrend.tsx
│   │   │   │
│   │   │   ├── settings/
│   │   │   │   ├── LLMProviderForm.tsx
│   │   │   │   ├── SandboxConfig.tsx
│   │   │   │   └── RoutingConfig.tsx
│   │   │   │
│   │   │   └── history/
│   │   │       ├── TaskList.tsx
│   │   │       ├── TaskDetail.tsx
│   │   │       └── FilterBar.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useTask.ts
│   │   │   └── useBenchmarks.ts
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts                # REST client
│   │   │   ├── ws.ts                 # WebSocket client
│   │   │   └── types.ts              # Shared TypeScript types
│   │   │
│   │   └── styles/
│   │       └── globals.css
│   │
│   ├── public/
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── Dockerfile
│
├── docker/
│   ├── sandbox/
│   │   ├── Dockerfile.python         # Python 3.11 + numpy, pandas, etc.
│   │   └── Dockerfile.node           # Node.js 20 (optional)
│   └── otel/
│       └── otel-collector-config.yml
│
├── benchmarks/
│   ├── __init__.py
│   ├── runner.py                     # Benchmark orchestrator
│   ├── humaneval/
│   │   ├── __init__.py
│   │   ├── loader.py                 # Load HumanEval problems
│   │   ├── evaluator.py              # pass@1 calculation
│   │   └── data/                     # HumanEval dataset (gitignored, downloaded)
│   ├── mbpp/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── evaluator.py
│   │   └── data/
│   ├── custom/
│   │   ├── __init__.py
│   │   ├── tasks.json                # 25 custom multi-step tasks
│   │   └── evaluator.py
│   └── results/                      # Benchmark output (gitignored)
│       └── .gitkeep
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── agent-design.md
│   ├── deployment.md
│   └── images/
│       └── architecture-diagram.png
│
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── .gitignore
├── Makefile
├── LICENSE
└── README.md
```

---

## 3. Database Schema

### ER Diagram (ASCII)

```
┌──────────────┐       ┌──────────────┐       ┌──────────────────┐
│    tasks     │       │  agent_traces │       │ execution_results│
├──────────────┤       ├──────────────┤       ├──────────────────┤
│ id (PK, UUID)│◄──┐   │ id (PK, UUID)│       │ id (PK, UUID)    │
│ prompt       │   ├──▶│ task_id (FK) │   ┌──▶│ trace_id (FK)    │
│ status       │   │   │ agent_type   │   │   │ exit_code        │
│ complexity   │   │   │ input_data   │──▶┘   │ stdout           │
│ model_used   │   │   │ output_data  │       │ stderr           │
│ plan         │   │   │ reasoning    │       │ execution_time_ms│
│ final_code   │   │   │ tokens_used  │       │ memory_used_mb   │
│ final_output │   │   │ cost_usd     │       │ container_id     │
│ total_cost   │   │   │ duration_ms  │       │ retry_number     │
│ total_time_ms│   │   │ step_order   │       │ created_at       │
│ retry_count  │   │   │ created_at   │       └──────────────────┘
│ error_message│   │   └──────────────┘
│ created_at   │   │
│ updated_at   │   │   ┌──────────────────┐
└──────────────┘   │   │ benchmark_runs   │
                   │   ├──────────────────┤
                   │   │ id (PK, UUID)    │
                   │   │ benchmark_type   │   ┌──────────────────┐
                   │   │ model_config     │   │ benchmark_results│
                   │   │ total_problems   │   ├──────────────────┤
                   │   │ passed           │   │ id (PK, UUID)    │
                   │   │ pass_at_1        │   │ run_id (FK)      │
                   │   │ pass_at_1_repair │   │ problem_id       │
                   │   │ avg_retries      │   │ passed           │
                   │   │ total_cost       │   │ passed_after_rep │
                   │   │ total_time_ms    │   │ retries_used     │
                   │   │ created_at       │   │ generated_code   │
                   └───│                  │   │ error_message    │
                       └──────────────────┘   │ cost_usd         │
                                              │ time_ms          │
┌──────────────────┐                          └──────────────────┘
│   app_settings   │
├──────────────────┤
│ key (PK, VARCHAR)│
│ value (JSONB)    │
│ updated_at       │
└──────────────────┘
```

### Table Definitions

**tasks**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Unique task ID |
| prompt | TEXT | NOT NULL | Original user prompt |
| status | VARCHAR(20) | NOT NULL | planning, coding, executing, reviewing, repairing, completed, failed |
| complexity | VARCHAR(10) | NULL | simple, medium, hard |
| model_used | VARCHAR(50) | NULL | Which LLM handled the task |
| plan | JSONB | NULL | Planner output (subtasks + dependencies) |
| final_code | TEXT | NULL | Final generated code |
| final_output | TEXT | NULL | Final execution output |
| total_cost_usd | DECIMAL(10,6) | DEFAULT 0 | Total cost in USD |
| total_time_ms | INTEGER | NULL | End-to-end duration |
| retry_count | INTEGER | DEFAULT 0 | Number of repair attempts |
| error_message | TEXT | NULL | Final error if failed |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | |

**agent_traces**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| task_id | UUID | FK → tasks.id, ON DELETE CASCADE | |
| agent_type | VARCHAR(20) | NOT NULL | planner, coder, executor, reviewer |
| input_data | JSONB | NOT NULL | What the agent received |
| output_data | JSONB | NULL | What the agent produced |
| reasoning | TEXT | NULL | Chain-of-thought / explanation |
| tokens_used | INTEGER | DEFAULT 0 | Input + output tokens |
| cost_usd | DECIMAL(10,6) | DEFAULT 0 | |
| duration_ms | INTEGER | NULL | |
| step_order | INTEGER | NOT NULL | Ordering within the task |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |

**execution_results**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | |
| trace_id | UUID | FK → agent_traces.id | Links to the executor trace |
| exit_code | INTEGER | NOT NULL | 0 = success |
| stdout | TEXT | DEFAULT '' | |
| stderr | TEXT | DEFAULT '' | |
| execution_time_ms | INTEGER | NOT NULL | |
| memory_used_mb | FLOAT | NULL | |
| container_id | VARCHAR(64) | NULL | Docker container hash |
| retry_number | INTEGER | DEFAULT 0 | Which attempt (0 = first) |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | |

**benchmark_runs** and **benchmark_results** — as diagrammed above.

**app_settings** — key-value store for user configuration (API keys encrypted at rest, routing thresholds, execution limits).

---

## 4. API Specification

### Base URL: `/api/v1`

#### Tasks

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|-------------|----------|
| POST | `/tasks` | Submit a new task | `{ prompt: string }` | `{ task_id: UUID, status: "planning" }` |
| GET | `/tasks/{task_id}` | Get task status + full details | — | `TaskDetail` (see below) |
| GET | `/tasks/{task_id}/traces` | Get all agent traces for a task | — | `AgentTrace[]` |
| DELETE | `/tasks/{task_id}` | Cancel / delete a task | — | `{ success: true }` |

**TaskDetail schema:**
```json
{
  "id": "uuid",
  "prompt": "string",
  "status": "completed",
  "complexity": "medium",
  "model_used": "gpt-4",
  "plan": { "subtasks": [...] },
  "final_code": "def solve():\n  ...",
  "final_output": "42",
  "total_cost_usd": 0.023,
  "total_time_ms": 4500,
  "retry_count": 1,
  "error_message": null,
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### History

| Method | Path | Description | Query Params |
|--------|------|-------------|-------------|
| GET | `/history` | List past tasks | `?status=completed&search=sort&page=1&per_page=20&sort_by=created_at&order=desc` |

#### Benchmarks

| Method | Path | Description | Request Body |
|--------|------|-------------|-------------|
| POST | `/benchmarks/run` | Trigger benchmark run | `{ type: "humaneval" \| "mbpp" \| "custom", with_repair: bool }` |
| GET | `/benchmarks/runs` | List all benchmark runs | — |
| GET | `/benchmarks/runs/{run_id}` | Get benchmark run details + per-problem results | — |

#### Settings

| Method | Path | Description | Body |
|--------|------|-------------|------|
| GET | `/settings` | Get all settings | — |
| PUT | `/settings` | Update settings | `SettingsUpdate` (partial) |
| POST | `/settings/test-connection` | Test LLM provider connectivity | `{ provider: "openai", api_key: "..." }` |

**SettingsUpdate schema:**
```json
{
  "openai_api_key": "sk-...",
  "anthropic_api_key": "sk-ant-...",
  "ollama_endpoint": "http://ollama:11434",
  "routing": {
    "simple_threshold": 0.3,
    "complex_threshold": 0.7,
    "simple_model": "llama3:8b",
    "complex_model": "gpt-4"
  },
  "sandbox": {
    "timeout_seconds": 30,
    "memory_limit_mb": 512,
    "max_retries": 3
  }
}
```

#### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Readiness check (DB, Redis, Docker, Ollama) |

---

## 5. WebSocket Event Specification

### Connection: `ws://host/api/v1/ws/tasks/{task_id}`

All events follow a uniform envelope:

```json
{
  "event": "event_name",
  "timestamp": "2025-01-01T00:00:00Z",
  "data": { ... }
}
```

### Server → Client Events

| Event | Data Payload | When |
|-------|-------------|------|
| `task.status_changed` | `{ status, previous_status }` | Any state transition |
| `agent.started` | `{ agent_type, step_order, input_summary }` | Agent begins work |
| `agent.thinking` | `{ agent_type, chunk }` | Streaming LLM tokens (reasoning) |
| `agent.completed` | `{ agent_type, output_summary, tokens_used, cost_usd, duration_ms }` | Agent finishes |
| `code.generated` | `{ code, language, subtask_index }` | Coder produces code |
| `execution.started` | `{ container_id, retry_number }` | Sandbox container spun up |
| `execution.stdout` | `{ line }` | Real-time stdout from sandbox |
| `execution.stderr` | `{ line }` | Real-time stderr from sandbox |
| `execution.completed` | `{ exit_code, execution_time_ms, memory_used_mb }` | Execution done |
| `repair.started` | `{ retry_number, error_summary }` | Self-repair loop triggered |
| `repair.fix_applied` | `{ original_code_hash, fixed_code, change_summary }` | Fix generated |
| `task.completed` | `{ final_code, final_output, total_cost, total_time_ms, retry_count }` | Success |
| `task.failed` | `{ error_message, retry_count }` | All retries exhausted |
| `error` | `{ message, code }` | System/connection error |

### Client → Server Events

| Event | Data | Purpose |
|-------|------|---------|
| `task.cancel` | `{}` | Cancel a running task |

---

## 6. Agent Specifications

### 6.1 Planner Agent

**Role:** Decompose a natural language task into an ordered execution plan.

**Input:**
```json
{
  "prompt": "Write a Python function that downloads a CSV from a URL, cleans null values, and generates a bar chart of the top 10 categories.",
  "complexity": "hard"
}
```

**Output:**
```json
{
  "subtasks": [
    {
      "id": 1,
      "description": "Write a function to download CSV data from a URL using requests",
      "dependencies": [],
      "estimated_complexity": "simple"
    },
    {
      "id": 2,
      "description": "Write a function to clean null values from a pandas DataFrame",
      "dependencies": [1],
      "estimated_complexity": "simple"
    },
    {
      "id": 3,
      "description": "Write a function to compute top 10 categories by count and generate a matplotlib bar chart",
      "dependencies": [2],
      "estimated_complexity": "medium"
    },
    {
      "id": 4,
      "description": "Write a main() function that chains the three steps together with error handling",
      "dependencies": [1, 2, 3],
      "estimated_complexity": "simple"
    }
  ],
  "reasoning": "The task has three clear stages: data acquisition, data cleaning, and visualization. Each is independently testable. A main function ties them together."
}
```

**System Prompt (core excerpt):**
```
You are a software planning agent. Given a natural language coding task:
1. Break it into 2-6 subtasks. Each must be independently implementable.
2. Identify dependencies (which subtasks must complete before others).
3. Estimate complexity per subtask (simple/medium/hard).
4. Ensure the final subtask integrates everything into a runnable script.

Output ONLY valid JSON matching the schema. No explanation outside the JSON.
```

**State Transitions:** `IDLE → PLANNING → PLAN_READY`

---

### 6.2 Coder Agent

**Role:** Generate production-quality Python code for a given subtask, following the plan.

**Input:**
```json
{
  "subtask": { "id": 2, "description": "...", "dependencies": [1] },
  "plan": { ... },
  "prior_code": { "1": "def download_csv(url): ..." },
  "language": "python"
}
```

**Output:**
```json
{
  "code": "import pandas as pd\n\ndef clean_nulls(df: pd.DataFrame) -> pd.DataFrame:\n    ...",
  "imports": ["pandas"],
  "explanation": "Uses dropna() with subset parameter for targeted null removal."
}
```

**System Prompt (core excerpt):**
```
You are a code generation agent. Given a subtask and any prior code from completed subtasks:
1. Write clean, typed, documented Python code.
2. Include docstrings with Args/Returns.
3. Handle edge cases and errors gracefully.
4. Import only standard library + common packages (numpy, pandas, matplotlib, requests).
5. If this is the final integration subtask, produce a complete runnable script with if __name__ == "__main__".

Output ONLY valid JSON with "code", "imports", and "explanation" keys.
```

**State Transitions:** `PLAN_READY → CODING → CODE_READY`

---

### 6.3 Executor Agent

**Role:** Run generated code in a Docker sandbox and capture results.

**Input:**
```json
{
  "code": "...",
  "language": "python",
  "timeout_seconds": 30,
  "memory_limit_mb": 512
}
```

**Output:**
```json
{
  "success": true,
  "exit_code": 0,
  "stdout": "Chart saved to output.png\n",
  "stderr": "",
  "execution_time_ms": 1200,
  "memory_used_mb": 45.3,
  "container_id": "abc123"
}
```

**Implementation Notes:**
- Uses Docker SDK for Python to create ephemeral containers
- Mounts code as a read-only volume
- `--network=none` for security (no network access)
- `--memory=512m --cpus=1` resource limits
- Captures stdout/stderr via `container.logs()`
- Kills container after timeout

**State Transitions:** `CODE_READY → EXECUTING → EXEC_SUCCESS | EXEC_FAILED`

---

### 6.4 Reviewer Agent

**Role:** Analyze execution failures, identify root cause, and suggest a targeted fix.

**Input:**
```json
{
  "code": "...",
  "error": {
    "exit_code": 1,
    "stderr": "Traceback (most recent call last):\n  File \"main.py\", line 12, in ...\nKeyError: 'category'",
    "stdout": ""
  },
  "attempt_number": 1,
  "max_attempts": 3,
  "original_task": "..."
}
```

**Output:**
```json
{
  "root_cause": "The code assumes a 'category' column exists but the CSV uses 'Category' (capitalized).",
  "fix_description": "Normalize column names to lowercase before accessing.",
  "fix_type": "bug_fix",
  "suggested_code_change": "df.columns = df.columns.str.lower()  # Add after loading CSV",
  "confidence": 0.92
}
```

**System Prompt (core excerpt):**
```
You are a code review and debugging agent. Given failed code and its error output:
1. Identify the root cause from the traceback/stderr.
2. Classify the error: syntax_error, runtime_error, logic_error, import_error, timeout.
3. Suggest the minimal targeted fix (do NOT rewrite the entire program).
4. Rate your confidence in the fix (0.0 to 1.0).

If confidence < 0.5, suggest a fundamentally different approach instead.
Output ONLY valid JSON.
```

**State Transitions:** `EXEC_FAILED → REVIEWING → FIX_READY`

---

### 6.5 Self-Repair Loop

The repair loop is not a separate agent but a state machine cycle:

```
EXEC_FAILED → Reviewer → FIX_READY → Coder (apply fix) → CODE_READY → Executor → EXEC_SUCCESS | EXEC_FAILED
```

Retry policy:
- **Max 3 retries** (configurable)
- **Exponential backoff:** 0s, 2s, 4s between retries (avoids hammering the LLM)
- **Escape hatch:** If Reviewer confidence < 0.3 on attempt 2+, abort early
- After max retries → `FAILED` state with full error trail

---

## 7. LangGraph State Machine

### State Definition

```python
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    # Input
    prompt: str
    task_id: str

    # Planning
    complexity: Optional[str]           # simple | medium | hard
    plan: Optional[dict]                # Planner output
    current_subtask_index: int          # Which subtask we're on

    # Coding
    code_segments: dict[int, str]       # subtask_id → code
    integrated_code: Optional[str]      # Final merged code

    # Execution
    execution_result: Optional[dict]    # Latest execution output
    execution_success: bool

    # Review / Repair
    review_result: Optional[dict]       # Reviewer output
    retry_count: int
    max_retries: int                    # Default 3

    # Metadata
    model_used: str
    total_cost_usd: float
    traces: list[dict]                  # Accumulated agent traces
    error_message: Optional[str]
    status: str
```

### Graph Definition

```python
graph = StateGraph(AgentState)

# Nodes
graph.add_node("classify",      classify_complexity)
graph.add_node("plan",          run_planner)
graph.add_node("code",          run_coder)
graph.add_node("execute",       run_executor)
graph.add_node("review",        run_reviewer)
graph.add_node("apply_fix",     apply_fix_and_recode)
graph.add_node("finalize",      finalize_success)
graph.add_node("fail",          finalize_failure)

# Edges
graph.set_entry_point("classify")

graph.add_edge("classify", "plan")
graph.add_edge("plan",     "code")
graph.add_edge("code",     "execute")

# Conditional: execution result
graph.add_conditional_edges(
    "execute",
    check_execution,                  # Returns "success" | "failure"
    {
        "success":   "finalize",
        "failure":   "review",
    }
)

# Conditional: should retry or give up?
graph.add_conditional_edges(
    "review",
    should_retry,                     # Returns "retry" | "abort"
    {
        "retry":  "apply_fix",
        "abort":  "fail",
    }
)

graph.add_edge("apply_fix", "execute")
graph.add_edge("finalize",  END)
graph.add_edge("fail",      END)
```

### Conditional Functions

```python
def check_execution(state: AgentState) -> str:
    return "success" if state["execution_success"] else "failure"

def should_retry(state: AgentState) -> str:
    if state["retry_count"] >= state["max_retries"]:
        return "abort"
    if (state["review_result"] and
        state["review_result"].get("confidence", 0) < 0.3 and
        state["retry_count"] >= 2):
        return "abort"     # Low-confidence escape hatch
    return "retry"
```

### Visual State Machine

```
                ┌───────────┐
                │  classify  │
                └─────┬─────┘
                      ▼
                ┌───────────┐
                │   plan     │
                └─────┬─────┘
                      ▼
                ┌───────────┐
           ┌───▶│   code     │
           │    └─────┬─────┘
           │          ▼
           │    ┌───────────┐
           │    │  execute   │
           │    └─────┬─────┘
           │          │
           │    ┌─────┴─────┐
           │    ▼           ▼
           │ success     failure
           │    │           │
           │    ▼           ▼
           │ ┌──────┐  ┌────────┐
           │ │final-│  │ review │
           │ │ize   │  └───┬────┘
           │ └──┬───┘      │
           │    │     ┌────┴────┐
           │    ▼     ▼         ▼
           │   END  retry     abort
           │          │         │
           │          ▼         ▼
           │   ┌──────────┐ ┌──────┐
           └───┤apply_fix │ │ fail │
               └──────────┘ └──┬───┘
                               ▼
                              END
```

---

## 8. Frontend Component Tree

```
App (layout.tsx)
├── ThemeProvider
├── Sidebar
│   ├── NavLink → / (Chat)
│   ├── NavLink → /history
│   ├── NavLink → /benchmarks
│   └── NavLink → /settings
│
├── Header
│   ├── ProjectTitle
│   └── ConnectionStatus (WS indicator)
│
└── Page Routes
    │
    ├── / (Main Chat)
    │   ├── TaskStream
    │   │   ├── ChatMessage[]
    │   │   │   └── CodeBlock (Monaco/CodeMirror, copy button)
    │   │   ├── AgentCard[]
    │   │   │   ├── StatusBadge (planning|coding|executing|reviewing|repairing)
    │   │   │   └── CollapsibleReasoning
    │   │   └── TerminalOutput
    │   │       ├── StdoutLine (green)
    │   │       ├── StderrLine (red)
    │   │       └── ResourceUsage (time, memory)
    │   │
    │   ├── AgentFlowDiagram (visual node graph of agent pipeline)
    │   │   └── AgentNode[] (highlighted when active)
    │   │
    │   ├── RepairDiff (side-by-side: original error → fix → result)
    │   │
    │   └── ChatInput
    │       ├── TextArea (auto-resize)
    │       └── SubmitButton
    │
    ├── /history
    │   ├── FilterBar (status dropdown, search input, date range)
    │   ├── TaskList
    │   │   └── TaskListItem[] (prompt preview, status badge, cost, time)
    │   └── TaskDetail (expanded view with full traces)
    │
    ├── /benchmarks
    │   ├── RunBenchmarkButton
    │   ├── PassRateChart (bar: HumanEval/MBPP, with vs without repair)
    │   ├── CostAnalysis (pie: model cost distribution)
    │   ├── ModelDistribution (bar: % tasks per model)
    │   └── HistoricalTrend (line: pass@1 over time)
    │
    └── /settings
        ├── LLMProviderForm
        │   ├── OpenAIKeyInput + TestButton
        │   ├── AnthropicKeyInput + TestButton
        │   └── OllamaEndpointInput + TestButton
        ├── RoutingConfig
        │   ├── ThresholdSliders (simple/complex boundaries)
        │   └── ModelSelectors
        └── SandboxConfig
            ├── TimeoutInput
            ├── MemoryLimitInput
            └── MaxRetriesInput
```

### Key Frontend Libraries

| Component | Library | Purpose |
|-----------|---------|---------|
| Code display | `@monaco-editor/react` | Syntax highlighting, read-only code blocks |
| Charts | `recharts` | Benchmark visualizations |
| Agent flow | `reactflow` | Visual node-based agent diagram |
| Terminal | Custom `<pre>` with ANSI parsing | Execution output |
| UI components | `shadcn/ui` | Buttons, cards, inputs, dialogs, badges, tabs |
| WebSocket | Custom hook wrapping native WS | Real-time streaming |

---

## 9. Task Breakdown

### Phase 1: Foundation (Week 1) — ~25 hrs

| # | Task | Files | Time | Depends On |
|---|------|-------|------|------------|
| 1.1 | **Project scaffolding** — init monorepo, pyproject.toml, package.json, .gitignore, Makefile | Root configs | 1h | — |
| 1.2 | **Backend FastAPI skeleton** — app factory, config, health endpoint, uvicorn runner | `backend/app/main.py`, `config.py`, `api/router.py` | 1.5h | 1.1 |
| 1.3 | **Database setup** — PostgreSQL with async SQLAlchemy, Alembic migrations, all table models | `backend/app/models/`, `backend/app/db/`, `alembic/` | 3h | 1.2 |
| 1.4 | **Pydantic schemas** — Request/response models for all API endpoints | `backend/app/models/schemas.py` | 2h | 1.3 |
| 1.5 | **REST API endpoints** — Tasks CRUD, history (list + filter), settings CRUD | `backend/app/api/tasks.py`, `history.py`, `settings.py` | 3h | 1.4 |
| 1.6 | **Redis integration** — Connection pool, caching layer for settings | `backend/app/dependencies.py` | 1h | 1.2 |
| 1.7 | **Docker Compose (dev)** — PostgreSQL + Redis + backend (hot-reload) | `docker-compose.dev.yml` | 1.5h | 1.2 |
| 1.8 | **Sandbox Docker image** — Python 3.11 image with numpy, pandas, matplotlib, requests | `docker/sandbox/Dockerfile.python` | 1.5h | — |
| 1.9 | **Sandbox manager** — Docker SDK wrapper: create container, execute code, capture output, cleanup, timeout/memory enforcement | `backend/app/sandbox/manager.py`, `executor.py`, `security.py` | 4h | 1.8 |
| 1.10 | **Sandbox integration tests** — Test execution, timeout, memory limit, stderr capture | `backend/tests/integration/test_sandbox_execution.py` | 2h | 1.9 |
| 1.11 | **Structured logging** — JSON logger with correlation IDs, request middleware | `backend/app/observability/logging.py` | 1h | 1.2 |
| 1.12 | **Unit test infrastructure** — conftest.py, mock DB, test fixtures | `backend/tests/conftest.py` | 1.5h | 1.3 |

---

### Phase 2: Agent System (Week 2) — ~25 hrs

| # | Task | Files | Time | Depends On |
|---|------|-------|------|------------|
| 2.1 | **LLM provider abstraction** — Unified interface wrapping OpenAI, Anthropic, Ollama with async calls | `backend/app/llm/providers.py` | 3h | 1.2 |
| 2.2 | **Task complexity classifier** — Prompt-based classification using embedding similarity or keyword heuristics, returning simple/medium/hard | `backend/app/llm/classifier.py` | 2h | 2.1 |
| 2.3 | **Model router** — Route to Llama-3 (Ollama) for simple, GPT-4/Claude for complex. Fallback logic if local model unavailable | `backend/app/llm/router.py` | 2h | 2.2 |
| 2.4 | **Cost tracker** — Per-call token counting, price lookup table (GPT-4: $30/$60 per 1M, Llama: $0), running totals per task | `backend/app/llm/cost_tracker.py` | 1.5h | 2.1 |
| 2.5 | **Base agent class** — Abstract class with `run()`, tracing hooks, structured output parsing, error handling | `backend/app/agents/base.py` | 1.5h | 2.1 |
| 2.6 | **Planner agent** — Implement planning with structured JSON output, subtask decomposition, dependency graph | `backend/app/agents/planner.py`, `prompts/planner.py` | 3h | 2.5 |
| 2.7 | **Coder agent** — Code generation per subtask, code merging for integration step, import deduplication | `backend/app/agents/coder.py`, `prompts/coder.py` | 3h | 2.5 |
| 2.8 | **Reviewer agent** — Error analysis, root cause extraction, fix suggestion with confidence score | `backend/app/agents/reviewer.py`, `prompts/reviewer.py` | 2.5h | 2.5 |
| 2.9 | **LangGraph orchestrator** — Full state machine: classify → plan → code → execute → review → repair loop → finalize/fail | `backend/app/agents/orchestrator.py` | 4h | 2.6–2.8, 1.9 |
| 2.10 | **Self-repair integration test** — End-to-end test with intentionally broken code, verify retry + fix | `backend/tests/integration/test_self_repair.py` | 2h | 2.9 |
| 2.11 | **Unit tests for all agents** — Mock LLM responses, test parsing, edge cases | `backend/tests/unit/test_planner.py`, `test_coder.py`, `test_reviewer.py`, `test_model_router.py` | 2.5h | 2.6–2.8 |

---

### Phase 3: Real-Time & Observability (Week 2–3) — ~12 hrs

| # | Task | Files | Time | Depends On |
|---|------|-------|------|------------|
| 3.1 | **WebSocket endpoint** — FastAPI WebSocket route, connection manager, event broadcasting | `backend/app/api/websocket.py` | 3h | 2.9 |
| 3.2 | **Agent streaming integration** — Hook agent callbacks to emit WS events (started, thinking, completed) | Modify `orchestrator.py` + `base.py` | 2.5h | 3.1 |
| 3.3 | **OpenTelemetry tracing** — Instrument agents, sandbox, DB calls with spans. Export to Jaeger | `backend/app/observability/tracing.py`, `metrics.py` | 3h | 2.9 |
| 3.4 | **Jaeger + OTel Collector** — Add to Docker Compose, configure collector pipeline | `docker/otel/`, update `docker-compose.yml` | 1.5h | 3.3 |
| 3.5 | **Cost dashboard data endpoint** — Aggregate cost/token data from traces table, return time series | `backend/app/api/` (extend) | 2h | 2.4 |

---

### Phase 4: Frontend (Week 3) — ~25 hrs

| # | Task | Files | Time | Depends On |
|---|------|-------|------|------------|
| 4.1 | **Next.js project init** — Create app with TypeScript, Tailwind, shadcn/ui setup | `frontend/` scaffolding | 1.5h | — |
| 4.2 | **Layout, sidebar, navigation** — App shell with sidebar nav, header, dark mode toggle | `frontend/src/components/layout/` | 2h | 4.1 |
| 4.3 | **REST API client** — Typed fetch wrapper for all backend endpoints | `frontend/src/lib/api.ts`, `types.ts` | 1.5h | 4.1 |
| 4.4 | **WebSocket hook** — `useWebSocket` custom hook: connect, reconnect, parse events, expose state | `frontend/src/hooks/useWebSocket.ts` | 2h | 4.1 |
| 4.5 | **Chat input component** — Auto-resizing textarea, submit button, keyboard shortcuts | `frontend/src/components/chat/ChatInput.tsx` | 1h | 4.2 |
| 4.6 | **Task stream / main chat view** — Scrollable message list, agent cards, code blocks, terminal output — all wired to WS events | `frontend/src/components/chat/TaskStream.tsx`, `ChatMessage.tsx`, `AgentCard.tsx` | 4h | 4.4 |
| 4.7 | **Code block component** — Monaco Editor (read-only), syntax highlighting, copy button, language label | `frontend/src/components/chat/CodeBlock.tsx` | 1.5h | 4.1 |
| 4.8 | **Agent flow diagram** — Interactive node graph using React Flow showing Planner→Coder→Executor→Reviewer with active state highlighting | `frontend/src/components/agents/AgentFlowDiagram.tsx` | 3h | 4.4 |
| 4.9 | **Terminal output component** — Styled `<pre>`, green stdout, red stderr, resource usage bar | `frontend/src/components/execution/TerminalOutput.tsx` | 1.5h | 4.6 |
| 4.10 | **Repair diff view** — Side-by-side: error + original code vs. fix + new code | `frontend/src/components/execution/RepairDiff.tsx` | 2h | 4.6 |
| 4.11 | **Benchmarks page** — Charts for pass@1, cost breakdown, model distribution, historical trends using Recharts | `frontend/src/app/benchmarks/page.tsx`, `components/benchmarks/*` | 3h | 4.3 |
| 4.12 | **History page** — Filterable task list, click-to-expand detail view with full agent traces | `frontend/src/app/history/page.tsx`, `components/history/*` | 2h | 4.3 |
| 4.13 | **Settings page** — Forms for API keys, routing thresholds, sandbox config, test-connection buttons | `frontend/src/app/settings/page.tsx`, `components/settings/*` | 2h | 4.3 |
| 4.14 | **Frontend Dockerfile + Compose** — Multi-stage build, add to docker-compose.yml | `frontend/Dockerfile`, update compose | 1h | 4.1 |

---

### Phase 5: Benchmarks & Polish (Week 4) — ~20 hrs

| # | Task | Files | Time | Depends On |
|---|------|-------|------|------------|
| 5.1 | **HumanEval loader** — Download dataset, parse problems, extract function signatures + test cases | `benchmarks/humaneval/loader.py` | 2h | — |
| 5.2 | **MBPP loader** — Download dataset, parse problems + assertions | `benchmarks/mbpp/loader.py` | 1.5h | — |
| 5.3 | **Benchmark runner** — Iterate problems, feed to orchestrator (with and without repair), collect results | `benchmarks/runner.py` | 3h | 2.9, 5.1, 5.2 |
| 5.4 | **pass@1 evaluator** — Calculate pass@1 for baseline and repair modes, generate comparison report | `benchmarks/humaneval/evaluator.py`, `benchmarks/mbpp/evaluator.py` | 2h | 5.3 |
| 5.5 | **Custom benchmark tasks** — Write 25 multi-step tasks (data processing, API mocking, algorithm puzzles, file I/O) | `benchmarks/custom/tasks.json`, `evaluator.py` | 3h | 5.3 |
| 5.6 | **Benchmark API endpoints** — Wire backend to trigger runs, store results, serve to frontend | `backend/app/api/benchmarks.py`, `services/benchmark_service.py` | 2h | 5.3 |
| 5.7 | **CI/CD pipeline** — GitHub Actions: lint (ruff), type-check (mypy), unit tests, build Docker images | `.github/workflows/ci.yml` | 2h | all |
| 5.8 | **Documentation** — Architecture doc, API doc, deployment guide, agent design doc | `docs/*` | 2h | all |
| 5.9 | **README** — Professional README with badges, screenshots, architecture diagram, quick start, benchmarks table | `README.md` | 1.5h | 5.8 |
| 5.10 | **Final integration test** — Full docker-compose up, submit task via API, verify WS stream, check DB records | `backend/tests/e2e/test_full_pipeline.py` | 2h | all |

---

## 10. Docker Compose Configuration

```yaml
# docker-compose.yml
version: "3.9"

services:
  # ── Backend API ──────────────────────────────────────────────
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://codeforge:codeforge@postgres:5432/codeforge
      - REDIS_URL=redis://redis:6379/0
      - OLLAMA_BASE_URL=http://ollama:11434
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
      - DOCKER_HOST=unix:///var/run/docker.sock
      - SANDBOX_IMAGE=codeforge-sandbox-python:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Docker-in-Docker for sandbox
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # ── Frontend ─────────────────────────────────────────────────
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

  # ── PostgreSQL ───────────────────────────────────────────────
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: codeforge
      POSTGRES_PASSWORD: codeforge
      POSTGRES_DB: codeforge
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U codeforge"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ── Redis ────────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ── Ollama (Local LLM) ──────────────────────────────────────
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia        # GPU passthrough (optional)
              count: all
              capabilities: [gpu]

  # ── OpenTelemetry Collector ──────────────────────────────────
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config", "/etc/otel/config.yml"]
    volumes:
      - ./docker/otel/otel-collector-config.yml:/etc/otel/config.yml
    ports:
      - "4317:4317"    # gRPC OTLP
      - "4318:4318"    # HTTP OTLP
    depends_on:
      - jaeger

  # ── Jaeger (Trace Visualization) ─────────────────────────────
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "14268:14268"  # Collector HTTP
    environment:
      - COLLECTOR_OTLP_ENABLED=true

volumes:
  pgdata:
  ollama_data:
```

---

## 11. Environment Variables

```bash
# .env.example

# ── Database ───────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://codeforge:codeforge@localhost:5432/codeforge
DATABASE_SYNC_URL=postgresql://codeforge:codeforge@localhost:5432/codeforge  # For Alembic

# ── Redis ──────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ── LLM Providers ─────────────────────────────────────────────
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
OLLAMA_BASE_URL=http://localhost:11434

# ── Model Routing ─────────────────────────────────────────────
DEFAULT_SIMPLE_MODEL=llama3:8b
DEFAULT_COMPLEX_MODEL=gpt-4
COMPLEXITY_SIMPLE_THRESHOLD=0.3
COMPLEXITY_COMPLEX_THRESHOLD=0.7

# ── Sandbox ────────────────────────────────────────────────────
SANDBOX_IMAGE=codeforge-sandbox-python:latest
SANDBOX_TIMEOUT_SECONDS=30
SANDBOX_MEMORY_LIMIT_MB=512
SANDBOX_CPU_LIMIT=1.0
SANDBOX_NETWORK_DISABLED=true
MAX_REPAIR_RETRIES=3

# ── Docker ─────────────────────────────────────────────────────
DOCKER_HOST=unix:///var/run/docker.sock

# ── Observability ──────────────────────────────────────────────
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=codeforge-backend
LOG_LEVEL=INFO
LOG_FORMAT=json

# ── Server ─────────────────────────────────────────────────────
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000
SECRET_KEY=change-me-in-production-use-openssl-rand-hex-32

# ── Frontend ───────────────────────────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## 12. Testing Strategy

### Test Pyramid

```
          ╱╲
         ╱  ╲          E2E Tests (2-3)
        ╱ E2E╲         Full docker-compose, real API calls
       ╱──────╲
      ╱        ╲       Integration Tests (8-10)
     ╱Integration╲     Real DB, real Docker, mock LLMs
    ╱──────────────╲
   ╱                ╲   Unit Tests (25-30)
  ╱   Unit Tests     ╲  Mock everything, test logic in isolation
 ╱────────────────────╲
```

### Unit Tests

| Test File | What It Tests |
|-----------|--------------|
| `test_planner.py` | Planner prompt construction, JSON output parsing, subtask dependency validation, edge cases (empty prompt, single-step task) |
| `test_coder.py` | Code generation parsing, import extraction, code merging logic, handling of malformed LLM output |
| `test_reviewer.py` | Error analysis parsing, confidence scoring, fix suggestion extraction, timeout error handling |
| `test_model_router.py` | Complexity → model mapping, fallback when Ollama unavailable, threshold boundary behavior |
| `test_cost_tracker.py` | Token counting accuracy, cost calculation per model, cumulative tracking |
| `test_sandbox.py` | Command construction, timeout enforcement (mock Docker), security validation (blocked commands) |

**Approach:** All LLM calls mocked with canned responses. Use `pytest-asyncio` for async tests. Parameterize with `@pytest.mark.parametrize` for edge cases.

### Integration Tests

| Test File | What It Tests |
|-----------|--------------|
| `test_orchestrator.py` | Full LangGraph flow with mock LLM but real state machine transitions |
| `test_sandbox_execution.py` | Real Docker execution: valid Python, syntax errors, timeouts, memory limits, stderr capture |
| `test_self_repair.py` | Inject a known failing code → verify reviewer triggers → verify fix applied → verify re-execution succeeds |

**Approach:** Use real PostgreSQL (test database), real Redis, real Docker. Mock only LLM API calls.

### E2E Tests

| Test File | What It Tests |
|-----------|--------------|
| `test_full_pipeline.py` | POST task → WS connect → receive all events → verify DB records → verify final output |

**Approach:** Full `docker-compose up`, real HTTP/WS calls, LLM calls either mocked or use a cheap model.

### Frontend Tests (Optional but recommended)

- Component tests with `@testing-library/react` for critical components (TaskStream, AgentFlowDiagram)
- No full E2E browser tests (Playwright) unless time permits

### Running Tests

```bash
# Unit tests (fast, no Docker needed)
make test-unit

# Integration tests (needs Docker)
make test-integration

# E2E (needs full stack running)
make test-e2e

# All tests with coverage
make test-all
```

---

## 13. Benchmark Evaluation Plan

### HumanEval Benchmark

**Dataset:** 164 hand-written Python problems from OpenAI. Each has a function signature, docstring, and test cases.

**Protocol:**
1. For each problem, feed the docstring + signature to the agent pipeline
2. Capture the generated code
3. Run the code against the test cases in the sandbox
4. Record pass/fail

**Metrics:**
- **pass@1 (baseline):** Percentage of problems solved on the first attempt (no repair)
- **pass@1 (with repair):** Percentage solved after allowing up to 3 repair attempts
- **Repair lift:** `pass@1_repair - pass@1_baseline` — the delta that proves self-repair value

**Expected ballpark targets:**
- Baseline (GPT-4): ~65–75% pass@1
- With repair: ~80–85% pass@1
- Repair lift: ~10–15 percentage points

### MBPP Benchmark

**Dataset:** 500 crowd-sourced Python problems with 3 test assertions each.

**Protocol:** Same as HumanEval. Feed task description → generate code → execute assertions.

**Expected targets:**
- Baseline: ~70–78% pass@1
- With repair: ~82–88% pass@1

### Custom Multi-Step Benchmark

**25 hand-crafted tasks** spanning:

| Category | Count | Example |
|----------|-------|---------|
| Data processing | 5 | Read CSV, pivot, export summary |
| API interaction | 4 | Mock API call, parse JSON, handle errors |
| Algorithm implementation | 5 | Graph traversal, dynamic programming |
| File I/O | 4 | Read/write files, parse config |
| Multi-function composition | 4 | Chain 3+ functions with error handling |
| Edge case handling | 3 | Empty inputs, unicode, large datasets |

**Evaluation criteria per task:**
- Functional correctness (all assertions pass)
- Error handling (doesn't crash on edge cases)
- Code quality (lint-clean, has docstrings)

### Metrics Dashboard

The benchmarks page displays:

1. **Pass rate bar chart:** HumanEval and MBPP, each showing baseline vs. repair bars
2. **Repair effectiveness:** Scatter plot of problems — X axis = difficulty, Y axis = retries needed
3. **Cost analysis:** Total cost for each benchmark run, cost per solved problem
4. **Model routing distribution:** How many problems went to Llama-3 vs. GPT-4
5. **Time distribution:** Histogram of per-problem solve time

### Running Benchmarks

```bash
# Run HumanEval (takes ~20-40 min depending on model)
make benchmark-humaneval

# Run MBPP
make benchmark-mbpp

# Run custom tasks
make benchmark-custom

# Run all with comparison report
make benchmark-all
```

---

## 14. README Structure

```markdown
# 🔧 CodeForge — AI Code Agent with Self-Repair

[![CI](badge)](link) [![Python](badge)](link) [![License](badge)](link)

> A multi-agent AI system that generates, executes, tests, and self-repairs
> code from natural language instructions.

![Architecture Diagram](docs/images/architecture-diagram.png)

## ✨ Key Features

- **Multi-agent orchestration** via LangGraph state machine
- **Self-repair loop** — automatic error analysis and fix application (up to 3 retries)
- **Intelligent model routing** — simple tasks → Llama-3 (free), complex → GPT-4
- **Secure Docker sandbox** — isolated code execution with resource limits
- **Real-time streaming UI** — watch agents think, code, execute, and repair
- **Full observability** — OpenTelemetry tracing, Jaeger visualization, cost tracking
- **Rigorous benchmarks** — HumanEval (XX% pass@1), MBPP (XX% pass@1)

## 📊 Benchmark Results

| Benchmark | Baseline pass@1 | With Self-Repair | Repair Lift |
|-----------|----------------|------------------|-------------|
| HumanEval (164) | XX.X% | XX.X% | +XX.X% |
| MBPP (500) | XX.X% | XX.X% | +XX.X% |
| Custom (25) | XX.X% | XX.X% | +XX.X% |

## 🏗️ Architecture

[Brief description + link to detailed architecture doc]

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key (or Ollama for local-only mode)

### Setup
    ```bash
    git clone https://github.com/user/codeforge.git
    cd codeforge
    cp .env.example .env
    # Edit .env with your API keys
    docker-compose up --build
    ```

    Open http://localhost:3000

## 🖥️ Screenshots

[Chat interface, Agent flow, Benchmark dashboard, Trace viewer]

## 🔬 Technical Deep Dive

- [Agent Design & Prompts](docs/agent-design.md)
- [LangGraph State Machine](docs/architecture.md#state-machine)
- [Sandbox Security Model](docs/architecture.md#sandbox)
- [Model Routing Strategy](docs/architecture.md#model-routing)
- [Benchmark Methodology](docs/architecture.md#benchmarks)

## 📁 Project Structure

[Abbreviated tree]

## 🧪 Testing

    ```bash
    make test-unit          # Fast, no Docker
    make test-integration   # Needs Docker
    make test-all           # Full suite with coverage
    ```

## 🛠️ Tech Stack

[Table of backend, frontend, infra, LLMs]

## 📈 Cost Optimization

[Brief description of routing strategy and savings]

## 🔮 Future Work

- Multi-language support (JavaScript, Rust, Go)
- Collaborative multi-turn conversations
- Fine-tuned local model for code repair
- RAG integration for domain-specific code patterns

## 📄 License

MIT
```

---

## Appendix: Interview Talking Points

When discussing this project in a 45-minute technical interview, structure your narrative around these pillars:

**System Design (10 min):** Why multi-agent vs. single-prompt? How does LangGraph manage state? How do you handle partial failures? What are the trade-offs of Docker sandboxing vs. other isolation approaches?

**Cost Optimization (5 min):** How does the model router work? What's the classifier's accuracy? What's the actual cost saving? How would you add a new model tier?

**Self-Repair (10 min):** This is your differentiator. Walk through: how does the reviewer identify root causes? Why exponential backoff? Why a confidence-based escape hatch? Show the benchmark data: repair lift numbers.

**Observability (5 min):** Why OpenTelemetry over custom logging? How do you correlate traces across agents? What metrics matter most? How would you set up alerting?

**Benchmarks (10 min):** Why HumanEval and MBPP? How do you ensure fair evaluation (no data leakage from prompts)? What does your custom benchmark add that HumanEval doesn't? How do your numbers compare to published baselines?

**Production Concerns (5 min):** How would you scale this? (Horizontal: stateless API + task queue. Vertical: GPU for local models.) How would you handle prompt injection in user inputs? What about concurrent users?
