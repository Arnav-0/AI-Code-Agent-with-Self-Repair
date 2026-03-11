# Architecture

## System Overview

CodeForge is an AI-powered code generation system with an autonomous self-repair loop. It accepts a natural-language task description, decomposes it into subtasks, generates code, executes it in a sandboxed environment, and automatically repairs failures using an LLM reviewer.

```
                    ┌─────────────────────────────────────────────┐
                    │               CodeForge System               │
                    │                                              │
  User Prompt ─────►│  FastAPI Backend  ◄──── WebSocket Events ───►│ Next.js Frontend
                    │        │                                      │
                    │        ▼                                      │
                    │  LangGraph State Machine                      │
                    │  ┌──────────────────────────────────────┐    │
                    │  │  classify → plan → code → execute    │    │
                    │  │       ↑                   │          │    │
                    │  │  apply_fix ← review ←─── fail?      │    │
                    │  │       │                   │          │    │
                    │  │    (retry)             finalize      │    │
                    │  └──────────────────────────────────────┘    │
                    │        │                                      │
                    │   ┌────┴────┐    ┌──────────┐               │
                    │   │  LLM    │    │  Docker  │               │
                    │   │ Router  │    │ Sandbox  │               │
                    │   └────┬────┘    └──────────┘               │
                    │   ┌────┴──────────┐                         │
                    │   │ Ollama / OAI  │                         │
                    │   │ / Anthropic   │                         │
                    │   └───────────────┘                         │
                    │                                              │
                    │  PostgreSQL + Redis + Jaeger (OTel)         │
                    └─────────────────────────────────────────────┘
```

## Components

### Backend (`backend/`)
- **FastAPI** application with async SQLAlchemy and asyncpg (PostgreSQL)
- 19 REST endpoints + WebSocket for real-time task progress
- Alembic migrations for schema management
- OpenTelemetry instrumentation for distributed tracing

### Frontend (`frontend/`)
- **Next.js 14** (App Router) with TypeScript
- Real-time task dashboard via WebSocket
- Benchmark results visualization

### Agents (`backend/app/agents/`)
The core intelligence layer — four specialized agents that form the self-repair pipeline:
1. **PlannerAgent** — decomposes the task into a DAG of subtasks
2. **CoderAgent** — implements each subtask with syntax validation
3. **ReviewerAgent** — analyzes failures and generates fixes
4. **Orchestrator** — LangGraph state machine coordinating all agents

### Sandbox (`backend/app/sandbox/`)
- Docker-based isolated execution environment
- Configurable memory/CPU limits and execution timeout
- Network disabled by default to prevent exfiltration
- Code security validation before execution

### Observability (`backend/app/observability/`)
- Structured JSON logging with correlation IDs
- OpenTelemetry traces exported to Jaeger
- Custom metrics: cost, latency, retry counts

## Data Flow

1. User submits a prompt via POST `/api/v1/tasks/`
2. Task is persisted to PostgreSQL with `status=pending`
3. Orchestrator starts as a background asyncio task
4. State machine transitions: `classify → plan → code → execute`
5. On success: `finalize` — task marked `completed`, code saved
6. On failure: `review → apply_fix → execute` (retried up to `max_retries`)
7. After max retries or low-confidence review: `fail`
8. WebSocket broadcasts each state transition to connected clients

## State Machine

```
classify ──► plan ──► code ──► execute
                                  │
                        ┌─────────┴──────────┐
                        │ success?            │ failure?
                        ▼                     ▼
                    finalize              review
                                              │
                                    ┌─────────┴──────────┐
                                    │ retry?              │ abort?
                                    ▼                     ▼
                                apply_fix               fail
                                    │
                                    └──────► execute (loop)
```

**Abort conditions:**
- `retry_count >= max_retries`
- reviewer confidence < 0.3 after 2+ attempts

## Model Routing Strategy

The `ModelRouter` classifies each task by complexity and selects the appropriate LLM:

| Complexity Score | Model          | Rationale                    |
|-----------------|----------------|------------------------------|
| < 0.3 (simple)  | Ollama local   | Fast, free, sufficient       |
| 0.3–0.7 (medium)| Ollama local   | Still local                  |
| > 0.7 (complex) | OpenAI/Anthropic | Higher quality for hard tasks|

Fallback chain: primary → Ollama on API errors.

## Sandbox Security Model

- Docker containers are ephemeral (destroyed after each run)
- No network access (unless explicitly enabled)
- Memory limited (default 512 MB), CPU limited (default 1.0 core)
- Execution timeout enforced (default 30s)
- Code is statically validated before execution (banned imports check)
- Containers run as non-root user

## Cost Optimization

- Local Ollama handles simple tasks at zero cost
- Cloud LLM usage tracked per request (tokens × per-token price)
- Cumulative cost saved vs always-cloud is calculated and stored
- Benchmark runs track cost per problem for ROI analysis

## Technology Choices

| Technology         | Reason                                              |
|--------------------|-----------------------------------------------------|
| FastAPI            | Async, high performance, excellent OpenAPI support  |
| LangGraph          | First-class state machine with conditional edges    |
| SQLAlchemy async   | Type-safe ORM with PostgreSQL async support         |
| Docker SDK         | Programmatic sandbox container management           |
| OpenTelemetry      | Vendor-neutral distributed tracing standard         |
| Next.js App Router | Server components + streaming for modern UX         |
| Pydantic v2        | Fast validation, IDE-friendly type hints            |
