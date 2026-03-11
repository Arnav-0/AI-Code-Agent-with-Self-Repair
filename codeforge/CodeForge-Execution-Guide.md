# CodeForge — Complete Execution Guide (Claude Code CLI)

> **How to use:** Copy-paste each command block into your terminal. Each task is self-contained.
> Run them in order within each phase. Tasks marked **[PARALLEL]** can run simultaneously in separate terminals.
> Every task includes built-in validation — it won't finish until tests pass.

---

## PRE-REQUISITES

```bash
# Run this ONCE before starting
mkdir -p ~/codeforge && cd ~/codeforge
git init
```

---

## PHASE 1: Foundation (Tasks 1.1 – 1.12)

---

### TASK 1.1 — Project Scaffolding + Monorepo Init

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)

Create the complete monorepo scaffolding for this project. Do the following:

1. Create the full directory structure:

codeforge/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py (empty placeholder with comment)
│   │   ├── config.py (empty placeholder)
│   │   ├── dependencies.py
│   │   ├── api/__init__.py
│   │   ├── agents/__init__.py
│   │   ├── agents/prompts/__init__.py
│   │   ├── llm/__init__.py
│   │   ├── sandbox/__init__.py
│   │   ├── models/__init__.py
│   │   ├── services/__init__.py
│   │   ├── observability/__init__.py
│   │   └── db/__init__.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── unit/__init__.py
│   │   ├── integration/__init__.py
│   │   └── e2e/__init__.py
│   ├── alembic/
│   │   └── versions/.gitkeep
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   └── .gitkeep
├── docker/
│   ├── sandbox/.gitkeep
│   └── otel/.gitkeep
├── benchmarks/
│   ├── __init__.py
│   ├── humaneval/__init__.py
│   ├── mbpp/__init__.py
│   ├── custom/__init__.py
│   └── results/.gitkeep
├── docs/
│   └── .gitkeep
├── .github/workflows/.gitkeep
├── .gitignore
├── .env.example
├── Makefile
├── LICENSE (MIT)
└── README.md

2. Create pyproject.toml with:
   - Project name: codeforge
   - Python >= 3.11
   - Dependencies: fastapi>=0.104.0, uvicorn[standard]>=0.24.0, sqlalchemy[asyncio]>=2.0.23, asyncpg>=0.29.0, alembic>=1.13.0, pydantic>=2.5.0, pydantic-settings>=2.1.0, langchain>=0.1.0, langgraph>=0.0.40, langchain-openai>=0.0.5, langchain-anthropic>=0.1.0, docker>=7.0.0, redis>=5.0.0, opentelemetry-api>=1.22.0, opentelemetry-sdk>=1.22.0, opentelemetry-instrumentation-fastapi>=0.43b0, opentelemetry-exporter-otlp>=1.22.0, httpx>=0.25.0
   - Dev dependencies: pytest>=7.4.0, pytest-asyncio>=0.23.0, pytest-cov>=4.1.0, ruff>=0.1.0, mypy>=1.7.0
   - Ruff config: line-length=100, target-version=py311
   - Mypy config: strict mode

3. Create requirements.txt that mirrors pyproject.toml deps (for Docker builds)

