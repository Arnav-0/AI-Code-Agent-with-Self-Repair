# Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose v2
- Python 3.11+
- Node.js 20+
- 4 GB RAM minimum (8 GB recommended for running local LLMs)

---

## Development Setup

### 1. Clone and configure

```bash
git clone https://github.com/yourorg/codeforge.git
cd codeforge
cp .env.example .env
# Edit .env with your API keys and settings
```

### 2. Start infrastructure

```bash
docker compose -f docker-compose.dev.yml up -d postgres redis jaeger
```

### 3. Run database migrations

```bash
cd backend
pip install -e '.[dev]'
alembic upgrade head
```

### 4. Start the backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Access the app at `http://localhost:3000`.
API docs at `http://localhost:8000/docs`.

---

## Production Deployment with Docker Compose

### 1. Build all images

```bash
docker compose build
```

### 2. Start all services

```bash
docker compose up -d
```

This starts 7 services:
- `backend` — FastAPI on port 8000
- `frontend` — Next.js on port 3000
- `postgres` — PostgreSQL 16 on port 5432
- `redis` — Redis 7 on port 6379
- `jaeger` — Jaeger tracing UI on port 16686
- `sandbox` — Python sandbox image (pulled on first use)
- `ollama` — Local LLM server on port 11434 (optional)

### 3. Run migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Verify

```bash
curl http://localhost:8000/api/v1/health
```

---

## Environment Configuration

Key variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://codeforge:codeforge@postgres:5432/codeforge
DATABASE_SYNC_URL=postgresql://codeforge:codeforge@postgres:5432/codeforge

# Redis
REDIS_URL=redis://redis:6379/0

# LLM providers (at least one required for cloud tasks)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_BASE_URL=http://ollama:11434

# Routing thresholds
COMPLEXITY_SIMPLE_THRESHOLD=0.3
COMPLEXITY_COMPLEX_THRESHOLD=0.7
DEFAULT_SIMPLE_MODEL=llama3:8b
DEFAULT_COMPLEX_MODEL=gpt-4

# Sandbox
SANDBOX_IMAGE=codeforge-sandbox-python:latest
SANDBOX_TIMEOUT_SECONDS=30
SANDBOX_MEMORY_LIMIT_MB=512
SANDBOX_CPU_LIMIT=1.0
SANDBOX_NETWORK_DISABLED=true
MAX_REPAIR_RETRIES=3

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
OTEL_SERVICE_NAME=codeforge-backend
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security
SECRET_KEY=change-me-in-production
CORS_ORIGINS=http://localhost:3000
```

---

## Monitoring with Jaeger

Open `http://localhost:16686` to view distributed traces.

Each task creates a trace with spans for:
- HTTP request handling
- Each agent node (classify, plan, code, execute, review)
- Database queries
- LLM API calls

Filter by service `codeforge-backend` and operation `POST /api/v1/tasks/`.

---

## Troubleshooting

**Backend fails to start — "Cannot connect to PostgreSQL"**
```bash
docker compose ps postgres   # check if postgres is healthy
docker compose logs postgres  # check for startup errors
```

**Sandbox execution times out**
- Increase `SANDBOX_TIMEOUT_SECONDS` in `.env`
- Check Docker daemon is running: `docker info`
- Ensure the sandbox image is built: `docker build -t codeforge-sandbox-python:latest docker/sandbox/`

**Ollama models not loading**
```bash
docker compose exec ollama ollama pull llama3:8b
```

**Redis connection errors**
```bash
docker compose ps redis
docker compose exec redis redis-cli ping   # should return PONG
```

**Frontend cannot reach backend**
- Check `NEXT_PUBLIC_API_URL` in `frontend/.env.local` points to `http://localhost:8000`
- Verify CORS_ORIGINS includes the frontend URL

**Alembic migration fails**
```bash
# Reset and re-run
docker compose exec backend alembic downgrade base
docker compose exec backend alembic upgrade head
```
