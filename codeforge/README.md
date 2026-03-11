# CodeForge

**AI Code Agent with Self-Repair** — generates, executes, and autonomously repairs Python code using a multi-agent LangGraph pipeline.

[![CI](https://github.com/yourorg/codeforge/actions/workflows/ci.yml/badge.svg)](https://github.com/yourorg/codeforge/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Key Features

- **Multi-agent pipeline**: Planner → Coder → Executor → Reviewer in a LangGraph state machine
- **Self-repair loop**: Automatically analyzes failures and retries with LLM-generated fixes (up to N retries)
- **Smart model routing**: Routes simple tasks to local Ollama (free) and complex tasks to OpenAI/Anthropic
- **Sandboxed execution**: Docker-isolated Python runtime with configurable memory/CPU/timeout limits
- **Real-time updates**: WebSocket-based task progress streaming to the Next.js dashboard
- **Full observability**: OpenTelemetry traces, structured JSON logging, cost tracking

## Architecture

```
User Prompt → FastAPI → LangGraph State Machine
                              │
              classify → plan → code → execute
                                          │
                              apply_fix ← review ← failure
                                          │
                                      finalize → Done
```

See [docs/architecture.md](docs/architecture.md) for the full system diagram and design decisions.

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/yourorg/codeforge.git && cd codeforge
cp .env.example .env   # add your API keys

# 2. Start infrastructure
docker compose up -d

# 3. Run migrations
docker compose exec backend alembic upgrade head

# 4. Open the dashboard
open http://localhost:3000
```

> For development setup (without Docker), see [docs/deployment.md](docs/deployment.md).

## Benchmark Results

| Benchmark   | pass@1 (no repair) | pass@1 (with repair) | Avg Retries |
|-------------|-------------------|----------------------|-------------|
| HumanEval   | TBD               | TBD                  | TBD         |
| MBPP        | TBD               | TBD                  | TBD         |
| Custom (25) | TBD               | TBD                  | TBD         |

*Benchmarks run weekly via GitHub Actions. See `.github/workflows/benchmark.yml`.*

## Tech Stack

| Layer         | Technology                           |
|---------------|--------------------------------------|
| Backend       | Python 3.11, FastAPI, SQLAlchemy     |
| Agent runtime | LangGraph, Pydantic v2               |
| Database      | PostgreSQL 16, Redis 7               |
| Sandbox       | Docker SDK, asyncio                  |
| LLMs          | OpenAI, Anthropic, Ollama (local)    |
| Observability | OpenTelemetry, Jaeger, structlog     |
| Frontend      | Next.js 14, TypeScript, Tailwind CSS |
| CI/CD         | GitHub Actions                       |

## Documentation

- [Architecture](docs/architecture.md) — system design, data flow, state machine
- [API Reference](docs/api.md) — all endpoints, schemas, WebSocket events
- [Agent Design](docs/agent-design.md) — agent internals, prompts, adding new agents
- [Deployment](docs/deployment.md) — dev setup, Docker Compose, env config, troubleshooting

## Project Structure

```
codeforge/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── agents/       # PlannerAgent, CoderAgent, ReviewerAgent, Orchestrator
│   │   ├── api/          # REST endpoints + WebSocket
│   │   ├── llm/          # LLM providers, router, cost tracker
│   │   ├── sandbox/      # Docker execution manager
│   │   ├── services/     # Business logic layer
│   │   └── observability/# Logging, tracing, metrics
│   └── tests/            # Unit, integration, E2E tests
├── frontend/             # Next.js dashboard
├── benchmarks/           # HumanEval, MBPP, custom evaluators
├── docs/                 # Architecture, API, deployment docs
├── docker/               # Dockerfiles
└── .github/workflows/    # CI/CD pipelines
```

## Running Tests

```bash
cd backend

# Unit tests
pytest tests/unit -v

# Integration tests (requires Docker)
pytest tests/integration -v

# E2E tests
pytest tests/e2e -v

# All tests with coverage
pytest --cov=app --cov-report=html
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Run linting: `cd backend && python -m ruff check app/ tests/`
4. Run tests: `pytest tests/unit`
5. Submit a pull request

## License

MIT — see [LICENSE](LICENSE).
