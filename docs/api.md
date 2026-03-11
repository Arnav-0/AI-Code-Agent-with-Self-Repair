# API Reference

Base URL: `http://localhost:8000/api/v1`

All responses are JSON. Timestamps are ISO 8601 UTC strings.

## Health

### GET /health

Check API and dependency health.

**Response 200:**
```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok",
  "version": "0.1.0"
}
```

---

## Tasks

### POST /tasks/

Create a new code-generation task and start the agent pipeline.

**Request:**
```json
{ "prompt": "Write a function that computes fibonacci numbers" }
```

**Response 201:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "prompt": "Write a function that computes fibonacci numbers",
  "status": "pending",
  "complexity": null,
  "model_used": null,
  "total_cost_usd": 0.0,
  "total_time_ms": null,
  "retry_count": 0,
  "error_message": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Status values:** `pending`, `classifying`, `planning`, `coding`, `executing`, `reviewing`, `repairing`, `completed`, `failed`

---

### GET /tasks/{task_id}

Get full task details including generated code and traces.

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "prompt": "...",
  "status": "completed",
  "complexity": "medium",
  "model_used": "gpt-4",
  "total_cost_usd": 0.0032,
  "total_time_ms": 4521,
  "retry_count": 1,
  "error_message": null,
  "plan": { "subtasks": [...] },
  "final_code": "def fibonacci(n):\n    ...",
  "final_output": "Test passed",
  "traces": [
    {
      "id": "...",
      "task_id": "...",
      "agent_type": "planner",
      "input_data": { "prompt": "..." },
      "output_data": { "subtasks": [...] },
      "tokens_used": 450,
      "cost_usd": 0.0009,
      "duration_ms": 1200,
      "step_order": 1,
      "created_at": "..."
    }
  ],
  "created_at": "...",
  "updated_at": "..."
}
```

---

### GET /tasks/{task_id}/traces

Get all agent traces for a task.

**Response 200:** `list[AgentTraceResponse]`

---

### DELETE /tasks/{task_id}

Delete a task and all related data.

**Response 200:**
```json
{ "success": true }
```

---

## History

### GET /history/

List all tasks with filtering and pagination.

**Query parameters:**

| Parameter  | Type   | Default    | Description                          |
|------------|--------|------------|--------------------------------------|
| status     | string | null       | Filter by status                     |
| search     | string | null       | Full-text search in prompt           |
| date_from  | datetime | null     | Filter tasks created after this date |
| date_to    | datetime | null     | Filter tasks created before this date|
| sort_by    | string | created_at | Field to sort by                     |
| order      | string | desc       | Sort order: `asc` or `desc`          |
| page       | int    | 1          | Page number (1-indexed)              |
| per_page   | int    | 20         | Items per page (1–100)               |

**Response 200:**
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "total_pages": 3
}
```

---

## Benchmarks

### POST /benchmarks/run

Start a benchmark run.

**Request:**
```json
{
  "type": "humaneval",
  "with_repair": true
}
```

`type` must be one of: `humaneval`, `mbpp`, `custom`

**Response 201:** `BenchmarkRunResponse`

---

### GET /benchmarks/runs

List all benchmark runs.

**Response 200:** `list[BenchmarkRunResponse]`

---

### GET /benchmarks/runs/{run_id}

Get a benchmark run with per-problem results.

**Response 200:** `BenchmarkRunDetail`

---

## Settings

### GET /settings/

Get current application settings.

**Response 200:**
```json
{
  "llm": {
    "openai_api_key": null,
    "anthropic_api_key": null,
    "ollama_endpoint": "http://localhost:11434"
  },
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

---

### PUT /settings/

Update application settings. All fields are optional (partial update).

**Request:** Same structure as GET response, all fields optional.

---

### POST /settings/test-connection

Test connectivity to an LLM provider.

**Request:**
```json
{
  "provider": "openai",
  "api_key": "sk-...",
  "endpoint": null
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Connection successful",
  "latency_ms": 342
}
```

---

## Analytics

### GET /analytics/cost

Get cost analytics.

### GET /analytics/performance

Get performance analytics (latency, success rates).

### GET /analytics/models

Get per-model usage statistics.

---

## WebSocket

### WS /ws/tasks/{task_id}

Subscribe to real-time events for a task.

**Event types:**

| Event               | Payload fields                                     |
|---------------------|----------------------------------------------------|
| status_change       | `task_id`, `status`                               |
| code_generated      | `task_id`, `code`, `language`, `subtask_id`       |
| execution_started   | `task_id`, `container_id`, `attempt`              |
| execution_completed | `task_id`, `exit_code`, `duration_ms`, `memory_mb`|
| repair_started      | `task_id`, `attempt`, `error_summary`             |
| repair_fix_applied  | `task_id`, `fixed_code`, `change_summary`         |
| task_completed      | `task_id`, `final_code`, `output`, `cost_usd`     |
| task_failed         | `task_id`, `error`, `retry_count`                 |

**Example message:**
```json
{
  "event": "status_change",
  "task_id": "550e8400-...",
  "status": "coding",
  "timestamp": "2024-01-15T10:30:05Z"
}
```

---

## Error Codes

| HTTP Status | Meaning                          |
|-------------|----------------------------------|
| 400         | Validation error (bad request)   |
| 404         | Resource not found               |
| 422         | Unprocessable entity             |
| 500         | Internal server error            |