4. Create .gitignore covering: Python, Node.js, Docker, .env, __pycache__, .mypy_cache, .ruff_cache, .pytest_cache, benchmarks/results/*, benchmarks/*/data/*, node_modules, .next, dist

5. Create .env.example with ALL these variables (with placeholder values):
   DATABASE_URL=postgresql+asyncpg://codeforge:codeforge@localhost:5432/codeforge
   DATABASE_SYNC_URL=postgresql://codeforge:codeforge@localhost:5432/codeforge
   REDIS_URL=redis://localhost:6379/0
   OPENAI_API_KEY=sk-your-key-here
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   OLLAMA_BASE_URL=http://localhost:11434
   DEFAULT_SIMPLE_MODEL=llama3:8b
   DEFAULT_COMPLEX_MODEL=gpt-4
   COMPLEXITY_SIMPLE_THRESHOLD=0.3
   COMPLEXITY_COMPLEX_THRESHOLD=0.7
   SANDBOX_IMAGE=codeforge-sandbox-python:latest
   SANDBOX_TIMEOUT_SECONDS=30
   SANDBOX_MEMORY_LIMIT_MB=512
   SANDBOX_CPU_LIMIT=1.0
   SANDBOX_NETWORK_DISABLED=true
   MAX_REPAIR_RETRIES=3
   DOCKER_HOST=unix:///var/run/docker.sock
   OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
   OTEL_SERVICE_NAME=codeforge-backend
   LOG_LEVEL=INFO
   LOG_FORMAT=json
   HOST=0.0.0.0
   PORT=8000
   CORS_ORIGINS=http://localhost:3000
   SECRET_KEY=change-me-in-production

6. Create Makefile with targets:
   - install: pip install -e '.[dev]'
   - dev: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   - test-unit: pytest tests/unit -v --tb=short
   - test-integration: pytest tests/integration -v --tb=short
   - test-e2e: pytest tests/e2e -v --tb=short
   - test-all: pytest --cov=app --cov-report=term-missing
   - lint: ruff check app/ tests/
   - format: ruff format app/ tests/
   - type-check: mypy app/
   - migrate: alembic upgrade head
   - migration: alembic revision --autogenerate -m
   - docker-up: docker-compose up --build -d
   - docker-down: docker-compose down
   - benchmark-humaneval: python -m benchmarks.runner --type humaneval
   - benchmark-mbpp: python -m benchmarks.runner --type mbpp
   - benchmark-custom: python -m benchmarks.runner --type custom
   - benchmark-all: python -m benchmarks.runner --type all
   - clean: find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; find . -type f -name '*.pyc' -delete

7. Create a minimal README.md with project title and 'Setup instructions coming soon'

VALIDATION after creating everything:
- Run: find . -name '*.py' -path '*/app/*' | head -20 (should show all __init__.py files)
- Run: cat pyproject.toml | head -5 (should show [project] with name)
- Run: cat .env.example | wc -l (should be 20+ lines)
- Run: make --dry-run install (should show pip install command)
- Run: cat .gitignore | grep __pycache__ (should find it)
Print 'TASK 1.1 COMPLETE — Scaffolding verified' when all validations pass.
"
```

---

### TASK 1.2 — FastAPI Backend Skeleton

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: Monorepo scaffolding exists. pyproject.toml has FastAPI, uvicorn, pydantic-settings deps.

Create the FastAPI application skeleton with proper app factory pattern.

1. Create backend/app/config.py:
   - Use pydantic_settings.BaseSettings
   - Class Settings with ALL env vars from .env.example as typed fields
   - Nested model classes: DatabaseSettings, RedisSettings, LLMSettings, SandboxSettings, ObservabilitySettings, ServerSettings
   - Validator for DATABASE_URL format
   - @lru_cache get_settings() function
   - All fields have sensible defaults matching .env.example

2. Create backend/app/main.py:
   - create_app() factory function returning FastAPI instance
   - Lifespan context manager (async) that:
     - Logs 'Starting CodeForge backend...'
     - Yields
     - Logs 'Shutting down CodeForge backend...'
   - CORS middleware configured from settings.CORS_ORIGINS (split by comma)
   - Include the main api router with prefix /api/v1
   - Root endpoint GET / returning {name: 'CodeForge', version: '0.1.0', status: 'running'}
   - app = create_app() at module level for uvicorn

3. Create backend/app/api/__init__.py — empty

4. Create backend/app/api/router.py:
   - Main APIRouter that aggregates all sub-routers
   - Import and include: tasks_router, history_router, benchmarks_router, settings_router
   - For now, create STUB routers for each (just the router object, no endpoints yet)

5. Create backend/app/api/health.py:
   - GET /health endpoint returning {status: 'healthy', database: 'unknown', redis: 'unknown', docker: 'unknown'}
   - Include this in the main router

6. Create backend/app/dependencies.py:
   - get_settings dependency (returns Settings instance)
   - Placeholder get_db dependency (returns None for now, will be replaced)

VALIDATION:
- cd backend && python -c 'from app.config import get_settings; s = get_settings(); print(f\"Settings loaded: {s.HOST}:{s.PORT}\")' — should print 0.0.0.0:8000
- cd backend && python -c 'from app.main import app; print(f\"App created: {app.title}\")' — should show CodeForge
- cd backend && python -c 'from app.api.router import router; print(f\"Routes: {len(router.routes)}\")' — should show routes registered
- cd backend && python -m ruff check app/ --select E,F — should pass with no errors
Print 'TASK 1.2 COMPLETE — FastAPI skeleton verified' when all pass.
"
```

---

### TASK 1.3 — Database Models + Alembic Migrations

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: FastAPI app exists in backend/app/. Config has DATABASE_URL. Dependencies: sqlalchemy[asyncio], asyncpg, alembic.

Create the complete database layer with all table models and Alembic migration setup.

1. Create backend/app/db/__init__.py — empty

2. Create backend/app/db/session.py:
   - Create async engine from settings.DATABASE_URL using create_async_engine
   - Create async_sessionmaker bound to engine
   - async get_db() generator that yields AsyncSession with proper cleanup
   - Engine config: pool_size=10, max_overflow=20, pool_recycle=3600, echo=False (echo=True if LOG_LEVEL=DEBUG)

3. Create backend/app/models/__init__.py — import all models

4. Create backend/app/models/database.py with these SQLAlchemy ORM models using DeclarativeBase:

   Base class with:
   - id: Mapped[UUID] primary key, default=uuid4
   - created_at: Mapped[datetime] with timezone, server_default=func.now()

   class Task(Base):
     __tablename__ = 'tasks'
     - prompt: Mapped[str] = mapped_column(Text, nullable=False)
     - status: Mapped[str] = mapped_column(String(20), nullable=False, default='pending', index=True)
       # Values: pending, planning, coding, executing, reviewing, repairing, completed, failed
     - complexity: Mapped[Optional[str]] = mapped_column(String(10))  # simple, medium, hard
     - model_used: Mapped[Optional[str]] = mapped_column(String(50))
     - plan: Mapped[Optional[dict]] = mapped_column(JSON)
     - final_code: Mapped[Optional[str]] = mapped_column(Text)
     - final_output: Mapped[Optional[str]] = mapped_column(Text)
     - total_cost_usd: Mapped[Decimal] = mapped_column(Numeric(10,6), default=0)
     - total_time_ms: Mapped[Optional[int]]
     - retry_count: Mapped[int] = mapped_column(default=0)
     - error_message: Mapped[Optional[str]] = mapped_column(Text)
     - updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
     - Relationship: traces = relationship('AgentTrace', back_populates='task', cascade='all, delete-orphan')

   class AgentTrace(Base):
     __tablename__ = 'agent_traces'
     - task_id: Mapped[UUID] = mapped_column(ForeignKey('tasks.id', ondelete='CASCADE'), index=True)
     - agent_type: Mapped[str] = mapped_column(String(20), nullable=False)  # planner, coder, executor, reviewer
     - input_data: Mapped[dict] = mapped_column(JSON, nullable=False)
     - output_data: Mapped[Optional[dict]] = mapped_column(JSON)
     - reasoning: Mapped[Optional[str]] = mapped_column(Text)
     - tokens_used: Mapped[int] = mapped_column(default=0)
     - cost_usd: Mapped[Decimal] = mapped_column(Numeric(10,6), default=0)
     - duration_ms: Mapped[Optional[int]]
     - step_order: Mapped[int] = mapped_column(nullable=False)
     - Relationships: task, execution_results

   class ExecutionResult(Base):
     __tablename__ = 'execution_results'
     - trace_id: Mapped[UUID] = mapped_column(ForeignKey('agent_traces.id', ondelete='CASCADE'), index=True)
     - exit_code: Mapped[int] = mapped_column(nullable=False)
     - stdout: Mapped[str] = mapped_column(Text, default='')
     - stderr: Mapped[str] = mapped_column(Text, default='')
     - execution_time_ms: Mapped[int] = mapped_column(nullable=False)
     - memory_used_mb: Mapped[Optional[float]]
     - container_id: Mapped[Optional[str]] = mapped_column(String(64))
     - retry_number: Mapped[int] = mapped_column(default=0)

   class BenchmarkRun(Base):
     __tablename__ = 'benchmark_runs'
     - benchmark_type: Mapped[str] = mapped_column(String(20), nullable=False)  # humaneval, mbpp, custom
     - model_config_json: Mapped[dict] = mapped_column(JSON)
     - total_problems: Mapped[int]
     - passed: Mapped[int]
     - pass_at_1: Mapped[float]
     - pass_at_1_repair: Mapped[Optional[float]]
     - avg_retries: Mapped[Optional[float]]
     - total_cost_usd: Mapped[Decimal] = mapped_column(Numeric(10,6), default=0)
     - total_time_ms: Mapped[Optional[int]]
     - Relationship: results

   class BenchmarkResult(Base):
     __tablename__ = 'benchmark_results'
     - run_id: Mapped[UUID] = mapped_column(ForeignKey('benchmark_runs.id', ondelete='CASCADE'), index=True)
     - problem_id: Mapped[str] = mapped_column(String(50), nullable=False)
     - passed: Mapped[bool] = mapped_column(default=False)
     - passed_after_repair: Mapped[bool] = mapped_column(default=False)
     - retries_used: Mapped[int] = mapped_column(default=0)
     - generated_code: Mapped[Optional[str]] = mapped_column(Text)
     - error_message: Mapped[Optional[str]] = mapped_column(Text)
     - cost_usd: Mapped[Decimal] = mapped_column(Numeric(10,6), default=0)
     - time_ms: Mapped[Optional[int]]

   class AppSettings(no Base inheritance, standalone):
     __tablename__ = 'app_settings'
     - key: Mapped[str] = mapped_column(String(100), primary_key=True)
     - value: Mapped[dict] = mapped_column(JSON)
     - updated_at: Mapped[datetime]

5. Create backend/app/db/repository.py:
   - Generic async CRUD repository class
   - Methods: create(model, **kwargs), get_by_id(model, id), get_all(model, filters, pagination), update(model, id, **kwargs), delete(model, id)
   - All methods use async session properly

6. Setup Alembic:
   - Create backend/alembic.ini pointing to backend/alembic/
   - Create backend/alembic/env.py configured for:
     - async mode (run_async_migrations)
     - Import Base.metadata from app.models.database
     - Read DATABASE_SYNC_URL from environment
   - Create initial migration: 'init_all_tables'
   - The migration file in alembic/versions/ should create ALL tables

VALIDATION:
- cd backend && python -c 'from app.models.database import Base, Task, AgentTrace, ExecutionResult, BenchmarkRun, BenchmarkResult; print(f\"Tables: {list(Base.metadata.tables.keys())}\")' — should list all 6 tables
- cd backend && python -c 'from app.models.database import Task; t = Task.__table__; print(f\"Task columns: {[c.name for c in t.columns]}\")' — should show all columns
- cd backend && python -c 'from app.db.session import get_db; print(\"Session factory ready\")' — should not error
- cd backend && ls alembic/versions/*.py | head -1 — should find migration file
- cd backend && python -c 'from app.db.repository import CRUDRepository; print(\"Repository imported\")' — should work
- cd backend && python -m ruff check app/ --select E,F — should pass
Print 'TASK 1.3 COMPLETE — Database layer verified' when all pass.
"
```

---

### TASK 1.4 — Pydantic Request/Response Schemas

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: Database models exist in backend/app/models/database.py with tables: tasks, agent_traces, execution_results, benchmark_runs, benchmark_results, app_settings.

Create comprehensive Pydantic v2 schemas for all API request/response models.

Create backend/app/models/schemas.py with:

1. Base schemas:
   - BaseSchema(BaseModel) with model_config = ConfigDict(from_attributes=True)
   - PaginationParams: page(int, ge=1, default=1), per_page(int, ge=1, le=100, default=20)
   - PaginatedResponse[T](BaseModel, Generic[T]): items: list[T], total: int, page: int, per_page: int, total_pages: int

2. Task schemas:
   - TaskCreate: prompt(str, min_length=1, max_length=10000)
   - TaskResponse: id(UUID), prompt, status, complexity, model_used, total_cost_usd(float), total_time_ms, retry_count, error_message, created_at(datetime), updated_at(datetime)
   - TaskDetail(TaskResponse): plan(dict|None), final_code(str|None), final_output(str|None), traces(list[AgentTraceResponse])
   - TaskListResponse = PaginatedResponse[TaskResponse]

3. Agent trace schemas:
   - AgentTraceResponse: id(UUID), task_id(UUID), agent_type(str), input_data(dict), output_data(dict|None), reasoning(str|None), tokens_used(int), cost_usd(float), duration_ms(int|None), step_order(int), created_at(datetime)

4. Execution schemas:
   - ExecutionResultResponse: id(UUID), trace_id(UUID), exit_code(int), stdout(str), stderr(str), execution_time_ms(int), memory_used_mb(float|None), container_id(str|None), retry_number(int), created_at(datetime)

5. Benchmark schemas:
   - BenchmarkRunRequest: type(Literal['humaneval','mbpp','custom']), with_repair(bool, default=True)
   - BenchmarkRunResponse: id(UUID), benchmark_type, total_problems, passed, pass_at_1(float), pass_at_1_repair(float|None), avg_retries(float|None), total_cost_usd(float), total_time_ms(int|None), created_at
   - BenchmarkResultResponse: id(UUID), run_id(UUID), problem_id, passed, passed_after_repair, retries_used, generated_code(str|None), error_message(str|None), cost_usd(float), time_ms(int|None)
   - BenchmarkRunDetail(BenchmarkRunResponse): results(list[BenchmarkResultResponse])

6. Settings schemas:
   - LLMProviderSettings: openai_api_key(str|None), anthropic_api_key(str|None), ollama_endpoint(str, default='http://localhost:11434')
   - RoutingSettings: simple_threshold(float, ge=0, le=1, default=0.3), complex_threshold(float, ge=0, le=1, default=0.7), simple_model(str, default='llama3:8b'), complex_model(str, default='gpt-4')
   - SandboxSettingsSchema: timeout_seconds(int, ge=5, le=120, default=30), memory_limit_mb(int, ge=128, le=2048, default=512), max_retries(int, ge=0, le=10, default=3)
   - AppSettingsResponse: llm(LLMProviderSettings), routing(RoutingSettings), sandbox(SandboxSettingsSchema)
   - AppSettingsUpdate: llm(LLMProviderSettings|None), routing(RoutingSettings|None), sandbox(SandboxSettingsSchema|None) — all optional for partial updates
   - ConnectionTestRequest: provider(Literal['openai','anthropic','ollama']), api_key(str|None), endpoint(str|None)
   - ConnectionTestResponse: success(bool), message(str), latency_ms(int|None)

7. WebSocket schemas:
   - WSEvent: event(str), timestamp(datetime), data(dict)
   - WSAgentStarted: agent_type(str), step_order(int), input_summary(str)
   - WSAgentThinking: agent_type(str), chunk(str)
   - WSAgentCompleted: agent_type(str), output_summary(str), tokens_used(int), cost_usd(float), duration_ms(int)
   - WSCodeGenerated: code(str), language(str), subtask_index(int)
   - WSExecutionStarted: container_id(str|None), retry_number(int)
   - WSExecutionOutput: stream(Literal['stdout','stderr']), line(str)
   - WSExecutionCompleted: exit_code(int), execution_time_ms(int), memory_used_mb(float|None)
   - WSRepairStarted: retry_number(int), error_summary(str)
   - WSRepairFixApplied: fixed_code(str), change_summary(str)
   - WSTaskCompleted: final_code(str), final_output(str), total_cost(float), total_time_ms(int), retry_count(int)
   - WSTaskFailed: error_message(str), retry_count(int)

8. History filter schemas:
   - HistoryFilter: status(str|None), search(str|None), date_from(datetime|None), date_to(datetime|None), sort_by(str, default='created_at'), order(Literal['asc','desc'], default='desc')

VALIDATION:
- cd backend && python -c '
from app.models.schemas import (
    TaskCreate, TaskResponse, TaskDetail, TaskListResponse,
    AgentTraceResponse, ExecutionResultResponse,
    BenchmarkRunRequest, BenchmarkRunResponse, BenchmarkRunDetail,
    AppSettingsResponse, AppSettingsUpdate, ConnectionTestRequest,
    WSEvent, WSAgentStarted, WSTaskCompleted, WSTaskFailed,
    HistoryFilter, PaginationParams
)
# Test creation
t = TaskCreate(prompt=\"Write hello world\")
print(f\"TaskCreate valid: {t.prompt}\")
# Test validation
try:
    TaskCreate(prompt=\"\")
except Exception as e:
    print(f\"Validation works: {type(e).__name__}\")
# Test settings
from app.models.schemas import RoutingSettings
r = RoutingSettings()
print(f\"Defaults work: simple_threshold={r.simple_threshold}\")
print(\"All schemas imported and validated\")
'
- cd backend && python -m ruff check app/models/schemas.py --select E,F — should pass
Print 'TASK 1.4 COMPLETE — All Pydantic schemas verified' when all pass.
"
```

---

### TASK 1.5 — REST API Endpoints (Tasks, History, Settings)

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: FastAPI app in backend/app/main.py. Database models in backend/app/models/database.py. Pydantic schemas in backend/app/models/schemas.py. DB session in backend/app/db/session.py. Repository in backend/app/db/repository.py.

Create ALL REST API endpoints. These should work with the database but the agent orchestration will be added later — for now, task submission creates a DB record and returns immediately.

1. Create backend/app/services/task_service.py:
   - TaskService class taking AsyncSession
   - create_task(prompt: str) -> Task: creates task with status='pending', returns it
   - get_task(task_id: UUID) -> Task|None: fetch with traces eagerly loaded
   - get_task_traces(task_id: UUID) -> list[AgentTrace]
   - delete_task(task_id: UUID) -> bool
   - list_tasks(filters: HistoryFilter, pagination: PaginationParams) -> tuple[list[Task], int]: supports filtering by status, search in prompt, date range, sorting, pagination

2. Create backend/app/services/settings_service.py:
   - SettingsService class taking AsyncSession
   - get_all() -> AppSettingsResponse: reads from app_settings table, returns defaults if no rows
   - update(settings: AppSettingsUpdate) -> AppSettingsResponse: upserts changed keys
   - test_connection(request: ConnectionTestRequest) -> ConnectionTestResponse: for now returns {success: True, message: 'Connection test not yet implemented', latency_ms: None}

3. Create backend/app/services/benchmark_service.py:
   - BenchmarkService class taking AsyncSession
   - list_runs() -> list[BenchmarkRun]
   - get_run(run_id: UUID) -> BenchmarkRunDetail|None
   - trigger_run(request: BenchmarkRunRequest) -> BenchmarkRun: creates a BenchmarkRun record with status data, returns it (actual execution will be added later)

4. Create backend/app/api/tasks.py:
   - Router with prefix '/tasks', tag 'Tasks'
   - POST / : create task, return TaskResponse (201)
   - GET /{task_id} : get task detail, return TaskDetail (404 if not found)
   - GET /{task_id}/traces : get traces, return list[AgentTraceResponse]
   - DELETE /{task_id} : delete task, return {success: true} (404 if not found)

5. Create backend/app/api/history.py:
   - Router with prefix '/history', tag 'History'
   - GET / : list tasks with query params (status, search, date_from, date_to, sort_by, order, page, per_page), return TaskListResponse

6. Create backend/app/api/benchmarks.py:
   - Router with prefix '/benchmarks', tag 'Benchmarks'
   - POST /run : trigger benchmark, return BenchmarkRunResponse (202 Accepted)
   - GET /runs : list all runs, return list[BenchmarkRunResponse]
   - GET /runs/{run_id} : get run detail, return BenchmarkRunDetail (404 if not found)

7. Create backend/app/api/settings.py:
   - Router with prefix '/settings', tag 'Settings'
   - GET / : return AppSettingsResponse
   - PUT / : update settings, return AppSettingsResponse
   - POST /test-connection : test provider, return ConnectionTestResponse

8. Update backend/app/api/router.py:
   - Import and include ALL routers (tasks, history, benchmarks, settings, health)

9. Update backend/app/main.py:
   - Wire up the database session dependency
   - Add exception handlers for 404, 422, 500

10. Update backend/app/dependencies.py:
   - get_db: proper async session generator using the session factory from db/session.py
   - get_task_service, get_settings_service, get_benchmark_service: dependency injection functions

VALIDATION:
- cd backend && python -c '
from app.main import app
routes = [r.path for r in app.routes if hasattr(r, \"path\")]
print(f\"Total routes: {len(routes)}\")
required = [\"/api/v1/tasks\", \"/api/v1/history\", \"/api/v1/benchmarks/run\", \"/api/v1/settings\", \"/api/v1/health\"]
for r in required:
    # Check that at least one route starts with the required prefix
    found = any(route.startswith(r.replace(\"/api/v1\", \"/api/v1\")) for route in routes)
    assert found or any(r.split(\"/\")[-1] in route for route in routes), f\"Missing route: {r}\"
print(\"All required routes registered\")
'
- cd backend && python -c 'from app.services.task_service import TaskService; print(\"TaskService OK\")'
- cd backend && python -c 'from app.services.settings_service import SettingsService; print(\"SettingsService OK\")'
- cd backend && python -c 'from app.services.benchmark_service import BenchmarkService; print(\"BenchmarkService OK\")'
- cd backend && python -m ruff check app/ --select E,F — should have zero errors
Print 'TASK 1.5 COMPLETE — All REST endpoints verified' when all pass.
"
```

---

### TASK 1.6 — Redis Integration

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: FastAPI app with config.py having REDIS_URL. Dependencies: redis>=5.0.0

Create Redis connection layer and caching utilities.

1. Create backend/app/db/redis.py:
   - Import redis.asyncio as aioredis
   - RedisManager class:
     - __init__(self, url: str): store url
     - async connect() -> None: create connection pool via aioredis.from_url(url, decode_responses=True)
     - async disconnect() -> None: close pool
     - async get(key: str) -> str|None
     - async set(key: str, value: str, ttl: int = 3600) -> None
     - async delete(key: str) -> None
     - async get_json(key: str) -> dict|None: get + json.loads
     - async set_json(key: str, value: dict, ttl: int = 3600) -> None: json.dumps + set
     - async publish(channel: str, message: str) -> None: for pub/sub
     - @property pool: returns the connection pool
   - Module-level redis_manager: RedisManager|None = None
   - get_redis_manager() -> RedisManager function

2. Update backend/app/main.py lifespan:
   - On startup: create redis_manager, call connect()
   - On shutdown: call disconnect()

3. Update backend/app/dependencies.py:
   - get_redis: dependency returning RedisManager instance

4. Create backend/app/services/cache.py:
   - CacheService wrapping RedisManager for app-level caching
   - cache_settings(settings: dict) -> None
   - get_cached_settings() -> dict|None
   - invalidate_settings() -> None
   - cache_task_status(task_id: str, status: str) -> None
   - get_cached_task_status(task_id: str) -> str|None

VALIDATION:
- cd backend && python -c '
from app.db.redis import RedisManager
rm = RedisManager(\"redis://localhost:6379/0\")
print(f\"RedisManager created with url\")
from app.services.cache import CacheService
print(\"CacheService imported\")
print(\"Redis integration complete\")
'
- cd backend && python -m ruff check app/db/redis.py app/services/cache.py --select E,F
Print 'TASK 1.6 COMPLETE — Redis integration verified' when all pass.
"
```

---

### TASK 1.7 — Docker Compose (Dev Environment)

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: Backend FastAPI app needs PostgreSQL and Redis. Sandbox needs Docker-in-Docker.

Create Docker Compose configuration for the full development stack.

1. Create docker-compose.dev.yml:
   services:
     postgres:
       image: postgres:16-alpine
       environment:
         POSTGRES_USER: codeforge
         POSTGRES_PASSWORD: codeforge
         POSTGRES_DB: codeforge
       ports: ['5432:5432']
       volumes: [pgdata:/var/lib/postgresql/data]
       healthcheck:
         test: ['CMD-SHELL', 'pg_isready -U codeforge']
         interval: 5s
         timeout: 5s
         retries: 5

     redis:
       image: redis:7-alpine
       ports: ['6379:6379']
       healthcheck:
         test: ['CMD', 'redis-cli', 'ping']
         interval: 5s
         timeout: 5s
         retries: 5

   volumes:
     pgdata:

2. Create docker-compose.yml (PRODUCTION — full stack):
   services:
     backend:
       build: {context: ./backend, dockerfile: Dockerfile}
       ports: ['8000:8000']
       environment:
         DATABASE_URL: postgresql+asyncpg://codeforge:codeforge@postgres:5432/codeforge
         REDIS_URL: redis://redis:6379/0
         OLLAMA_BASE_URL: http://ollama:11434
         OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4317
         DOCKER_HOST: unix:///var/run/docker.sock
         SANDBOX_IMAGE: codeforge-sandbox-python:latest
       volumes:
         - /var/run/docker.sock:/var/run/docker.sock
       depends_on:
         postgres: {condition: service_healthy}
         redis: {condition: service_healthy}
       restart: unless-stopped

     frontend:
       build: {context: ./frontend, dockerfile: Dockerfile}
       ports: ['3000:3000']
       environment:
         NEXT_PUBLIC_API_URL: http://localhost:8000
         NEXT_PUBLIC_WS_URL: ws://localhost:8000
       depends_on: [backend]
       restart: unless-stopped

     postgres:
       image: postgres:16-alpine
       environment:
         POSTGRES_USER: codeforge
         POSTGRES_PASSWORD: codeforge
         POSTGRES_DB: codeforge
       ports: ['5432:5432']
       volumes: [pgdata:/var/lib/postgresql/data]
       healthcheck:
         test: ['CMD-SHELL', 'pg_isready -U codeforge']
         interval: 5s
         timeout: 5s
         retries: 5

     redis:
       image: redis:7-alpine
       ports: ['6379:6379']
       healthcheck:
         test: ['CMD', 'redis-cli', 'ping']
         interval: 5s
         timeout: 5s
         retries: 5

     ollama:
       image: ollama/ollama:latest
       ports: ['11434:11434']
       volumes: [ollama_data:/root/.ollama]

     otel-collector:
       image: otel/opentelemetry-collector-contrib:latest
       command: ['--config', '/etc/otel/config.yml']
       volumes: ['./docker/otel/otel-collector-config.yml:/etc/otel/config.yml']
       ports: ['4317:4317', '4318:4318']
       depends_on: [jaeger]

     jaeger:
       image: jaegertracing/all-in-one:latest
       ports: ['16686:16686', '14268:14268']
       environment:
         COLLECTOR_OTLP_ENABLED: 'true'

   volumes:
     pgdata:
     ollama_data:

3. Create docker/otel/otel-collector-config.yml:
   receivers:
     otlp:
       protocols:
         grpc: {endpoint: '0.0.0.0:4317'}
         http: {endpoint: '0.0.0.0:4318'}
   processors:
     batch:
       timeout: 1s
       send_batch_size: 1024
   exporters:
     otlp/jaeger:
       endpoint: 'jaeger:4317'
       tls: {insecure: true}
     logging:
       loglevel: info
   service:
     pipelines:
       traces:
         receivers: [otlp]
         processors: [batch]
         exporters: [otlp/jaeger, logging]

4. Create backend/Dockerfile:
   FROM python:3.11-slim
   WORKDIR /app
   RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   EXPOSE 8000
   CMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]

5. Update Makefile:
   - dev-services: docker-compose -f docker-compose.dev.yml up -d
   - dev-services-down: docker-compose -f docker-compose.dev.yml down

VALIDATION:
- cat docker-compose.yml | python3 -c 'import sys,yaml; d=yaml.safe_load(sys.stdin) if __import__(\"importlib\").util.find_spec(\"yaml\") else print(\"YAML module not available, checking syntax...\"); print(\"docker-compose.yml is valid\")' 2>/dev/null || docker compose -f docker-compose.yml config > /dev/null 2>&1 && echo 'docker-compose.yml valid' || python3 -c 'import json; print(\"Skipping YAML validation - check manually\")'
- test -f docker-compose.dev.yml && echo 'dev compose exists'
- test -f docker/otel/otel-collector-config.yml && echo 'otel config exists'
- test -f backend/Dockerfile && echo 'backend Dockerfile exists'
- grep 'dev-services' Makefile && echo 'Makefile updated'
Print 'TASK 1.7 COMPLETE — Docker Compose verified' when all checks pass.
"
```

---

### TASK 1.8 — Sandbox Docker Image

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)

Create the Docker sandbox image for secure code execution.

1. Create docker/sandbox/Dockerfile.python:
   FROM python:3.11-slim
   
   # Install common data science / utility packages
   RUN pip install --no-cache-dir \
       numpy==1.26.2 \
       pandas==2.1.4 \
       matplotlib==3.8.2 \
       scipy==1.11.4 \
       scikit-learn==1.3.2 \
       requests==2.31.0 \
       beautifulsoup4==4.12.2 \
       sympy==1.12 \
       Pillow==10.1.0 \
       networkx==3.2.1 \
       sortedcontainers==2.4.0
   
   # Create non-root user for security
   RUN useradd -m -s /bin/bash sandbox
   USER sandbox
   WORKDIR /home/sandbox
   
   # Default: run a Python script passed as a file
   ENTRYPOINT [\"python\"]
   CMD [\"main.py\"]

2. Create docker/sandbox/Dockerfile.node (optional secondary sandbox):
   FROM node:20-slim
   RUN useradd -m -s /bin/bash sandbox
   USER sandbox
   WORKDIR /home/sandbox
   ENTRYPOINT [\"node\"]
   CMD [\"main.js\"]

3. Create a docker/sandbox/build.sh script:
   #!/bin/bash
   set -e
   echo 'Building Python sandbox image...'
   docker build -t codeforge-sandbox-python:latest -f docker/sandbox/Dockerfile.python docker/sandbox/
   echo 'Building Node.js sandbox image...'
   docker build -t codeforge-sandbox-node:latest -f docker/sandbox/Dockerfile.node docker/sandbox/
   echo 'All sandbox images built successfully!'

4. Make build.sh executable: chmod +x docker/sandbox/build.sh

5. Add to Makefile:
   build-sandbox: docker/sandbox/build.sh

VALIDATION:
- test -f docker/sandbox/Dockerfile.python && echo 'Python Dockerfile exists'
- test -f docker/sandbox/Dockerfile.node && echo 'Node Dockerfile exists'
- test -x docker/sandbox/build.sh && echo 'build.sh is executable'
- grep 'numpy' docker/sandbox/Dockerfile.python && echo 'numpy included'
- grep 'sandbox' docker/sandbox/Dockerfile.python && echo 'non-root user created'
- grep 'network' docker/sandbox/Dockerfile.python || echo 'No network config in image (correct — network disabled at runtime)'
Print 'TASK 1.8 COMPLETE — Sandbox Docker images verified' when all pass.
"
```

---

### TASK 1.9 — Sandbox Manager (Docker SDK)

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: Sandbox Docker image defined in docker/sandbox/Dockerfile.python. Config has SANDBOX_IMAGE, SANDBOX_TIMEOUT_SECONDS, SANDBOX_MEMORY_LIMIT_MB, SANDBOX_CPU_LIMIT, SANDBOX_NETWORK_DISABLED. Dependency: docker>=7.0.0

Create the sandbox manager that handles Docker container lifecycle for secure code execution.

1. Create backend/app/sandbox/__init__.py — empty

2. Create backend/app/sandbox/security.py:
   - DANGEROUS_IMPORTS: set of strings — ['os.system', 'subprocess', 'shutil.rmtree', '__import__', 'eval', 'exec', 'compile']
   - DANGEROUS_PATTERNS: list of regex patterns — [r'import\s+ctypes', r'from\s+ctypes', r'open\s*\(.*/etc/', r'open\s*\(.*/proc/', r'socket\.socket']
   - validate_code(code: str) -> tuple[bool, str|None]: scan for dangerous patterns, return (True, None) if safe or (False, 'reason') if unsafe
   - Note: this is a SOFT check (defense in depth). The Docker sandbox is the real isolation.

3. Create backend/app/sandbox/manager.py:
   - Import docker (Docker SDK for Python)
   - SandboxManager class:
     - __init__(self, image: str, timeout: int = 30, memory_mb: int = 512, cpu_limit: float = 1.0, network_disabled: bool = True)
     - async create_container(code: str, language: str = 'python') -> str:
       * Write code to a temp file
       * Create container with:
         - image=self.image
         - command=['python', '/code/main.py'] (or node for JS)
         - volumes={temp_dir: {'bind': '/code', 'mode': 'ro'}}
         - mem_limit=f'{self.memory_mb}m'
         - nano_cpus=int(self.cpu_limit * 1e9)
         - network_disabled=self.network_disabled
         - user='sandbox'
         - read_only=True (root fs)
         - tmpfs={'/tmp': 'size=64M'}
       * Return container.id
     
     - async execute(code: str, language: str = 'python') -> ExecutionOutput:
       * validate_code first (if fails, return error without running)
       * create_container
       * Start container
       * Wait with timeout
       * Capture stdout, stderr from container.logs()
       * Get exit code from container.wait()
       * Calculate execution_time_ms
       * Get memory stats if available
       * Cleanup: remove container + temp files
       * Return ExecutionOutput dataclass
     
     - async cleanup_container(container_id: str) -> None:
       * Try to stop container (timeout=5)
       * Remove container (force=True)
       * Clean up temp directory

   - @dataclass ExecutionOutput:
     - success: bool
     - exit_code: int
     - stdout: str
     - stderr: str
     - execution_time_ms: int
     - memory_used_mb: float | None
     - container_id: str
     - timed_out: bool = False

4. Create backend/app/sandbox/executor.py:
   - CodeExecutor class (high-level interface):
     - __init__(self, settings: SandboxSettings): create SandboxManager from settings
     - async execute_python(code: str) -> ExecutionOutput
     - async execute_with_retry(code: str, max_retries: int = 0) -> ExecutionOutput: single attempt (retries managed by orchestrator)
   - Use asyncio.wait_for for timeout enforcement
   - Handle docker.errors.ContainerError, docker.errors.ImageNotFound, docker.errors.APIError

5. Update backend/app/dependencies.py:
   - get_sandbox_executor: dependency returning CodeExecutor instance

IMPORTANT IMPLEMENTATION DETAILS:
- Use tempfile.mkdtemp() for code files, clean up in finally block
- Container names: f'codeforge-sandbox-{uuid4().hex[:8]}'
- Log container creation/destruction at INFO level
- Handle the case where Docker daemon is not available (raise clear error)
- All methods should be async (use asyncio.to_thread for sync Docker SDK calls)

VALIDATION:
- cd backend && python -c '
from app.sandbox.security import validate_code, DANGEROUS_IMPORTS, DANGEROUS_PATTERNS
# Test safe code
ok, msg = validate_code(\"print(42)\")
assert ok, f\"Safe code rejected: {msg}\"
# Test dangerous code
ok, msg = validate_code(\"import subprocess; subprocess.run([\\\"rm\\\", \\\"-rf\\\", \\\"/\\\"])\")
assert not ok, \"Dangerous code not caught\"
print(f\"Security validation works: {msg}\")
'
- cd backend && python -c '
from app.sandbox.manager import SandboxManager, ExecutionOutput
print(f\"SandboxManager imported\")
print(f\"ExecutionOutput fields: {ExecutionOutput.__dataclass_fields__.keys()}\")
'
- cd backend && python -c '
from app.sandbox.executor import CodeExecutor
print(\"CodeExecutor imported successfully\")
'
- cd backend && python -m ruff check app/sandbox/ --select E,F — should pass
Print 'TASK 1.9 COMPLETE — Sandbox manager verified' when all pass.
"
```

---

### TASK 1.10 — Sandbox Integration Tests

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: SandboxManager in backend/app/sandbox/manager.py, CodeExecutor in backend/app/sandbox/executor.py, ExecutionOutput dataclass.

Create comprehensive integration tests for the sandbox. These tests require Docker to be running.

Create backend/tests/integration/test_sandbox_execution.py:

import pytest
import pytest_asyncio
# ... proper imports

Mark all tests with @pytest.mark.integration and @pytest.mark.asyncio

Create a fixture that initializes SandboxManager with test-safe settings (timeout=10, memory=256).

Tests to write:

1. test_execute_simple_print:
   code = 'print(\"Hello CodeForge\")'
   Assert: success=True, exit_code=0, 'Hello CodeForge' in stdout, stderr is empty

2. test_execute_math_computation:
   code = 'import math; print(math.factorial(10))'
   Assert: success=True, '3628800' in stdout

3. test_execute_with_imports:
   code = 'import numpy as np; print(np.array([1,2,3]).sum())'
   Assert: success=True, '6' in stdout

4. test_execute_pandas:
   code = 'import pandas as pd; df = pd.DataFrame({\"a\": [1,2,3]}); print(df.shape)'
   Assert: success=True, '(3, 1)' in stdout

5. test_execute_syntax_error:
   code = 'def foo(\n  print(42)'
   Assert: success=False, exit_code != 0, 'SyntaxError' in stderr

6. test_execute_runtime_error:
   code = 'x = 1/0'
   Assert: success=False, 'ZeroDivisionError' in stderr

7. test_execute_import_error:
   code = 'import nonexistent_module_xyz'
   Assert: success=False, 'ModuleNotFoundError' in stderr

8. test_execute_timeout:
   code = 'import time; time.sleep(60)'
   Assert: timed_out=True OR execution_time_ms >= timeout * 1000

9. test_execute_stderr_capture:
   code = 'import sys; print(\"error msg\", file=sys.stderr)'
   Assert: 'error msg' in stderr

10. test_execute_multiline_output:
    code = 'for i in range(5): print(f\"line {i}\")'
    Assert: all 5 lines in stdout

11. test_security_validation_blocks_dangerous_code:
    code = 'import subprocess; subprocess.run([\"ls\"])'
    Assert: rejected by security validation (doesn't even run)

12. test_container_cleanup:
    Execute code, capture container_id, then verify the container no longer exists

13. test_execute_large_output:
    code = 'print(\"x\" * 100000)'
    Assert: success=True, stdout has the output (tests that large outputs don't crash)

Also create backend/tests/conftest.py if not exists:
- Add pytest markers: unit, integration, e2e
- Add fixture for SandboxManager that skips if Docker is not available:
  try: docker.from_env().ping() except: pytest.skip('Docker not available')

VALIDATION:
- cd backend && python -c 'import tests.integration.test_sandbox_execution; print(\"Test file imports OK\")'
- cd backend && python -m pytest tests/integration/test_sandbox_execution.py --collect-only 2>/dev/null | grep 'test_' | wc -l — should show 13+ tests collected
- cd backend && python -m ruff check tests/ --select E,F
Print 'TASK 1.10 COMPLETE — Sandbox tests written and verified' when all pass.
"
```

---

### TASK 1.11 — Structured JSON Logging

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: FastAPI app in backend/app/main.py. Config has LOG_LEVEL and LOG_FORMAT.

Create production-grade structured JSON logging.

1. Create backend/app/observability/__init__.py — empty

2. Create backend/app/observability/logging.py:
   - Configure Python logging with structlog or standard library JSON formatter
   - Use standard library approach (no extra deps): custom JsonFormatter(logging.Formatter) that outputs:
     {\"timestamp\": ISO8601, \"level\": \"INFO\", \"logger\": name, \"message\": msg, \"correlation_id\": id, ...extra}
   - setup_logging(level: str = 'INFO', format: str = 'json') function:
     * If format='json': use JsonFormatter
     * If format='text': use standard colored formatter for dev
     * Set root logger level
     * Add handler to root logger
     * Suppress noisy loggers: uvicorn.access at WARNING, sqlalchemy.engine at WARNING (unless DEBUG)
   - get_logger(name: str) -> logging.Logger: returns named logger
   - CorrelationIdMiddleware(BaseHTTPMiddleware):
     * Generate UUID for each request
     * Store in contextvars.ContextVar
     * Add to response header X-Correlation-ID
     * JsonFormatter reads from contextvar automatically

3. Update backend/app/main.py:
   - Call setup_logging() in lifespan startup
   - Add CorrelationIdMiddleware
   - Log startup/shutdown with structured fields

4. Create backend/app/observability/context.py:
   - correlation_id_var: ContextVar[str] with default ''
   - get_correlation_id() -> str
   - set_correlation_id(id: str)

VALIDATION:
- cd backend && python -c '
from app.observability.logging import setup_logging, get_logger, JsonFormatter
import json, io, logging

# Setup JSON logging
setup_logging(level=\"INFO\", format=\"json\")
logger = get_logger(\"test\")

# Capture log output
handler = logging.StreamHandler(stream := io.StringIO())
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
logger.info(\"Test message\", extra={\"task_id\": \"abc123\"})

output = stream.getvalue().strip()
parsed = json.loads(output)
assert \"timestamp\" in parsed
assert parsed[\"level\"] == \"INFO\"
assert parsed[\"message\"] == \"Test message\"
print(f\"JSON logging works: {parsed}\")
'
- cd backend && python -m ruff check app/observability/ --select E,F
Print 'TASK 1.11 COMPLETE — Structured logging verified' when all pass.
"
```

---

### TASK 1.12 — Test Infrastructure (conftest + fixtures)

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: Full backend structure exists. DB models, services, sandbox all created.

Create comprehensive test infrastructure.

1. Create/update backend/tests/conftest.py:
   - pytest markers: unit, integration, e2e
   - Fixtures:
     a. mock_settings: returns Settings with test-safe defaults (SQLite or test Postgres URL, test Redis, etc.)
     b. async_session: creates an async SQLAlchemy session using in-memory SQLite for unit tests
        * Create all tables before test, drop after
        * Use aiosqlite: 'sqlite+aiosqlite:///:memory:'
     c. mock_llm_response: factory fixture that returns a callable accepting (prompt) and returning canned responses
        * Returns different responses based on keywords in the prompt
        * Planning prompts return valid plan JSON
        * Coding prompts return valid code JSON
        * Review prompts return valid review JSON
     d. sample_task: creates a Task in the DB and returns it
     e. sample_traces: creates a set of AgentTrace records for a task
     f. sandbox_manager: SandboxManager fixture (skips if Docker unavailable)

2. Create backend/tests/unit/__init__.py

3. Create backend/tests/unit/test_cost_tracker.py (placeholder with one test):
   def test_placeholder():
       assert True  # Will be replaced in Phase 2

4. Create backend/pytest.ini or add to pyproject.toml:
   [tool.pytest.ini_options]
   asyncio_mode = 'auto'
   markers = ['unit: unit tests', 'integration: requires Docker/DB', 'e2e: full stack tests']
   testpaths = ['tests']
   filterwarnings = ['ignore::DeprecationWarning']

5. Verify the test infrastructure actually works:
   - Run: cd backend && python -m pytest tests/ -v --co (collect only)

VALIDATION:
- cd backend && python -m pytest tests/ --collect-only 2>&1 | tail -5 — should show tests collected
- cd backend && python -c 'import tests.conftest; print(\"conftest imports OK\")'
- cd backend && grep 'asyncio_mode' pyproject.toml && echo 'pytest config found'
Print 'TASK 1.12 COMPLETE — Test infrastructure verified' when all pass.
"
```

---

## PHASE 2: Agent System (Tasks 2.1 – 2.11)

---

### TASK 2.1 — LLM Provider Abstraction Layer

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: Config has OPENAI_API_KEY, ANTHROPIC_API_KEY, OLLAMA_BASE_URL. Dependencies: langchain-openai, langchain-anthropic, langchain.

Create a unified LLM provider abstraction that wraps OpenAI, Anthropic, and Ollama with a consistent interface.

1. Create backend/app/llm/__init__.py — empty

2. Create backend/app/llm/providers.py:

   from abc import ABC, abstractmethod
   from dataclasses import dataclass

   @dataclass
   class LLMResponse:
       content: str
       model: str
       input_tokens: int
       output_tokens: int
       total_tokens: int
       latency_ms: int
       raw_response: dict | None = None

   class BaseLLMProvider(ABC):
       @abstractmethod
       async def generate(self, prompt: str, system_prompt: str = '', temperature: float = 0.0, max_tokens: int = 4096, response_format: dict | None = None) -> LLMResponse: ...
       
       @abstractmethod
       async def generate_structured(self, prompt: str, system_prompt: str = '', schema: dict | None = None) -> LLMResponse:
           '''Generate with JSON output enforcement'''
           ...
       
       @abstractmethod
       async def health_check(self) -> bool: ...
       
       @property
       @abstractmethod
       def model_name(self) -> str: ...
       
       @property
       @abstractmethod
       def provider_name(self) -> str: ...

   class OpenAIProvider(BaseLLMProvider):
       def __init__(self, api_key: str, model: str = 'gpt-4'):
           from langchain_openai import ChatOpenAI
           self.llm = ChatOpenAI(api_key=api_key, model=model, temperature=0)
           self._model = model
       
       async def generate(...): 
           - Use self.llm.ainvoke()
           - Measure latency with time.perf_counter()
           - Extract token counts from response.usage_metadata
           - Return LLMResponse
       
       async def generate_structured(...):
           - Add 'Respond ONLY with valid JSON. No markdown, no backticks.' to system prompt
           - Call generate() 
           - Validate JSON parsing
           - If fails, retry once with stronger JSON instruction
       
       async def health_check():
           - Try a minimal generation: 'Say OK'
           - Return True/False
       
       model_name -> self._model
       provider_name -> 'openai'

   class AnthropicProvider(BaseLLMProvider):
       - Same pattern using langchain_anthropic.ChatAnthropic
       - Model default: 'claude-sonnet-4-20250514'

   class OllamaProvider(BaseLLMProvider):
       - Use langchain_community.llms.Ollama or httpx direct calls to Ollama API
       - Base URL from config
       - Model default: 'llama3:8b'
       - health_check: GET {base_url}/api/tags — check response
       - Note: Ollama may not provide token counts — estimate from string length

   class LLMProviderFactory:
       @staticmethod
       def create(provider: str, **kwargs) -> BaseLLMProvider:
           if provider == 'openai': return OpenAIProvider(**kwargs)
           elif provider == 'anthropic': return AnthropicProvider(**kwargs)
           elif provider == 'ollama': return OllamaProvider(**kwargs)
           else: raise ValueError(f'Unknown provider: {provider}')

VALIDATION:
- cd backend && python -c '
from app.llm.providers import (
    LLMResponse, BaseLLMProvider, OpenAIProvider, AnthropicProvider, 
    OllamaProvider, LLMProviderFactory
)
# Test dataclass
resp = LLMResponse(content=\"test\", model=\"gpt-4\", input_tokens=10, output_tokens=5, total_tokens=15, latency_ms=100)
print(f\"LLMResponse: {resp.content}, {resp.total_tokens} tokens\")

# Test factory
provider = LLMProviderFactory.create(\"openai\", api_key=\"test-key\", model=\"gpt-4\")
print(f\"Provider created: {provider.provider_name}/{provider.model_name}\")

# Test ollama factory
ollama = LLMProviderFactory.create(\"ollama\", base_url=\"http://localhost:11434\", model=\"llama3:8b\")
print(f\"Ollama provider: {ollama.provider_name}/{ollama.model_name}\")

print(\"All providers verified\")
'
- cd backend && python -m ruff check app/llm/providers.py --select E,F
Print 'TASK 2.1 COMPLETE — LLM providers verified' when all pass.
"
```

---

### TASK 2.2 — Task Complexity Classifier

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: LLM providers in backend/app/llm/providers.py with BaseLLMProvider, LLMProviderFactory. Config has COMPLEXITY_SIMPLE_THRESHOLD, COMPLEXITY_COMPLEX_THRESHOLD.

Create a task complexity classifier that routes tasks to appropriate models.

Create backend/app/llm/classifier.py:

1. ComplexityLevel enum: SIMPLE, MEDIUM, HARD

2. HeuristicClassifier (no LLM needed — fast keyword/pattern based):
   - SIMPLE indicators: 'hello world', 'print', 'fizzbuzz', single function, basic math, string manipulation, <50 words in prompt
   - HARD indicators: 'multiple files', 'database', 'API', 'concurrent', 'distributed', 'algorithm', 'optimize', 'machine learning', 'neural', >200 words in prompt, multiple requirements (count sentences > 5)
   - MEDIUM: everything else
   - Method: classify(prompt: str) -> tuple[ComplexityLevel, float]:
     * Score based on indicators (0.0 to 1.0)
     * Apply thresholds from config
     * Return (level, confidence_score)

3. LLMClassifier (uses a cheap model for better classification):
   - Takes a BaseLLMProvider
   - classify(prompt: str) -> tuple[ComplexityLevel, float]:
     * Send prompt with system instruction:
       'Classify this coding task complexity as SIMPLE, MEDIUM, or HARD. 
        SIMPLE: single function, basic operations, well-known patterns.
        MEDIUM: multiple functions, some error handling, standard libraries.
        HARD: multi-step, complex logic, multiple modules, advanced algorithms.
        Respond with JSON: {\"level\": \"SIMPLE|MEDIUM|HARD\", \"confidence\": 0.0-1.0, \"reasoning\": \"brief explanation\"}'
     * Parse response, return (level, confidence)
     * Fallback to HeuristicClassifier if LLM call fails

4. TaskClassifier (main interface):
   - __init__(self, llm_provider: BaseLLMProvider | None = None, use_llm: bool = False):
   - classify(prompt: str) -> tuple[ComplexityLevel, float]:
     * If use_llm and llm_provider available: use LLMClassifier
     * Otherwise: use HeuristicClassifier
   - Always log classification result

VALIDATION:
- cd backend && python -c '
from app.llm.classifier import TaskClassifier, ComplexityLevel, HeuristicClassifier

clf = HeuristicClassifier()

# Simple task
level, conf = clf.classify(\"Write a function that prints hello world\")
print(f\"hello world -> {level.name} (conf={conf:.2f})\")
assert level == ComplexityLevel.SIMPLE, f\"Expected SIMPLE, got {level}\"

# Hard task  
level, conf = clf.classify(\"Build a distributed web scraping system with multiple workers, a task queue using Redis, rate limiting, proxy rotation, and store results in PostgreSQL with proper error handling and retry logic. Include a REST API for monitoring.\")
print(f\"distributed scraper -> {level.name} (conf={conf:.2f})\")
assert level == ComplexityLevel.HARD, f\"Expected HARD, got {level}\"

# Medium task
level, conf = clf.classify(\"Write a function that reads a CSV file, filters rows where age > 30, and writes the result to a new file\")
print(f\"csv filter -> {level.name} (conf={conf:.2f})\")
assert level in (ComplexityLevel.MEDIUM, ComplexityLevel.SIMPLE), f\"Unexpected: {level}\"

# Test TaskClassifier interface
tc = TaskClassifier(use_llm=False)
level, conf = tc.classify(\"Sort a list of numbers\")
print(f\"TaskClassifier: {level.name}\")

print(\"Classifier verified\")
'
- cd backend && python -m ruff check app/llm/classifier.py --select E,F
Print 'TASK 2.2 COMPLETE — Complexity classifier verified' when all pass.
"
```

---

### TASK 2.3 — Model Router

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: LLM providers in backend/app/llm/providers.py. Classifier in backend/app/llm/classifier.py. Config has DEFAULT_SIMPLE_MODEL, DEFAULT_COMPLEX_MODEL, OPENAI_API_KEY, ANTHROPIC_API_KEY, OLLAMA_BASE_URL.

Create the model router that picks the optimal model based on task complexity.

Create backend/app/llm/router.py:

1. @dataclass ModelConfig:
   - provider: str  # 'openai', 'anthropic', 'ollama'
   - model: str     # 'gpt-4', 'claude-sonnet-4-20250514', 'llama3:8b'
   - cost_per_1k_input: float
   - cost_per_1k_output: float

2. DEFAULT_MODEL_CONFIGS dict mapping complexity to ModelConfig:
   - SIMPLE: ollama/llama3:8b (cost: 0.0 / 0.0)
   - MEDIUM: openai/gpt-4o-mini (cost: 0.15 / 0.60 per 1M -> per 1k)
   - HARD: openai/gpt-4 (cost: 30.0 / 60.0 per 1M -> per 1k)

3. ModelRouter class:
   - __init__(self, settings: Settings):
     * Create available providers dict based on which API keys are configured
     * Create TaskClassifier
   - async route(self, prompt: str) -> tuple[BaseLLMProvider, ModelConfig, ComplexityLevel]:
     * Classify the task
     * Select ModelConfig based on complexity
     * Check if that provider is available (API key exists, or Ollama is reachable)
     * If not available, FALLBACK: try next best available provider
     * Fallback chain: ollama -> openai -> anthropic (for simple)
     * Fallback chain: openai -> anthropic -> ollama (for complex)
     * Create and return the provider instance + config + complexity level
     * Log the routing decision: '{complexity} task -> {provider}/{model}'
   
   - get_provider(self, provider_name: str, model: str) -> BaseLLMProvider:
     * Use LLMProviderFactory
   
   - get_available_providers(self) -> list[str]:
     * Check which providers have credentials configured
     * For ollama: optionally try health_check
   
   - async estimate_cost(self, prompt: str, model_config: ModelConfig) -> float:
     * Rough estimate based on prompt token count (len(prompt.split()) * 1.3 as token estimate)

VALIDATION:
- cd backend && python -c '
from app.llm.router import ModelRouter, ModelConfig, DEFAULT_MODEL_CONFIGS
from app.llm.classifier import ComplexityLevel

# Check configs exist
for level in ComplexityLevel:
    assert level in DEFAULT_MODEL_CONFIGS or level.name in str(DEFAULT_MODEL_CONFIGS), f\"Missing config for {level}\"
print(f\"Model configs: {len(DEFAULT_MODEL_CONFIGS)} levels configured\")

# Check ModelConfig
mc = ModelConfig(provider=\"openai\", model=\"gpt-4\", cost_per_1k_input=0.03, cost_per_1k_output=0.06)
print(f\"ModelConfig: {mc.provider}/{mc.model}\")

print(\"Model router verified\")
'
- cd backend && python -m ruff check app/llm/router.py --select E,F
Print 'TASK 2.3 COMPLETE — Model router verified' when all pass.
"
```

---

### TASK 2.4 — Cost Tracker

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: ModelConfig in backend/app/llm/router.py has cost_per_1k_input/output. LLMResponse has input_tokens, output_tokens.

Create cost tracking for every LLM call.

Create backend/app/llm/cost_tracker.py:

1. PRICING dict — cost per 1K tokens (input, output):
   'gpt-4': (0.03, 0.06)
   'gpt-4-turbo': (0.01, 0.03)
   'gpt-4o': (0.005, 0.015)
   'gpt-4o-mini': (0.00015, 0.0006)
   'claude-sonnet-4-20250514': (0.003, 0.015)
   'claude-haiku-4-5-20251001': (0.0008, 0.004)
   'llama3:8b': (0.0, 0.0)  # Local, free
   # Add more as needed

2. @dataclass CostRecord:
   - model: str
   - input_tokens: int
   - output_tokens: int
   - cost_usd: float
   - timestamp: datetime

3. CostTracker class:
   - __init__(self):
     * records: list[CostRecord] = []
     * total_cost: float = 0.0
   
   - calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
     * Look up pricing, compute cost
     * If model not in PRICING, log warning, estimate using gpt-4o-mini prices
   
   - record(llm_response: LLMResponse) -> CostRecord:
     * Calculate cost
     * Create CostRecord, append to records
     * Update total_cost
     * Return the record
   
   - get_summary() -> dict:
     * total_cost, total_tokens, records_count
     * cost_by_model: dict[str, float]
     * tokens_by_model: dict[str, int]
     * estimated_savings: cost if everything used gpt-4 minus actual cost
   
   - reset():
     * Clear records, reset total

VALIDATION:
- cd backend && python -c '
from app.llm.cost_tracker import CostTracker, PRICING, CostRecord
from app.llm.providers import LLMResponse

tracker = CostTracker()

# Simulate GPT-4 call
resp = LLMResponse(content=\"code here\", model=\"gpt-4\", input_tokens=500, output_tokens=200, total_tokens=700, latency_ms=1500)
record = tracker.record(resp)
print(f\"GPT-4 cost: \${record.cost_usd:.4f}\")
assert record.cost_usd > 0

# Simulate Llama call (free)
resp2 = LLMResponse(content=\"code\", model=\"llama3:8b\", input_tokens=300, output_tokens=100, total_tokens=400, latency_ms=800)
record2 = tracker.record(resp2)
print(f\"Llama cost: \${record2.cost_usd:.4f}\")
assert record2.cost_usd == 0.0

# Check summary
summary = tracker.get_summary()
print(f\"Total cost: \${summary[\"total_cost\"]:.4f}\")
print(f\"Cost by model: {summary[\"cost_by_model\"]}\")
print(f\"Estimated savings: \${summary[\"estimated_savings\"]:.4f}\")
assert summary[\"estimated_savings\"] > 0  # Saved money by using Llama

print(\"Cost tracker verified\")
'
- cd backend && python -m ruff check app/llm/cost_tracker.py --select E,F
Print 'TASK 2.4 COMPLETE — Cost tracker verified' when all pass.
"
```

---

### TASK 2.5 — Base Agent Class

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: LLM providers in app/llm/providers.py (BaseLLMProvider, LLMResponse). CostTracker in app/llm/cost_tracker.py.

Create the abstract base agent class that all agents inherit from.

Create backend/app/agents/base.py:

1. AgentType enum: PLANNER, CODER, EXECUTOR, REVIEWER

2. @dataclass AgentInput:
   - data: dict  # Flexible input payload
   - task_id: str
   - step_order: int

3. @dataclass AgentOutput:
   - data: dict         # Flexible output payload
   - reasoning: str     # Explanation of what the agent did
   - tokens_used: int
   - cost_usd: float
   - duration_ms: int
   - success: bool
   - error: str | None = None

4. AgentCallback protocol/ABC:
   - on_agent_start(agent_type: AgentType, input_data: dict) -> None
   - on_agent_thinking(agent_type: AgentType, chunk: str) -> None
   - on_agent_complete(agent_type: AgentType, output: AgentOutput) -> None
   - on_agent_error(agent_type: AgentType, error: str) -> None

5. BaseAgent(ABC):
   - __init__(self, llm: BaseLLMProvider, cost_tracker: CostTracker, callback: AgentCallback | None = None):
   
   - @abstractmethod agent_type(self) -> AgentType: ...
   - @abstractmethod async def _execute(self, input_data: AgentInput) -> AgentOutput: ...
   - @abstractmethod def _build_system_prompt(self) -> str: ...
   - @abstractmethod def _build_user_prompt(self, input_data: AgentInput) -> str: ...
   
   - async def run(self, input_data: AgentInput) -> AgentOutput:
     '''Template method pattern — handles common concerns'''
     * Log start
     * Notify callback on_agent_start
     * Start timer
     * Try:
       - Call self._execute(input_data)
       - Record cost via tracker
       - Notify callback on_agent_complete
     * Except:
       - Log error
       - Notify callback on_agent_error
       - Return AgentOutput with success=False, error=str(e)
     * Finally:
       - Calculate duration_ms
     * Return output
   
   - async def _call_llm(self, user_prompt: str, system_prompt: str | None = None) -> LLMResponse:
     '''Helper to call LLM with structured output'''
     * Use self.llm.generate_structured() for JSON responses
     * Use self.llm.generate() for free-text
     * Record via cost_tracker
     * Notify callback on_agent_thinking with response chunks
     * Return response
   
   - def _parse_json_response(self, text: str) -> dict:
     '''Safely parse JSON from LLM response, handling markdown fences'''
     * Strip ```json and ``` 
     * Try json.loads
     * If fails, try to extract JSON from text using regex
     * If still fails, raise ValueError with helpful message
   
   - def _get_logger(self) -> logging.Logger:
     * Return logger named f'codeforge.agent.{self.agent_type.value}'

6. NullCallback class implementing AgentCallback with no-ops (default)

VALIDATION:
- cd backend && python -c '
from app.agents.base import (
    BaseAgent, AgentType, AgentInput, AgentOutput, 
    AgentCallback, NullCallback
)

# Test enums and dataclasses
assert AgentType.PLANNER.value == \"planner\"
inp = AgentInput(data={\"prompt\": \"test\"}, task_id=\"abc\", step_order=1)
out = AgentOutput(data={}, reasoning=\"test\", tokens_used=0, cost_usd=0.0, duration_ms=100, success=True)
print(f\"AgentInput: {inp.task_id}, AgentOutput: success={out.success}\")

# Test JSON parsing
agent_cls = BaseAgent
# We cannot instantiate ABC, but we can test the static helper
import json
test_text = \"\`\`\`json\\n{\\\"key\\\": \\\"value\\\"}\\n\`\`\`\"
# Test that parse method exists
assert hasattr(BaseAgent, \"_parse_json_response\")

# Test NullCallback
cb = NullCallback()
cb.on_agent_start(AgentType.PLANNER, {})
print(\"NullCallback works\")

print(\"Base agent verified\")
'
- cd backend && python -m ruff check app/agents/base.py --select E,F
Print 'TASK 2.5 COMPLETE — Base agent class verified' when all pass.
"
```

---

### TASK 2.6 — Planner Agent

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: BaseAgent in backend/app/agents/base.py. AgentType, AgentInput, AgentOutput defined. LLM providers available.

Create the Planner Agent that decomposes natural language tasks into execution plans.

1. Create backend/app/agents/prompts/__init__.py — empty

2. Create backend/app/agents/prompts/planner.py:
   
   PLANNER_SYSTEM_PROMPT = '''You are a software planning agent. Your job is to decompose a coding task into clear, ordered subtasks.

Rules:
1. Break the task into 2-6 subtasks. Each must be independently implementable as a Python function or module.
2. Identify dependencies between subtasks (which must complete before others can start).
3. Estimate complexity of each subtask: simple, medium, or hard.
4. The FINAL subtask must always be an integration step that combines all prior work into a single runnable script with a main() function.
5. Each subtask description must be specific enough for a code generator to implement without ambiguity.

Output ONLY valid JSON matching this exact schema:
{
  \"subtasks\": [
    {
      \"id\": 1,
      \"description\": \"Write a function that...\",
      \"dependencies\": [],
      \"estimated_complexity\": \"simple\"
    }
  ],
  \"reasoning\": \"Brief explanation of decomposition strategy\"
}

Do NOT include any text outside the JSON. No markdown fences.'''

   def build_planner_user_prompt(task_prompt: str) -> str:
       return f'Decompose this coding task into subtasks:\n\n{task_prompt}'

3. Create backend/app/agents/planner.py:
   
   class PlannerAgent(BaseAgent):
       @property
       def agent_type(self) -> AgentType: return AgentType.PLANNER
       
       def _build_system_prompt(self) -> str:
           return PLANNER_SYSTEM_PROMPT
       
       def _build_user_prompt(self, input_data: AgentInput) -> str:
           return build_planner_user_prompt(input_data.data['prompt'])
       
       async def _execute(self, input_data: AgentInput) -> AgentOutput:
           - Build prompts
           - Call self._call_llm()
           - Parse JSON response
           - Validate plan structure:
             * Must have 'subtasks' key with list
             * Each subtask must have id, description, dependencies, estimated_complexity
             * Dependencies must reference valid subtask IDs
             * Last subtask should be integration (heuristic check)
             * No circular dependencies (topological sort check)
           - If validation fails, retry once with error feedback
           - Return AgentOutput with data=parsed_plan, reasoning=plan['reasoning']
       
       def _validate_plan(self, plan: dict) -> tuple[bool, str]:
           '''Validate plan structure and dependencies'''
           - Check required keys
           - Check subtask IDs are sequential starting from 1
           - Check dependencies reference valid IDs
           - Check no self-dependencies
           - Check DAG (no cycles) using topological sort
           - Return (True, '') or (False, 'error description')

VALIDATION:
- cd backend && python -c '
from app.agents.planner import PlannerAgent
from app.agents.base import AgentType, AgentInput
from app.agents.prompts.planner import PLANNER_SYSTEM_PROMPT, build_planner_user_prompt

# Test prompt building
prompt = build_planner_user_prompt(\"Write a web scraper\")
assert \"web scraper\" in prompt
print(f\"User prompt: {prompt[:80]}...\")
print(f\"System prompt length: {len(PLANNER_SYSTEM_PROMPT)} chars\")

# Test agent type
# Cannot fully test without LLM, but verify structure
assert PlannerAgent.__bases__[0].__name__ == \"BaseAgent\"
print(\"PlannerAgent inherits BaseAgent\")

# Test validation (create instance with mock)
import json
sample_plan = {
    \"subtasks\": [
        {\"id\": 1, \"description\": \"Fetch data\", \"dependencies\": [], \"estimated_complexity\": \"simple\"},
        {\"id\": 2, \"description\": \"Process data\", \"dependencies\": [1], \"estimated_complexity\": \"medium\"},
        {\"id\": 3, \"description\": \"Main integration\", \"dependencies\": [1, 2], \"estimated_complexity\": \"simple\"}
    ],
    \"reasoning\": \"Three-step pipeline\"
}

# Test validate_plan method exists
assert hasattr(PlannerAgent, \"_validate_plan\")
print(\"Plan validation method exists\")

print(\"Planner agent verified\")
'
- cd backend && python -m ruff check app/agents/planner.py app/agents/prompts/planner.py --select E,F
Print 'TASK 2.6 COMPLETE — Planner agent verified' when all pass.
"
```

---

### TASK 2.7 — Coder Agent

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: BaseAgent, AgentType, AgentInput, AgentOutput in backend/app/agents/base.py. Planner produces plans with subtasks.

Create the Coder Agent that generates Python code for each subtask.

1. Create backend/app/agents/prompts/coder.py:

   CODER_SYSTEM_PROMPT = '''You are an expert Python code generation agent. Generate clean, production-quality code.

Rules:
1. Write well-typed Python 3.11+ code with type hints.
2. Include docstrings (Google style) for all functions and classes.
3. Handle edge cases: empty inputs, None values, type mismatches.
4. Use only standard library + these allowed packages: numpy, pandas, matplotlib, scipy, scikit-learn, requests, beautifulsoup4, sympy, Pillow, networkx.
5. Follow PEP 8. Use descriptive variable names.
6. If this is the integration subtask, create a complete runnable script with:
   - All necessary imports at the top
   - A main() function that orchestrates everything
   - if __name__ == \"__main__\": main()
   - Print meaningful output showing the result

Output ONLY valid JSON:
{
  \"code\": \"<complete Python code as a string>\",
  \"imports\": [\"list\", \"of\", \"required\", \"packages\"],
  \"explanation\": \"Brief description of approach and key decisions\"
}

Do NOT include markdown fences in the code field. Escape newlines as \\n in the JSON string.'''

   def build_coder_user_prompt(subtask: dict, plan: dict, prior_code: dict[int, str]) -> str:
       prompt = f\"\"\"Generate code for this subtask:

Subtask #{subtask['id']}: {subtask['description']}
Complexity: {subtask['estimated_complexity']}

Full plan context:
{json.dumps(plan['subtasks'], indent=2)}
\"\"\"
       if prior_code:
           prompt += \"\\nPreviously generated code from completed subtasks:\\n\"
           for sid, code in sorted(prior_code.items()):
               prompt += f\"\\n--- Subtask #{sid} ---\\n{code}\\n\"
       
       if subtask.get('dependencies'):
           prompt += f\"\\nThis subtask depends on subtasks: {subtask['dependencies']}\"
           prompt += \"\\nMake sure your code integrates with the prior code above.\"
       
       return prompt

2. Create backend/app/agents/coder.py:

   class CoderAgent(BaseAgent):
       @property
       def agent_type(self) -> AgentType: return AgentType.CODER
       
       def _build_system_prompt(self) -> str:
           return CODER_SYSTEM_PROMPT
       
       def _build_user_prompt(self, input_data: AgentInput) -> str:
           return build_coder_user_prompt(
               input_data.data['subtask'],
               input_data.data['plan'],
               input_data.data.get('prior_code', {})
           )
       
       async def _execute(self, input_data: AgentInput) -> AgentOutput:
           - Build prompts
           - Call LLM
           - Parse JSON response
           - Validate code:
             * Must have 'code' key with non-empty string
             * Code must be valid Python (compile() check)
             * Extract imports, verify they're in allowed list
           - If integration subtask: merge with prior code
           - Return AgentOutput with data={'code': code, 'imports': imports, 'explanation': explanation}
       
       def _validate_code(self, code: str) -> tuple[bool, str]:
           '''Check if code is syntactically valid Python'''
           try:
               compile(code, '<generated>', 'exec')
               return (True, '')
           except SyntaxError as e:
               return (False, f'Syntax error at line {e.lineno}: {e.msg}')
       
       def _merge_code(self, code_segments: dict[int, str], integration_code: str) -> str:
           '''Merge all code segments into a single file'''
           - Collect all imports from all segments
           - Deduplicate imports
           - Place imports at top
           - Add all function definitions
           - Add main() and if __name__ block
           - Return merged code

VALIDATION:
- cd backend && python -c '
from app.agents.coder import CoderAgent
from app.agents.base import AgentType
from app.agents.prompts.coder import CODER_SYSTEM_PROMPT, build_coder_user_prompt
import json

# Test prompt building
subtask = {\"id\": 1, \"description\": \"Write hello world\", \"dependencies\": [], \"estimated_complexity\": \"simple\"}
plan = {\"subtasks\": [subtask]}
prompt = build_coder_user_prompt(subtask, plan, {})
assert \"hello world\" in prompt
print(f\"User prompt built: {len(prompt)} chars\")

# Test with prior code
prior = {1: \"def fetch(): return [1,2,3]\"}
prompt2 = build_coder_user_prompt(
    {\"id\": 2, \"description\": \"Process data\", \"dependencies\": [1], \"estimated_complexity\": \"simple\"},
    plan, prior
)
assert \"Subtask #1\" in prompt2
print(f\"Prompt with prior code: {len(prompt2)} chars\")

# Test code validation
assert hasattr(CoderAgent, \"_validate_code\")
assert hasattr(CoderAgent, \"_merge_code\")
print(\"CoderAgent structure verified\")
'
- cd backend && python -m ruff check app/agents/coder.py app/agents/prompts/coder.py --select E,F
Print 'TASK 2.7 COMPLETE — Coder agent verified' when all pass.
"
```

---

### TASK 2.8 — Reviewer Agent

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: BaseAgent in backend/app/agents/base.py. Executor produces ExecutionOutput with exit_code, stdout, stderr.

Create the Reviewer Agent that analyzes execution failures and suggests fixes.

1. Create backend/app/agents/prompts/reviewer.py:

   REVIEWER_SYSTEM_PROMPT = '''You are an expert code debugging agent. Analyze failed code execution and suggest precise fixes.

Rules:
1. Identify the ROOT CAUSE from the traceback/error output.
2. Classify the error type: syntax_error, runtime_error, logic_error, import_error, timeout, memory_error.
3. Suggest the MINIMAL fix — change as few lines as possible. Do NOT rewrite the entire program.
4. Provide the COMPLETE fixed code (not just the changed lines).
5. Rate your confidence in the fix from 0.0 to 1.0.
6. If confidence < 0.5, suggest a completely different approach.

Output ONLY valid JSON:
{
  \"root_cause\": \"Clear description of why the code failed\",
  \"error_type\": \"runtime_error\",
  \"fix_description\": \"What the fix does and why\",
  \"fixed_code\": \"<complete corrected Python code>\",
  \"confidence\": 0.85,
  \"changes_made\": [\"Line 12: changed dict['key'] to dict.get('key', default)\"]
}'''

   def build_reviewer_user_prompt(code: str, error: dict, attempt: int, max_attempts: int, original_task: str) -> str:
       return f\"\"\"Fix this failed code execution.

ORIGINAL TASK: {original_task}

ATTEMPT: {attempt} of {max_attempts}

CODE THAT FAILED:
```python
{code}
```

EXIT CODE: {error.get('exit_code', 'unknown')}

STDOUT:
{error.get('stdout', '(empty)')}

STDERR:
{error.get('stderr', '(empty)')}

Analyze the error and provide a fix. Remember: minimal changes only.\"\"\"

2. Create backend/app/agents/reviewer.py:

   class ReviewerAgent(BaseAgent):
       @property
       def agent_type(self) -> AgentType: return AgentType.REVIEWER
       
       async def _execute(self, input_data: AgentInput) -> AgentOutput:
           - Build prompts
           - Call LLM
           - Parse JSON response
           - Validate review:
             * Must have root_cause, fixed_code, confidence
             * fixed_code must be valid Python (compile check)
             * confidence must be float between 0 and 1
           - Return AgentOutput with data containing the full review
       
       def _validate_review(self, review: dict) -> tuple[bool, str]:
           '''Validate the review output structure'''
           required = ['root_cause', 'fixed_code', 'confidence']
           for key in required:
               if key not in review:
                   return (False, f'Missing key: {key}')
           if not isinstance(review['confidence'], (int, float)):
               return (False, 'confidence must be a number')
           if not 0 <= review['confidence'] <= 1:
               return (False, 'confidence must be between 0 and 1')
           # Validate fixed code compiles
           try:
               compile(review['fixed_code'], '<fix>', 'exec')
           except SyntaxError as e:
               return (False, f'Fixed code has syntax error: {e}')
           return (True, '')

VALIDATION:
- cd backend && python -c '
from app.agents.reviewer import ReviewerAgent
from app.agents.base import AgentType
from app.agents.prompts.reviewer import REVIEWER_SYSTEM_PROMPT, build_reviewer_user_prompt

# Test prompt
prompt = build_reviewer_user_prompt(
    code=\"x = 1/0\",
    error={\"exit_code\": 1, \"stdout\": \"\", \"stderr\": \"ZeroDivisionError: division by zero\"},
    attempt=1, max_attempts=3,
    original_task=\"Compute ratio\"
)
assert \"ZeroDivisionError\" in prompt
assert \"1 of 3\" in prompt
print(f\"Reviewer prompt: {len(prompt)} chars\")

# Verify structure
assert ReviewerAgent.__bases__[0].__name__ == \"BaseAgent\"
assert hasattr(ReviewerAgent, \"_validate_review\")
print(\"ReviewerAgent verified\")
'
- cd backend && python -m ruff check app/agents/reviewer.py app/agents/prompts/reviewer.py --select E,F
Print 'TASK 2.8 COMPLETE — Reviewer agent verified' when all pass.
"
```

---

### TASK 2.9 — LangGraph Orchestrator (State Machine)

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: All agents created: PlannerAgent, CoderAgent, ExecutorAgent (sandbox), ReviewerAgent. ModelRouter in app/llm/router.py. CostTracker in app/llm/cost_tracker.py. AgentCallback in app/agents/base.py.

Create the LangGraph state machine orchestrator that manages the full agent lifecycle.

Create backend/app/agents/orchestrator.py:

1. Import everything:
   from langgraph.graph import StateGraph, END
   from typing import TypedDict, Optional, Annotated
   import operator  # for Annotated reducers if needed

2. Define AgentState(TypedDict):
   # Input
   prompt: str
   task_id: str
   
   # Classification
   complexity: str                    # 'simple' | 'medium' | 'hard'
   model_used: str
   
   # Planning
   plan: dict | None                  # Planner output
   current_subtask_index: int
   
   # Coding
   code_segments: dict                # {subtask_id: code_string}
   integrated_code: str               # Final merged code
   
   # Execution
   execution_result: dict | None
   execution_success: bool
   
   # Review / Repair
   review_result: dict | None
   retry_count: int
   max_retries: int
   
   # Metadata
   total_cost_usd: float
   total_tokens: int
   traces: list                       # All agent trace records
   error_message: str | None
   status: str                        # Current status string

3. Node functions (each takes AgentState, returns partial state update dict):

   async def classify_node(state: AgentState) -> dict:
       - Use ModelRouter to classify complexity and select model
       - Return {complexity, model_used, status: 'classifying'}
   
   async def plan_node(state: AgentState) -> dict:
       - Create PlannerAgent with routed LLM provider
       - Run planner with the prompt
       - Return {plan: output.data, status: 'planning', traces: [...existing, new_trace], cost/tokens updates}
   
   async def code_node(state: AgentState) -> dict:
       - Create CoderAgent
       - Iterate through subtasks in dependency order
       - For each subtask: generate code, store in code_segments
       - After all subtasks: merge into integrated_code
       - Return {code_segments, integrated_code, status: 'coding', traces updated}
   
   async def execute_node(state: AgentState) -> dict:
       - Create sandbox CodeExecutor
       - Execute integrated_code
       - Return {execution_result: result_dict, execution_success: result.success, status: 'executing'}
   
   async def review_node(state: AgentState) -> dict:
       - Create ReviewerAgent
       - Pass failed code + error info
       - Return {review_result: output.data, status: 'reviewing', retry_count: state.retry_count + 1}
   
   async def apply_fix_node(state: AgentState) -> dict:
       - Take fixed_code from review_result
       - Update integrated_code
       - Apply exponential backoff: await asyncio.sleep(2 ** (state.retry_count - 1))
       - Return {integrated_code: fixed_code, status: 'repairing'}
   
   async def finalize_node(state: AgentState) -> dict:
       - Return {status: 'completed', error_message: None}
   
   async def fail_node(state: AgentState) -> dict:
       - Compile error trail from all failed execution results
       - Return {status: 'failed', error_message: compiled_error}

4. Conditional edge functions:
   
   def check_execution(state: AgentState) -> str:
       return 'success' if state['execution_success'] else 'failure'
   
   def should_retry(state: AgentState) -> str:
       if state['retry_count'] >= state['max_retries']:
           return 'abort'
       if (state.get('review_result') and
           state['review_result'].get('confidence', 0) < 0.3 and
           state['retry_count'] >= 2):
           return 'abort'  # Low-confidence escape hatch
       return 'retry'

5. Build the graph:
   
   def build_agent_graph() -> StateGraph:
       graph = StateGraph(AgentState)
       
       graph.add_node('classify', classify_node)
       graph.add_node('plan', plan_node)
       graph.add_node('code', code_node)
       graph.add_node('execute', execute_node)
       graph.add_node('review', review_node)
       graph.add_node('apply_fix', apply_fix_node)
       graph.add_node('finalize', finalize_node)
       graph.add_node('fail', fail_node)
       
       graph.set_entry_point('classify')
       graph.add_edge('classify', 'plan')
       graph.add_edge('plan', 'code')
       graph.add_edge('code', 'execute')
       
       graph.add_conditional_edges('execute', check_execution, {
           'success': 'finalize',
           'failure': 'review'
       })
       graph.add_conditional_edges('review', should_retry, {
           'retry': 'apply_fix',
           'abort': 'fail'
       })
       
       graph.add_edge('apply_fix', 'execute')
       graph.add_edge('finalize', END)
       graph.add_edge('fail', END)
       
       return graph.compile()

6. Create Orchestrator class (high-level interface):
   
   class Orchestrator:
       def __init__(self, settings, callback: AgentCallback | None = None):
           self.settings = settings
           self.callback = callback
           self.graph = build_agent_graph()
           self.cost_tracker = CostTracker()
       
       async def run_task(self, task_id: str, prompt: str) -> AgentState:
           '''Execute the full agent pipeline for a task'''
           initial_state: AgentState = {
               'prompt': prompt,
               'task_id': task_id,
               'complexity': '',
               'model_used': '',
               'plan': None,
               'current_subtask_index': 0,
               'code_segments': {},
               'integrated_code': '',
               'execution_result': None,
               'execution_success': False,
               'review_result': None,
               'retry_count': 0,
               'max_retries': settings.MAX_REPAIR_RETRIES or 3,
               'total_cost_usd': 0.0,
               'total_tokens': 0,
               'traces': [],
               'error_message': None,
               'status': 'pending'
           }
           
           result = await self.graph.ainvoke(initial_state)
           return result

IMPORTANT: The node functions need access to settings and LLM providers. Use a factory pattern or closure to inject these dependencies. A clean approach:
- Store settings, model_router, cost_tracker, sandbox_executor, and callback on a module-level or pass via a context object stored in the state.

VALIDATION:
- cd backend && python -c '
from app.agents.orchestrator import (
    AgentState, build_agent_graph, Orchestrator,
    classify_node, plan_node, code_node, execute_node,
    review_node, apply_fix_node, finalize_node, fail_node,
    check_execution, should_retry
)

# Test conditional functions
test_state_success = {\"execution_success\": True}
assert check_execution(test_state_success) == \"success\"

test_state_fail = {\"execution_success\": False}
assert check_execution(test_state_fail) == \"failure\"

# Test retry logic
test_retry_ok = {\"retry_count\": 1, \"max_retries\": 3, \"review_result\": {\"confidence\": 0.8}}
assert should_retry(test_retry_ok) == \"retry\"

test_retry_max = {\"retry_count\": 3, \"max_retries\": 3}
assert should_retry(test_retry_max) == \"abort\"

test_retry_low_conf = {\"retry_count\": 2, \"max_retries\": 3, \"review_result\": {\"confidence\": 0.2}}
assert should_retry(test_retry_low_conf) == \"abort\"

# Test graph builds
graph = build_agent_graph()
print(f\"Graph compiled successfully: {type(graph).__name__}\")

# Test Orchestrator instantiation
# (cannot fully test without LLM, but verify structure)
print(\"Orchestrator class exists and is importable\")

print(\"LangGraph orchestrator verified\")
'
- cd backend && python -m ruff check app/agents/orchestrator.py --select E,F
Print 'TASK 2.9 COMPLETE — LangGraph orchestrator verified' when all pass.
"
```

---

### TASK 2.10 — Self-Repair Integration Test

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: Orchestrator in backend/app/agents/orchestrator.py. All agents available. Sandbox in backend/app/sandbox/.

Create integration tests that verify the self-repair loop works end-to-end. These tests mock the LLM but use real state machine transitions.

Create backend/tests/integration/test_self_repair.py:

1. Create MockLLMProvider that implements BaseLLMProvider:
   - Accepts a list of responses (LLMResponse objects) and returns them in order
   - This lets us simulate: planner response → coder response (buggy) → reviewer response → coder response (fixed)

2. Tests:

   test_successful_execution_no_repair:
   - Mock planner returns single-subtask plan
   - Mock coder returns correct code: 'print(42)'
   - Run orchestrator
   - Assert: status='completed', retry_count=0, final_code contains 'print(42)'

   test_self_repair_fixes_on_first_retry:
   - Mock planner returns plan
   - Mock coder returns buggy code: 'print(1/0)'
   - Mock reviewer returns fix with confidence=0.9 and fixed_code='print(42)'
   - Mock coder (second call) returns the fixed code
   - Run orchestrator
   - Assert: status='completed', retry_count=1

   test_self_repair_exhausts_retries:
   - Mock all coder responses to produce buggy code
   - Mock all reviewer responses with fixes that still fail
   - Run orchestrator with max_retries=3
   - Assert: status='failed', retry_count=3

   test_low_confidence_early_abort:
   - Mock reviewer returns confidence=0.2 on second attempt
   - Assert: status='failed', retry_count=2 (aborted early)

   test_state_transitions_are_recorded:
   - Run a successful task
   - Assert: traces list contains entries for classify, plan, code, execute, finalize
   - Each trace has agent_type, duration_ms > 0

   test_cost_accumulates_across_retries:
   - Run a task that requires 2 retries
   - Assert: total_cost_usd > 0, total_tokens > 0

Note: These tests need to mock both the LLM provider AND the sandbox executor (since we may not have Docker in CI). Create a MockSandboxExecutor that returns predetermined ExecutionOutput objects.

VALIDATION:
- cd backend && python -c 'import tests.integration.test_self_repair; print(\"Test file imports OK\")'
- cd backend && python -m pytest tests/integration/test_self_repair.py --collect-only 2>/dev/null | grep 'test_' | wc -l — should show 6+ tests
- cd backend && python -m ruff check tests/integration/test_self_repair.py --select E,F
Print 'TASK 2.10 COMPLETE — Self-repair integration tests verified' when all pass.
"
```

---

### TASK 2.11 — Unit Tests for All Agents

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: All agents in backend/app/agents/. Classifier in backend/app/llm/classifier.py. CostTracker in backend/app/llm/cost_tracker.py.

Create comprehensive unit tests for all agents and LLM utilities.

1. Create backend/tests/unit/test_planner.py:
   - test_planner_system_prompt_contains_key_instructions
   - test_planner_user_prompt_includes_task
   - test_validate_plan_valid: valid plan passes
   - test_validate_plan_missing_subtasks: fails gracefully
   - test_validate_plan_circular_dependency: detected and rejected
   - test_validate_plan_invalid_dependency_id: caught
   - test_validate_plan_empty_subtasks: rejected

2. Create backend/tests/unit/test_coder.py:
   - test_coder_user_prompt_includes_subtask
   - test_coder_user_prompt_includes_prior_code
   - test_validate_code_valid_python
   - test_validate_code_syntax_error
   - test_merge_code_deduplicates_imports
   - test_merge_code_preserves_functions
   - test_coder_prompt_for_integration_subtask

3. Create backend/tests/unit/test_reviewer.py:
   - test_reviewer_prompt_includes_error
   - test_reviewer_prompt_includes_attempt_info
   - test_validate_review_valid
   - test_validate_review_missing_keys
   - test_validate_review_invalid_confidence
   - test_validate_review_broken_fixed_code

4. Create backend/tests/unit/test_model_router.py:
   - test_simple_task_routes_to_ollama
   - test_complex_task_routes_to_gpt4
   - test_fallback_when_ollama_unavailable
   - test_available_providers_detection

5. Update backend/tests/unit/test_cost_tracker.py (replace placeholder):
   - test_gpt4_cost_calculation
   - test_llama_free_cost
   - test_unknown_model_uses_default
   - test_summary_aggregation
   - test_cost_by_model_breakdown
   - test_savings_calculation
   - test_reset_clears_all

All tests should:
- Be marked @pytest.mark.unit
- Use unittest.mock or pytest fixtures for LLM mocking
- Be independent (no shared state)
- Have descriptive names and docstrings

VALIDATION:
- cd backend && python -m pytest tests/unit/ --collect-only 2>&1 | grep 'test_' | wc -l — should show 30+ tests
- cd backend && python -m pytest tests/unit/ -v --tb=short -x 2>&1 | tail -20
- cd backend && python -m ruff check tests/unit/ --select E,F
Print 'TASK 2.11 COMPLETE — All unit tests verified' when all pass.
"
```

---

## PHASE 3: Real-Time & Observability (Tasks 3.1 – 3.5)

---

### TASK 3.1 — WebSocket Endpoint

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: FastAPI app in backend/app/main.py. Pydantic WS schemas in backend/app/models/schemas.py (WSEvent, WSAgentStarted, etc.). Orchestrator in backend/app/agents/orchestrator.py.

Create WebSocket endpoint for real-time agent streaming.

1. Create backend/app/api/websocket.py:

   class ConnectionManager:
       '''Manages WebSocket connections per task'''
       def __init__(self):
           self.active_connections: dict[str, list[WebSocket]] = {}  # task_id -> connections
       
       async def connect(self, websocket: WebSocket, task_id: str):
           await websocket.accept()
           if task_id not in self.active_connections:
               self.active_connections[task_id] = []
           self.active_connections[task_id].append(websocket)
       
       async def disconnect(self, websocket: WebSocket, task_id: str):
           self.active_connections[task_id].remove(websocket)
           if not self.active_connections[task_id]:
               del self.active_connections[task_id]
       
       async def broadcast_to_task(self, task_id: str, event: WSEvent):
           '''Send event to all connections watching a task'''
           if task_id in self.active_connections:
               dead = []
               for ws in self.active_connections[task_id]:
                   try:
                       await ws.send_json(event.model_dump(mode='json'))
                   except Exception:
                       dead.append(ws)
               for ws in dead:
                   await self.disconnect(ws, task_id)

   manager = ConnectionManager()  # Singleton

2. Create WebSocketAgentCallback implementing AgentCallback:
   '''Bridges agent events to WebSocket broadcasts'''
   def __init__(self, task_id: str, manager: ConnectionManager):
   
   on_agent_start: creates WSAgentStarted, broadcasts via manager
   on_agent_thinking: creates WSEvent with 'agent.thinking', broadcasts
   on_agent_complete: creates WSAgentCompleted, broadcasts
   on_agent_error: broadcasts error event
   
   Also add methods for execution events:
   on_execution_started, on_execution_stdout, on_execution_stderr, on_execution_completed
   on_repair_started, on_repair_fix_applied
   on_task_completed, on_task_failed

3. Create the WebSocket route:
   
   @router.websocket('/ws/tasks/{task_id}')
   async def task_websocket(websocket: WebSocket, task_id: str):
       await manager.connect(websocket, task_id)
       try:
           while True:
               data = await websocket.receive_json()
               # Handle client events (e.g., task.cancel)
               if data.get('event') == 'task.cancel':
                   # TODO: implement cancellation
                   pass
       except WebSocketDisconnect:
           await manager.disconnect(websocket, task_id)

4. Update backend/app/api/tasks.py POST /tasks:
   - After creating the task in DB, start the orchestrator as a background task
   - Pass WebSocketAgentCallback to the orchestrator
   - Return task_id immediately (client connects to WS to watch progress)

5. Add websocket router to main api router

VALIDATION:
- cd backend && python -c '
from app.api.websocket import ConnectionManager, WebSocketAgentCallback, manager
print(f\"ConnectionManager created: {type(manager).__name__}\")
print(f\"Active connections dict: {manager.active_connections}\")

from app.agents.base import AgentType
cb = WebSocketAgentCallback(task_id=\"test-123\", manager=manager)
print(f\"WebSocketAgentCallback created for task test-123\")
print(\"WebSocket infrastructure verified\")
'
- cd backend && python -c '
from app.main import app
ws_routes = [r for r in app.routes if hasattr(r, \"path\") and \"ws\" in str(getattr(r, \"path\", \"\"))]
print(f\"WebSocket routes found: {len(ws_routes)}\")
'
- cd backend && python -m ruff check app/api/websocket.py --select E,F
Print 'TASK 3.1 COMPLETE — WebSocket endpoint verified' when all pass.
"
```

---

### TASK 3.2 — Agent Streaming Integration

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: WebSocketAgentCallback in backend/app/api/websocket.py. Orchestrator in backend/app/agents/orchestrator.py. All agents have callback hooks via BaseAgent.

Wire the agent system to emit WebSocket events at every step.

1. Update backend/app/agents/orchestrator.py:
   - Each node function should accept and use an optional callback parameter
   - Use a factory/closure pattern to inject the callback into node functions:
     
     def create_nodes(settings, callback=None):
         '''Create node functions with injected dependencies'''
         model_router = ModelRouter(settings)
         cost_tracker = CostTracker()
         
         async def classify_node(state):
             if callback:
                 await callback.on_status_change(state['task_id'], 'classifying')
             complexity, model = await model_router.route(state['prompt'])
             return {'complexity': complexity, 'model_used': model, 'status': 'classifying'}
         
         # ... same pattern for all nodes
         return classify_node, plan_node, code_node, execute_node, review_node, apply_fix_node, finalize_node, fail_node

2. Update backend/app/agents/base.py BaseAgent.run():
   - Emit on_agent_start before execution
   - Emit on_agent_thinking during LLM streaming (if supported)
   - Emit on_agent_complete or on_agent_error after execution
   - All emissions should be async-safe

3. Update backend/app/sandbox/executor.py:
   - Add callback parameter to execute methods
   - Emit on_execution_started when container is created
   - Stream stdout/stderr lines via on_execution_stdout / on_execution_stderr
   - Emit on_execution_completed with results

4. Update backend/app/api/websocket.py WebSocketAgentCallback:
   - Add on_status_change(task_id, new_status) method
   - Add on_code_generated(task_id, code, language, subtask_index) method
   - Ensure all methods handle the case where no WS connections exist (no-op)

5. Update backend/app/api/tasks.py:
   - The POST /tasks endpoint should:
     a. Create task in DB
     b. Create WebSocketAgentCallback
     c. Create Orchestrator with the callback
     d. Use asyncio.create_task() to run orchestrator.run_task() in background
     e. When orchestrator completes: update task in DB with results

VALIDATION:
- cd backend && python -c '
from app.agents.orchestrator import Orchestrator, build_agent_graph
from app.api.websocket import WebSocketAgentCallback, ConnectionManager
from app.agents.base import NullCallback

# Verify callback integration
cb = NullCallback()
print(f\"NullCallback methods: {[m for m in dir(cb) if m.startswith(\"on_\")]}\")

# Verify orchestrator accepts callback
print(\"Streaming integration structure verified\")
'
- cd backend && python -m ruff check app/agents/ app/api/ app/sandbox/ --select E,F
Print 'TASK 3.2 COMPLETE — Agent streaming integration verified' when all pass.
"
```

---

### TASK 3.3 — OpenTelemetry Tracing

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: Observability module at backend/app/observability/. Dependencies: opentelemetry-api, opentelemetry-sdk, opentelemetry-instrumentation-fastapi, opentelemetry-exporter-otlp.

Create OpenTelemetry distributed tracing for all agents and key operations.

1. Create backend/app/observability/tracing.py:
   
   - setup_tracing(service_name: str, otlp_endpoint: str) -> None:
     * Create TracerProvider with Resource(service.name=service_name)
     * Add BatchSpanProcessor with OTLPSpanExporter(endpoint=otlp_endpoint)
     * Set as global tracer provider
     * Instrument FastAPI: FastAPIInstrumentor().instrument()
   
   - get_tracer(name: str) -> Tracer:
     * Return trace.get_tracer(name)
   
   - Helper decorator: @traced(name=None, attributes=None)
     * Creates a span for the decorated async function
     * Adds custom attributes
     * Records exceptions
     * Measures duration

2. Create backend/app/observability/metrics.py:
   
   - Custom metrics using OpenTelemetry Metrics API:
     * task_counter: Counter for tasks by status (completed, failed, repaired)
     * task_duration: Histogram for total task duration
     * agent_duration: Histogram for per-agent duration
     * llm_tokens: Counter for token usage by model
     * llm_cost: Counter for cost by model
     * repair_counter: Counter for repair attempts
     * sandbox_execution_time: Histogram for sandbox execution time
   
   - record_task_completion(status, duration_ms, model, cost, retries)
   - record_agent_execution(agent_type, duration_ms, tokens, cost)
   - record_sandbox_execution(duration_ms, exit_code, memory_mb)

3. Update backend/app/main.py lifespan:
   - Call setup_tracing() on startup
   - Pass service name and OTLP endpoint from settings

4. Update backend/app/agents/base.py:
   - Add @traced decorator to BaseAgent.run()
   - Add agent_type and task_id as span attributes

5. Update backend/app/sandbox/executor.py:
   - Add tracing to code execution

VALIDATION:
- cd backend && python -c '
from app.observability.tracing import setup_tracing, get_tracer, traced
print(\"Tracing module imported\")

from app.observability.metrics import (
    record_task_completion, record_agent_execution, record_sandbox_execution
)
print(\"Metrics module imported\")

# Test traced decorator exists and is callable
@traced(name=\"test_span\")
async def dummy(): return 42
print(\"@traced decorator works\")

print(\"OpenTelemetry tracing verified\")
'
- cd backend && python -m ruff check app/observability/ --select E,F
Print 'TASK 3.3 COMPLETE — OpenTelemetry tracing verified' when all pass.
"
```

---

### TASK 3.4 — [SKIP if no Docker] Jaeger + OTel Collector Config

Already created in Task 1.7 (docker/otel/otel-collector-config.yml and jaeger in docker-compose.yml). No separate task needed.

---

### TASK 3.5 — Cost Dashboard Data Endpoint

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: AgentTrace model has cost_usd, tokens_used, agent_type. Task model has total_cost_usd, model_used, created_at.

Add API endpoints for cost/performance analytics data.

1. Create backend/app/services/analytics_service.py:
   - AnalyticsService class taking AsyncSession
   - Methods:
     * get_cost_summary(days: int = 30) -> CostSummary:
       Query agent_traces, aggregate: total_cost, cost_by_model, cost_by_agent_type, daily_cost_timeseries
     * get_performance_summary(days: int = 30) -> PerformanceSummary:
       Query tasks: total_tasks, success_rate, avg_time_ms, avg_retries, tasks_by_status
     * get_model_distribution(days: int = 30) -> ModelDistribution:
       Query tasks: count by model_used, percentage breakdown

2. Add Pydantic schemas in backend/app/models/schemas.py:
   - CostSummary: total_cost_usd, cost_by_model(dict), cost_by_agent(dict), daily_costs(list of {date, cost})
   - PerformanceSummary: total_tasks, success_rate, avg_time_ms, avg_retries, tasks_by_status(dict)
   - ModelDistribution: distribution(list of {model, count, percentage})

3. Add to backend/app/api/router.py or create backend/app/api/analytics.py:
   - GET /analytics/cost?days=30 -> CostSummary
   - GET /analytics/performance?days=30 -> PerformanceSummary
   - GET /analytics/models?days=30 -> ModelDistribution

4. Include analytics router in main router

VALIDATION:
- cd backend && python -c '
from app.services.analytics_service import AnalyticsService
print(\"AnalyticsService imported\")
from app.models.schemas import CostSummary, PerformanceSummary, ModelDistribution
print(\"Analytics schemas imported\")
'
- cd backend && python -c '
from app.main import app
routes = [r.path for r in app.routes if hasattr(r, \"path\")]
analytics_routes = [r for r in routes if \"analytics\" in r]
print(f\"Analytics routes: {analytics_routes}\")
'
- cd backend && python -m ruff check app/ --select E,F
Print 'TASK 3.5 COMPLETE — Analytics endpoints verified' when all pass.
"
```

---

## PHASE 4: Frontend (Tasks 4.1 – 4.14)

---

### TASK 4.1 — Next.js Project Init

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)

Initialize the Next.js 14 frontend with TypeScript, Tailwind CSS, and shadcn/ui.

1. Create the Next.js app:
   cd frontend
   npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias '@/*' --no-turbo

2. Install dependencies:
   npm install @monaco-editor/react recharts reactflow lucide-react class-variance-authority clsx tailwind-merge
   npm install -D @types/node

3. Setup shadcn/ui:
   npx shadcn@latest init (accept defaults, use 'new-york' style, slate base color)
   npx shadcn@latest add button card input textarea badge tabs separator scroll-area dialog alert dropdown-menu select slider switch label toast

4. Create frontend/src/lib/utils.ts:
   import { type ClassValue, clsx } from 'clsx'
   import { twMerge } from 'tailwind-merge'
   export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }

5. Create frontend/src/lib/types.ts with ALL TypeScript types matching backend schemas:
   - TaskStatus type union
   - Task, TaskDetail, AgentTrace, ExecutionResult interfaces
   - BenchmarkRun, BenchmarkResult interfaces
   - AppSettings, LLMProviderSettings, RoutingSettings, SandboxSettings interfaces
   - WSEvent, all WS event data interfaces
   - PaginatedResponse<T> generic

6. Update frontend/src/app/globals.css with dark mode support + custom scrollbar styles

7. Verify it builds: npm run build

VALIDATION:
- cd frontend && npm run build 2>&1 | tail -5 — should succeed
- test -f frontend/src/lib/types.ts && echo 'Types file exists'
- test -d frontend/src/components/ui && echo 'shadcn components installed'
- grep 'recharts' frontend/package.json && echo 'recharts installed'
- grep 'monaco' frontend/package.json && echo 'monaco installed'
- grep 'reactflow' frontend/package.json && echo 'reactflow installed'
Print 'TASK 4.1 COMPLETE — Next.js frontend initialized' when all pass.
"
```

---

### TASK 4.2 — Layout, Sidebar, Navigation

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: Next.js 14 app in frontend/ with shadcn/ui, Tailwind, lucide-react installed.

Create the app shell with sidebar navigation, header, and dark mode.

1. Create frontend/src/components/layout/ThemeProvider.tsx:
   - Uses next-themes or manual dark mode toggle with localStorage
   - Wraps children with theme context

2. Create frontend/src/components/layout/Sidebar.tsx:
   - Fixed left sidebar (w-64, collapsible to w-16)
   - Logo/brand at top: '🔧 CodeForge'
   - Nav links using lucide-react icons:
     * MessageSquare → / (Chat)
     * History → /history
     * BarChart3 → /benchmarks
     * Settings → /settings
   - Active link highlighted with bg-accent
   - Collapse/expand toggle button at bottom
   - Dark mode toggle at bottom

3. Create frontend/src/components/layout/Header.tsx:
   - Top bar showing current page title
   - ConnectionStatus component: green dot if WS connected, red if disconnected
   - Breadcrumb if needed

4. Update frontend/src/app/layout.tsx:
   - Root layout with ThemeProvider, Sidebar, main content area
   - Use flex layout: sidebar on left, content takes remaining space
   - Include Toaster for notifications
   - Set metadata: title 'CodeForge', description

5. Create placeholder pages:
   - frontend/src/app/page.tsx (Chat — main page)
   - frontend/src/app/history/page.tsx
   - frontend/src/app/benchmarks/page.tsx
   - frontend/src/app/settings/page.tsx
   Each with just a heading for now

6. Design should be:
   - Dark theme by default (dark backgrounds, light text)
   - Clean, minimal, professional (think Linear/Vercel dashboard style)
   - Responsive: sidebar collapses on mobile

VALIDATION:
- cd frontend && npm run build 2>&1 | tail -3 — should succeed
- test -f frontend/src/components/layout/Sidebar.tsx && echo 'Sidebar exists'
- test -f frontend/src/components/layout/Header.tsx && echo 'Header exists'
- test -f frontend/src/app/history/page.tsx && echo 'History page exists'
- test -f frontend/src/app/benchmarks/page.tsx && echo 'Benchmarks page exists'
- test -f frontend/src/app/settings/page.tsx && echo 'Settings page exists'
Print 'TASK 4.2 COMPLETE — Layout and navigation verified' when all pass.
"
```

---

### TASK 4.3 — REST API Client + WebSocket Hook

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: Frontend types in frontend/src/lib/types.ts. Backend API at /api/v1/*.

Create typed API client and WebSocket hook.

1. Create frontend/src/lib/api.ts:
   - const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
   
   - Generic async fetcher with error handling:
     async function apiFetch<T>(path: string, options?: RequestInit): Promise<T>
   
   - Export functions for every endpoint:
     * createTask(prompt: string): Promise<{task_id: string, status: string}>
     * getTask(taskId: string): Promise<TaskDetail>
     * getTaskTraces(taskId: string): Promise<AgentTrace[]>
     * deleteTask(taskId: string): Promise<void>
     * getHistory(params: HistoryParams): Promise<PaginatedResponse<Task>>
     * getSettings(): Promise<AppSettings>
     * updateSettings(settings: Partial<AppSettings>): Promise<AppSettings>
     * testConnection(provider: string, apiKey?: string): Promise<{success: boolean, message: string}>
     * triggerBenchmark(type: string, withRepair: boolean): Promise<BenchmarkRun>
     * getBenchmarkRuns(): Promise<BenchmarkRun[]>
     * getBenchmarkRun(runId: string): Promise<BenchmarkRunDetail>
     * getCostSummary(days?: number): Promise<CostSummary>
     * getPerformanceSummary(days?: number): Promise<PerformanceSummary>
     * getModelDistribution(days?: number): Promise<ModelDistribution>

2. Create frontend/src/lib/ws.ts:
   - WebSocket URL builder from task_id
   - Event type constants

3. Create frontend/src/hooks/useWebSocket.ts:
   - Custom hook: useWebSocket(taskId: string | null)
   - Returns: { connected, events, lastEvent, error }
   - Features:
     * Auto-connect when taskId is provided
     * Auto-disconnect when taskId changes or component unmounts
     * Reconnect on disconnect with exponential backoff (max 3 retries)
     * Parse incoming events as WSEvent
     * Maintain event history array
     * Connection status tracking

4. Create frontend/src/hooks/useTask.ts:
   - Custom hook: useTask()
   - Returns: { submitTask, currentTaskId, taskDetail, isLoading, error }
   - submitTask(prompt: string): calls createTask, sets currentTaskId
   - Auto-fetches taskDetail when task completes
   - Integrates with useWebSocket for real-time updates

5. Create frontend/src/hooks/useBenchmarks.ts:
   - Custom hook for benchmark data fetching
   - Returns: { runs, currentRun, triggerRun, isLoading }

VALIDATION:
- cd frontend && npx tsc --noEmit 2>&1 | tail -10 — should have no type errors (or minimal)
- test -f frontend/src/lib/api.ts && echo 'API client exists'
- test -f frontend/src/hooks/useWebSocket.ts && echo 'WS hook exists'
- test -f frontend/src/hooks/useTask.ts && echo 'Task hook exists'
- cd frontend && npm run build 2>&1 | tail -3
Print 'TASK 4.3 COMPLETE — API client and hooks verified' when all pass.
"
```

---

### TASK 4.4 — Main Chat Interface (Core UI)

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: Frontend has hooks (useTask, useWebSocket), API client, shadcn/ui components, Monaco editor, types.

Build the main chat interface — the primary page users interact with.

1. Create frontend/src/components/chat/ChatInput.tsx:
   - Auto-resizing textarea (min 1 row, max 6 rows)
   - Submit button with Send icon (lucide-react)
   - Submit on Enter (Shift+Enter for newline)
   - Disabled state while task is running
   - Placeholder: 'Describe a coding task...'
   - Clean, minimal design

2. Create frontend/src/components/chat/CodeBlock.tsx:
   - Monaco Editor in read-only mode for code display
   - Language auto-detection (python default)
   - Copy to clipboard button (top-right corner)
   - Download as file button
   - Line numbers
   - Dark theme matching app
   - Compact: height auto-sizes to content (max 400px, scrollable)

3. Create frontend/src/components/agents/StatusBadge.tsx:
   - Colored badge for task/agent status
   - planning: blue, coding: purple, executing: yellow, reviewing: orange, repairing: red, completed: green, failed: red
   - Animated pulse for active states

4. Create frontend/src/components/agents/AgentCard.tsx:
   - Collapsible card for each agent's output
   - Shows: agent type icon, status badge, duration, cost
   - Expandable: reasoning text, full input/output data
   - Animated expand/collapse

5. Create frontend/src/components/execution/TerminalOutput.tsx:
   - Terminal-like dark panel
   - Monospace font
   - stdout lines in green (#4ade80)
   - stderr lines in red (#f87171)
   - Exit code display
   - Execution time + memory usage at bottom
   - Auto-scroll to bottom

6. Create frontend/src/components/execution/RepairDiff.tsx:
   - Side-by-side view when self-repair triggers
   - Left: original error (code + stderr)
   - Right: fixed code + new result
   - Retry number indicator
   - Animated transition when new retry appears

7. Create frontend/src/components/chat/TaskStream.tsx:
   - Main component that composes everything above
   - Renders events from useWebSocket in order:
     * agent.started → AgentCard appears
     * agent.thinking → streaming text in AgentCard
     * code.generated → CodeBlock appears
     * execution.started → TerminalOutput appears
     * execution.stdout/stderr → lines stream into terminal
     * repair.started → RepairDiff appears
     * task.completed → final code + output
     * task.failed → error display
   - Smooth auto-scrolling as new content appears

8. Update frontend/src/app/page.tsx:
   - Layout: full-height flex column
   - TaskStream takes most space (scrollable)
   - ChatInput fixed at bottom
   - Wire up useTask hook
   - Display initial welcome message when no task is running

VALIDATION:
- cd frontend && npm run build 2>&1 | tail -5 — should succeed
- test -f frontend/src/components/chat/ChatInput.tsx && echo 'ChatInput exists'
- test -f frontend/src/components/chat/CodeBlock.tsx && echo 'CodeBlock exists'
- test -f frontend/src/components/chat/TaskStream.tsx && echo 'TaskStream exists'
- test -f frontend/src/components/execution/TerminalOutput.tsx && echo 'Terminal exists'
- test -f frontend/src/components/execution/RepairDiff.tsx && echo 'RepairDiff exists'
- test -f frontend/src/components/agents/AgentCard.tsx && echo 'AgentCard exists'
Print 'TASK 4.4 COMPLETE — Main chat interface verified' when all pass.
"
```

---

### TASK 4.5 — Agent Flow Diagram

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: React Flow installed. Agent types: planner, coder, executor, reviewer. Self-repair loop exists.

Create a visual agent flow diagram showing the pipeline.

Create frontend/src/components/agents/AgentFlowDiagram.tsx:

- Uses reactflow library
- Shows 6 nodes in a flow:
  1. Classify (circle) → 2. Planner (rectangle) → 3. Coder (rectangle) → 4. Executor (rectangle)
  4 branches: Success → 5. Complete (green circle), Failure → 6. Reviewer (rectangle)
  6. Reviewer → 3. Coder (self-repair loop edge, dashed)
  After max retries: Reviewer → Failed (red circle)

- Props: activeAgent (string|null), status (string), retryCount (number)
- Active node highlighted with glow/pulse animation
- Completed nodes get green border
- Failed nodes get red border
- Edges animate when data flows between agents
- Self-repair loop edge shows retry count badge
- Clean dark theme matching the app

- Node styles:
  * Default: dark bg, subtle border
  * Active: bright border + pulse animation
  * Complete: green accent
  * Error: red accent

- Responsive: fits in a panel (collapsible)
- Include a legend showing what colors mean

Also create frontend/src/components/agents/AgentTimeline.tsx:
- Horizontal timeline showing agent execution order
- Each agent is a segment with proportional width based on duration
- Color-coded by agent type
- Hover to see details (duration, tokens, cost)
- Current agent has animated progress indicator

VALIDATION:
- cd frontend && npm run build 2>&1 | tail -3 — should succeed
- test -f frontend/src/components/agents/AgentFlowDiagram.tsx && echo 'Flow diagram exists'
- test -f frontend/src/components/agents/AgentTimeline.tsx && echo 'Timeline exists'
Print 'TASK 4.5 COMPLETE — Agent flow diagram verified' when all pass.
"
```

---

### TASK 4.6 — Benchmarks Dashboard Page

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: Recharts installed. API functions for benchmarks and analytics exist. Types defined.

Build the benchmarks dashboard page with charts and run controls.

1. Create frontend/src/components/benchmarks/PassRateChart.tsx:
   - Recharts BarChart
   - Groups: HumanEval, MBPP, Custom
   - Two bars per group: Baseline (blue) vs With Repair (green)
   - Y-axis: pass@1 percentage (0-100%)
   - Show repair lift as annotation
   - Responsive

2. Create frontend/src/components/benchmarks/CostAnalysis.tsx:
   - Recharts PieChart showing cost distribution by model
   - Show total cost prominently
   - Color per model (GPT-4: blue, Llama: green, Claude: orange)
   - Legend with percentages

3. Create frontend/src/components/benchmarks/ModelDistribution.tsx:
   - Recharts BarChart (horizontal)
   - Show % of tasks routed to each model
   - Show estimated savings vs all-GPT-4 baseline

4. Create frontend/src/components/benchmarks/HistoricalTrend.tsx:
   - Recharts LineChart
   - X-axis: benchmark run dates
   - Y-axis: pass@1
   - Lines for each benchmark type
   - Show improvement trend

5. Update frontend/src/app/benchmarks/page.tsx:
   - Page layout with:
     * Header: 'Benchmark Dashboard' + Run Benchmark button (dropdown: HumanEval, MBPP, Custom, All)
     * Stats cards at top: latest pass@1, total cost, avg retries
     * Grid of charts: PassRateChart, CostAnalysis (side by side)
     * ModelDistribution, HistoricalTrend (side by side)
     * Below: table of recent benchmark runs (click to see details)
   - Uses useBenchmarks hook for data
   - Loading skeletons while data loads
   - Empty state when no benchmarks have been run

VALIDATION:
- cd frontend && npm run build 2>&1 | tail -3 — should succeed
- test -f frontend/src/components/benchmarks/PassRateChart.tsx && echo 'PassRate chart exists'
- test -f frontend/src/components/benchmarks/CostAnalysis.tsx && echo 'Cost chart exists'
- test -f frontend/src/components/benchmarks/ModelDistribution.tsx && echo 'Model dist exists'
Print 'TASK 4.6 COMPLETE — Benchmarks dashboard verified' when all pass.
"
```

---

### TASK 4.7 — History Page

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)

Build the task history page with filtering, search, and detail view.

1. Create frontend/src/components/history/FilterBar.tsx:
   - Status dropdown: All, Completed, Failed, Repaired (multi-select)
   - Search input (debounced, searches in prompt text)
   - Date range picker (from/to)
   - Sort by dropdown: Date, Cost, Duration
   - Order toggle: Asc/Desc

2. Create frontend/src/components/history/TaskList.tsx:
   - Scrollable list of task cards
   - Each card shows: prompt preview (first 100 chars), status badge, model used, cost, duration, retry count, date
   - Click to select and view details
   - Pagination at bottom
   - Empty state: 'No tasks yet. Submit your first task!'

3. Create frontend/src/components/history/TaskDetail.tsx:
   - Expanded view of a selected task
   - Shows: full prompt, status, complexity, model, plan JSON (collapsible)
   - Agent trace timeline (reuse AgentTimeline component)
   - Final code (CodeBlock component)
   - Execution output (TerminalOutput component)
   - If repaired: show repair history with all attempts
   - Cost breakdown

4. Update frontend/src/app/history/page.tsx:
   - Two-panel layout: TaskList on left (40%), TaskDetail on right (60%)
   - FilterBar above TaskList
   - Responsive: on mobile, TaskList is full width, detail opens as overlay

VALIDATION:
- cd frontend && npm run build 2>&1 | tail -3
- test -f frontend/src/components/history/FilterBar.tsx && echo 'FilterBar exists'
- test -f frontend/src/components/history/TaskList.tsx && echo 'TaskList exists'
- test -f frontend/src/components/history/TaskDetail.tsx && echo 'TaskDetail exists'
Print 'TASK 4.7 COMPLETE — History page verified' when all pass.
"
```

---

### TASK 4.8 — Settings Page

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)

Build the settings page for configuring LLM providers, routing, and sandbox.

1. Create frontend/src/components/settings/LLMProviderForm.tsx:
   - OpenAI section: API key input (password field), model selector, test connection button
   - Anthropic section: same pattern
   - Ollama section: endpoint URL input, model selector, test connection button
   - Test buttons show: loading spinner → green check or red X with message
   - API keys are masked (show last 4 chars only)

2. Create frontend/src/components/settings/RoutingConfig.tsx:
   - Simple threshold slider (0.0 - 1.0)
   - Complex threshold slider (0.0 - 1.0)
   - Visual indicator showing: tasks below simple threshold → local model, above complex threshold → GPT-4, between → GPT-4o-mini
   - Model selector dropdowns for each tier

3. Create frontend/src/components/settings/SandboxConfig.tsx:
   - Timeout slider (5-120 seconds)
   - Memory limit slider (128-2048 MB)
   - Max retries slider (0-10)
   - Network disabled toggle

4. Update frontend/src/app/settings/page.tsx:
   - Tabbed layout: LLM Providers | Routing | Sandbox
   - Each tab loads corresponding form component
   - Save button at bottom (calls updateSettings API)
   - Toast notification on save success/failure
   - Loads current settings on mount

VALIDATION:
- cd frontend && npm run build 2>&1 | tail -3
- test -f frontend/src/components/settings/LLMProviderForm.tsx && echo 'LLM form exists'
- test -f frontend/src/components/settings/RoutingConfig.tsx && echo 'Routing config exists'
- test -f frontend/src/components/settings/SandboxConfig.tsx && echo 'Sandbox config exists'
Print 'TASK 4.8 COMPLETE — Settings page verified' when all pass.
"
```

---

### TASK 4.9 — Frontend Dockerfile

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)

Create production Dockerfile for the frontend.

Create frontend/Dockerfile:
   # Build stage
   FROM node:20-alpine AS builder
   WORKDIR /app
   COPY package.json package-lock.json ./
   RUN npm ci
   COPY . .
   ENV NEXT_TELEMETRY_DISABLED=1
   RUN npm run build
   
   # Production stage
   FROM node:20-alpine AS runner
   WORKDIR /app
   ENV NODE_ENV=production
   ENV NEXT_TELEMETRY_DISABLED=1
   RUN addgroup --system --gid 1001 nodejs
   RUN adduser --system --uid 1001 nextjs
   COPY --from=builder /app/public ./public
   COPY --from=builder /app/.next/standalone ./
   COPY --from=builder /app/.next/static ./.next/static
   USER nextjs
   EXPOSE 3000
   ENV PORT=3000
   CMD [\"node\", \"server.js\"]

Also update frontend/next.config.js to enable standalone output:
   output: 'standalone'

VALIDATION:
- test -f frontend/Dockerfile && echo 'Frontend Dockerfile exists'
- grep 'standalone' frontend/next.config.* && echo 'Standalone output configured'
- grep 'multi-stage\|builder\|AS runner' frontend/Dockerfile > /dev/null || grep 'FROM.*AS' frontend/Dockerfile && echo 'Multi-stage build'
Print 'TASK 4.9 COMPLETE — Frontend Docker verified' when all pass.
"
```

---

## PHASE 5: Benchmarks & Polish (Tasks 5.1 – 5.10)

---

### TASK 5.1 — HumanEval Benchmark Loader

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)

Create the HumanEval benchmark loader.

1. Create benchmarks/humaneval/loader.py:
   - download_humaneval(data_dir: str = 'benchmarks/humaneval/data') -> Path:
     * Download from: https://github.com/openai/human-eval (the HumanEval.jsonl.gz file)
     * Extract to data_dir
     * Return path to extracted .jsonl file
   
   - load_problems(path: str | None = None) -> list[HumanEvalProblem]:
     * If path not given, look in default data_dir (download if missing)
     * Parse each line of JSONL
     * Return list of HumanEvalProblem dataclasses
   
   - @dataclass HumanEvalProblem:
     * task_id: str (e.g., 'HumanEval/0')
     * prompt: str (function signature + docstring)
     * canonical_solution: str
     * test: str (test function)
     * entry_point: str (function name to test)

2. Create benchmarks/humaneval/evaluator.py:
   - evaluate_solution(problem: HumanEvalProblem, generated_code: str, sandbox: CodeExecutor) -> bool:
     * Combine generated_code + problem.test + call to check function
     * Execute in sandbox
     * Return True if exit_code == 0
   
   - calculate_pass_at_1(results: list[bool]) -> float:
     * Simple: count(True) / len(results)

VALIDATION:
- cd ~/codeforge && python -c '
from benchmarks.humaneval.loader import HumanEvalProblem, load_problems
from benchmarks.humaneval.evaluator import evaluate_solution, calculate_pass_at_1
print(\"HumanEval loader and evaluator imported\")

# Test dataclass
p = HumanEvalProblem(task_id=\"HumanEval/0\", prompt=\"def test():\", canonical_solution=\"pass\", test=\"assert True\", entry_point=\"test\")
print(f\"Problem: {p.task_id}\")

# Test pass@1 calculation
assert calculate_pass_at_1([True, True, False, True]) == 0.75
print(\"pass@1 calculation correct\")
'
Print 'TASK 5.1 COMPLETE — HumanEval loader verified' when all pass.
"
```

---

### TASK 5.2 — MBPP Benchmark Loader

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)

Create the MBPP benchmark loader (same pattern as HumanEval).

1. Create benchmarks/mbpp/loader.py:
   - @dataclass MBPPProblem:
     * task_id: int
     * text: str (task description)
     * code: str (reference solution)
     * test_list: list[str] (assertion strings)
     * test_setup_code: str
   
   - download_mbpp() and load_problems() following same pattern
   - MBPP dataset source: https://github.com/google-research/google-research/tree/master/mbpp

2. Create benchmarks/mbpp/evaluator.py:
   - Same pattern: evaluate_solution, calculate_pass_at_1

VALIDATION:
- cd ~/codeforge && python -c '
from benchmarks.mbpp.loader import MBPPProblem
from benchmarks.mbpp.evaluator import calculate_pass_at_1
print(\"MBPP loader verified\")
'
Print 'TASK 5.2 COMPLETE — MBPP loader verified' when all pass.
"
```

---

### TASK 5.3 — Benchmark Runner

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)
CONTEXT: HumanEval loader in benchmarks/humaneval/, MBPP loader in benchmarks/mbpp/, Orchestrator in backend/app/agents/orchestrator.py.

Create the benchmark runner that orchestrates evaluation.

Create benchmarks/runner.py:

1. BenchmarkRunner class:
   - __init__(self, settings, benchmark_type: str, with_repair: bool = True):
   
   - async run(self) -> BenchmarkRunResult:
     * Load problems based on benchmark_type
     * For each problem:
       - Create a task prompt from the problem
       - Run through Orchestrator (with or without repair based on with_repair flag)
       - Evaluate the generated code against test cases
       - Record: passed, retries_used, cost, time
       - Log progress: 'Problem {i}/{total}: {pass/fail}'
     * Calculate aggregate metrics
     * Save results to benchmarks/results/{type}_{timestamp}.json
     * Return BenchmarkRunResult
   
   - async run_single_problem(self, problem) -> ProblemResult:
     * Feed to orchestrator
     * Get generated code
     * Evaluate against tests
     * Return result

2. @dataclass BenchmarkRunResult:
   - benchmark_type: str
   - total_problems: int
   - passed: int
   - pass_at_1: float
   - pass_at_1_repair: float | None
   - avg_retries: float
   - total_cost_usd: float
   - total_time_seconds: float
   - per_problem_results: list[ProblemResult]

3. CLI entry point (__main__.py or argparse in runner.py):
   - python -m benchmarks.runner --type humaneval --with-repair --output results/
   - python -m benchmarks.runner --type mbpp --no-repair
   - python -m benchmarks.runner --type all

VALIDATION:
- cd ~/codeforge && python -c '
from benchmarks.runner import BenchmarkRunner, BenchmarkRunResult
print(\"BenchmarkRunner imported\")
'
- python -m benchmarks.runner --help 2>/dev/null || python -c 'from benchmarks.runner import BenchmarkRunner; print(\"Runner available\")'
Print 'TASK 5.3 COMPLETE — Benchmark runner verified' when all pass.
"
```

---

### TASK 5.4 — Custom Benchmark Tasks

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)

Create 25 custom multi-step benchmark tasks.

1. Create benchmarks/custom/tasks.json:
   Array of 25 tasks, each with:
   {
     \"id\": \"custom_01\",
     \"category\": \"data_processing\",
     \"description\": \"...\",
     \"difficulty\": \"medium\",
     \"test_assertions\": [\"assert ...\", \"assert ...\"],
     \"expected_imports\": [\"pandas\"],
     \"timeout_seconds\": 30
   }

   Categories and examples:
   - data_processing (5):
     * Read CSV, compute statistics, output summary
     * Merge two DataFrames on a key, handle missing values
     * Pivot table with aggregation
     * Time series resampling
     * Data normalization pipeline
   
   - algorithm (5):
     * BFS/DFS on a graph
     * Dynamic programming: longest common subsequence
     * Binary search with edge cases
     * Merge sort implementation
     * Dijkstra's shortest path
   
   - string_manipulation (3):
     * Regex-based log parser
     * Text tokenizer with special characters
     * Markdown to plain text converter
   
   - file_io (4):
     * JSON config reader/writer with validation
     * Log file analyzer (count errors, extract timestamps)
     * CSV to JSON converter
     * INI file parser
   
   - multi_step (5):
     * Build a calculator that handles operator precedence
     * Create a simple task scheduler with priorities
     * Implement a basic LRU cache
     * Build a URL shortener (in-memory)
     * Create a simple state machine parser
   
   - error_handling (3):
     * Retry decorator with exponential backoff
     * Input validation framework
     * Graceful degradation with fallback values

2. Create benchmarks/custom/evaluator.py:
   - Load tasks from tasks.json
   - Evaluate each against its assertions
   - Calculate pass@1

VALIDATION:
- cd ~/codeforge && python -c '
import json
with open(\"benchmarks/custom/tasks.json\") as f:
    tasks = json.load(f)
print(f\"Custom tasks: {len(tasks)}\")
assert len(tasks) >= 25, f\"Need 25 tasks, got {len(tasks)}\"
categories = set(t[\"category\"] for t in tasks)
print(f\"Categories: {categories}\")
assert len(categories) >= 5, f\"Need 5+ categories, got {len(categories)}\"
for t in tasks:
    assert \"test_assertions\" in t, f\"Task {t[\"id\"]} missing test_assertions\"
    assert len(t[\"test_assertions\"]) >= 1, f\"Task {t[\"id\"]} needs assertions\"
print(\"All 25 custom tasks validated\")
'
Print 'TASK 5.4 COMPLETE — Custom benchmark tasks verified' when all pass.
"
```

---

### TASK 5.5 — CI/CD Pipeline

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)

Create GitHub Actions CI/CD pipeline.

1. Create .github/workflows/ci.yml:
   name: CI
   on:
     push: {branches: [main, develop]}
     pull_request: {branches: [main]}
   
   jobs:
     lint-and-type-check:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with: {python-version: '3.11'}
         - run: pip install -e '.[dev]'
           working-directory: backend
         - run: ruff check app/ tests/
           working-directory: backend
         - run: mypy app/ --ignore-missing-imports
           working-directory: backend
     
     unit-tests:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with: {python-version: '3.11'}
         - run: pip install -e '.[dev]'
           working-directory: backend
         - run: pytest tests/unit -v --tb=short --junitxml=results/unit.xml
           working-directory: backend
         - uses: actions/upload-artifact@v4
           with: {name: test-results, path: backend/results/}
     
     integration-tests:
       runs-on: ubuntu-latest
       services:
         postgres:
           image: postgres:16
           env: {POSTGRES_USER: codeforge, POSTGRES_PASSWORD: codeforge, POSTGRES_DB: codeforge_test}
           ports: ['5432:5432']
           options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
         redis:
           image: redis:7
           ports: ['6379:6379']
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with: {python-version: '3.11'}
         - run: pip install -e '.[dev]'
           working-directory: backend
         - run: pytest tests/integration -v --tb=short
           working-directory: backend
           env:
             DATABASE_URL: postgresql+asyncpg://codeforge:codeforge@localhost:5432/codeforge_test
             REDIS_URL: redis://localhost:6379/0
     
     frontend-build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-node@v4
           with: {node-version: '20'}
         - run: npm ci
           working-directory: frontend
         - run: npm run build
           working-directory: frontend

2. Create .github/workflows/benchmark.yml:
   name: Weekly Benchmarks
   on:
     schedule: [{cron: '0 6 * * 1'}]  # Monday 6 AM UTC
     workflow_dispatch: {}  # Manual trigger
   
   jobs:
     run-benchmarks:
       runs-on: ubuntu-latest
       # ... full stack setup + benchmark execution

VALIDATION:
- test -f .github/workflows/ci.yml && echo 'CI workflow exists'
- test -f .github/workflows/benchmark.yml && echo 'Benchmark workflow exists'
- grep 'pytest' .github/workflows/ci.yml && echo 'Tests in CI'
- grep 'ruff' .github/workflows/ci.yml && echo 'Linting in CI'
- grep 'npm run build' .github/workflows/ci.yml && echo 'Frontend build in CI'
Print 'TASK 5.5 COMPLETE — CI/CD pipeline verified' when all pass.
"
```

---

### TASK 5.6 — Documentation

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)

Create comprehensive project documentation.

1. Create docs/architecture.md:
   - System overview with the ASCII architecture diagram
   - Component descriptions (Backend, Frontend, Agents, Sandbox, Observability)
   - Data flow description
   - State machine explanation with diagram
   - Model routing strategy
   - Sandbox security model
   - Cost optimization approach
   - Technology choices and rationale

2. Create docs/api.md:
   - Complete API reference for all endpoints
   - Request/response examples
   - WebSocket event catalog
   - Authentication (future)
   - Error codes

3. Create docs/agent-design.md:
   - Agent architecture overview
   - Each agent: role, prompts, inputs, outputs, state transitions
   - Self-repair loop detailed explanation
   - Prompt engineering decisions
   - How to add a new agent

4. Create docs/deployment.md:
   - Prerequisites (Docker, Node.js, Python)
   - Development setup (step by step)
   - Production deployment with Docker Compose
   - Environment configuration guide
   - Monitoring with Jaeger
   - Troubleshooting common issues

5. Update README.md with:
   - Professional header with badges (CI status, Python version, License)
   - Key features list (concise)
   - Architecture diagram (link to docs/architecture.md)
   - Quick start (5 commands to get running)
   - Screenshots placeholder
   - Benchmark results table (placeholder numbers)
   - Tech stack table
   - Contributing section
   - License (MIT)

VALIDATION:
- test -f docs/architecture.md && echo 'Architecture doc exists'
- test -f docs/api.md && echo 'API doc exists'
- test -f docs/agent-design.md && echo 'Agent design doc exists'
- test -f docs/deployment.md && echo 'Deployment doc exists'
- wc -l README.md | awk '{print \$1}' — should be 100+ lines
- grep 'Quick Start' README.md && echo 'README has quick start'
Print 'TASK 5.6 COMPLETE — Documentation verified' when all pass.
"
```

---

### TASK 5.7 — Final Integration Test

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)

Create the final end-to-end integration test.

Create backend/tests/e2e/test_full_pipeline.py:

1. test_full_task_lifecycle:
   - Use mock LLM providers (no real API calls)
   - Create FastAPI TestClient
   - POST /api/v1/tasks with prompt
   - Assert 201 response with task_id
   - GET /api/v1/tasks/{task_id} — poll until status != pending
   - Verify final status is 'completed' or 'failed'
   - If completed: verify final_code is not empty, total_cost >= 0
   - GET /api/v1/tasks/{task_id}/traces — verify traces exist
   - Verify traces have proper agent_type ordering

2. test_history_endpoint:
   - Create 3 tasks
   - GET /api/v1/history — verify all 3 appear
   - GET /api/v1/history?status=completed — verify filtering works
   - GET /api/v1/history?search=keyword — verify search works

3. test_settings_crud:
   - GET /api/v1/settings — verify defaults
   - PUT /api/v1/settings with new routing thresholds
   - GET /api/v1/settings — verify updated

4. test_health_endpoint:
   - GET /api/v1/health — verify 200

Use httpx.AsyncClient with the FastAPI app directly (no need for running server).

VALIDATION:
- cd backend && python -c 'import tests.e2e.test_full_pipeline; print(\"E2E tests import OK\")'
- cd backend && python -m pytest tests/e2e/ --collect-only 2>&1 | grep 'test_' | wc -l — should show 4+ tests
Print 'TASK 5.7 COMPLETE — E2E tests verified' when all pass.
"
```

---

## POST-BUILD: Final Validation Checklist

```bash
cd ~/codeforge && claude --permission-mode bypass "

PROJECT: CodeForge — AI Code Agent with Self-Repair
WORKING DIRECTORY: $(pwd)

Run a comprehensive validation of the entire project. Check EVERYTHING and report status.

1. STRUCTURE CHECK:
   - Verify all directories exist
   - Count .py files in backend/app/
   - Count .tsx files in frontend/src/
   - Verify no empty files (except __init__.py)

2. BACKEND CHECKS:
   - cd backend && python -m ruff check app/ --select E,F
   - cd backend && python -m pytest tests/ --collect-only | grep 'test_' | wc -l (should be 40+)
   - cd backend && python -c 'from app.main import app; print(len(app.routes))' (should be 15+)
   - cd backend && python -c 'from app.agents.orchestrator import build_agent_graph; g = build_agent_graph(); print(type(g))'
   - cd backend && python -c 'from app.models.database import Base; print(len(Base.metadata.tables))'

3. FRONTEND CHECKS:
   - cd frontend && npm run build
   - Count .tsx component files

4. DOCKER CHECKS:
   - Verify docker-compose.yml has all 7 services
   - Verify all Dockerfiles exist
   - Verify .env.example has all variables

5. DOCS CHECK:
   - Verify all 4 docs exist and are non-empty
   - Verify README is comprehensive

6. BENCHMARKS CHECK:
   - Verify custom tasks.json has 25+ tasks
   - Verify all loaders import

Print a FINAL REPORT showing:
✅ or ❌ for each check
Total: X/Y checks passed

If all pass: 'PROJECT CODEFORGE IS COMPLETE AND PRODUCTION-READY 🚀'
"
```

---

## PARALLEL EXECUTION GUIDE

You can run tasks in parallel across multiple terminal windows:

**Terminal 1 (Backend Core):** Tasks 1.1 → 1.2 → 1.3 → 1.4 → 1.5

**Terminal 2 (Infra — can start after 1.1):** Tasks 1.7 → 1.8 → 1.11

**Terminal 3 (Frontend — can start after 1.1):** Tasks 4.1 → 4.2 → 4.3

After Phase 1 completes in all terminals:

**Terminal 1 (Agents):** Tasks 2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 2.6 → 2.7 → 2.8 → 2.9

**Terminal 2 (Frontend UI):** Tasks 4.4 → 4.5 → 4.6 → 4.7 → 4.8 → 4.9

**Terminal 3 (Tests):** Tasks 1.10 → 1.12 (then wait for Phase 2, then 2.10 → 2.11)

After Phase 2+3:

**Terminal 1 (Benchmarks):** Tasks 5.1 → 5.2 → 5.3 → 5.4

**Terminal 2 (Polish):** Tasks 5.5 → 5.6 → 5.7

**Terminal 3 (Real-time):** Tasks 3.1 → 3.2 → 3.3 → 3.5
