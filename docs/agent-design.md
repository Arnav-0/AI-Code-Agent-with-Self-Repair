# Agent Design

## Architecture Overview

CodeForge uses four specialized agents coordinated by a LangGraph state machine. Each agent is stateless and communicates through a shared `AgentState` dict passed between graph nodes.

```
AgentState (TypedDict)
├── prompt, task_id
├── complexity, model_used
├── plan, current_subtask_index
├── code_segments, integrated_code
├── execution_result, execution_success
├── review_result, retry_count, max_retries
├── total_cost_usd, total_tokens, traces
└── error_message, status
```

All agents inherit from `BaseAgent` which provides the template method pattern: `run()` calls `_execute()` (implemented by subclasses), wraps it in timing/cost tracking, and returns a standardized `AgentOutput`.

---

## PlannerAgent

**File:** `backend/app/agents/planner.py`
**Role:** Decompose the user's prompt into a DAG of subtasks.

**Input:**
```python
AgentInput(data={"prompt": str}, task_id=str, step_order=1)
```

**Output:**
```json
{
  "subtasks": [
    {
      "id": 1,
      "description": "...",
      "dependencies": [],
      "estimated_complexity": "simple|medium|complex"
    }
  ],
  "reasoning": "..."
}
```

**Prompt strategy:** System prompt instructs the model to produce valid JSON matching the schema. The user message is the raw task description. Subtasks are topologically sorted; cycles are detected and the plan is re-requested if found.

**State transitions:** On success: `plan` is populated and execution continues to `code`. On failure: `plan` is None, which causes `code` to skip all subtasks (empty `code_segments`).

---

## CoderAgent

**File:** `backend/app/agents/coder.py`
**Role:** Implement one subtask at a time, producing syntactically valid Python.

**Input:**
```python
AgentInput(data={
    "subtask": dict,       # current subtask
    "plan": dict,          # full plan for context
    "prior_code": dict,    # {subtask_id: code} already generated
}, ...)
```

**Output:**
```json
{
  "code": "def solution():\n    ...",
  "imports": ["os", "re"],
  "explanation": "..."
}
```

**Validation:** After generation, code is passed through Python's `ast.parse()`. If it raises `SyntaxError`, the agent returns an empty code segment and logs a warning (rather than crashing).

**Integration:** The orchestrator runs the coder for each subtask in plan order. The final `integrated_code` is the last generated segment (which should import/call previous segments as needed).

---

## ReviewerAgent

**File:** `backend/app/agents/reviewer.py`
**Role:** Analyze execution failures and generate a fixed version of the code.

**Input:**
```python
AgentInput(data={
    "code": str,           # the failing code
    "error": dict,         # execution_result with stderr/stdout/exit_code
    "attempt": int,        # current retry attempt number
    "max_attempts": int,
    "original_task": str,  # the user's original prompt
}, ...)
```

**Output:**
```json
{
  "root_cause": "...",
  "error_type": "syntax_error|runtime_error|logic_error|timeout",
  "fix_description": "...",
  "fixed_code": "...",
  "confidence": 0.85,
  "changes_made": ["Fixed off-by-one error in loop"]
}
```

**Confidence score:** A float [0.0, 1.0] indicating how confident the reviewer is that the fix will succeed. If confidence < 0.3 after 2+ attempts, the orchestrator aborts early rather than wasting retries.

---

## Orchestrator

**File:** `backend/app/agents/orchestrator.py`
**Role:** LangGraph state machine coordinating the full pipeline.

**Key functions:**
- `build_agent_graph(settings, callback)` — constructs and compiles the graph
- `Orchestrator.run_task(task_id, prompt)` — invokes the compiled graph

**Callback interface:** The orchestrator accepts an optional callback object with async methods: `on_status_change`, `on_code_generated`, `on_execution_started`, `on_execution_completed`, `on_repair_started`, `on_repair_fix_applied`, `on_task_completed`, `on_task_failed`. The `WebSocketAgentCallback` in `api/websocket.py` implements this to broadcast events to connected WebSocket clients.

**Retry logic:**

```python
def should_retry(state) -> "retry" | "abort":
    if retry_count >= max_retries:
        return "abort"
    if confidence < 0.3 and retry_count >= 2:
        return "abort"
    return "retry"
```

**Exponential backoff:** `apply_fix` node sleeps `2^(retry_count-1)` seconds (capped at 8s) before re-executing.

---

## Self-Repair Loop Explained

```
1. code → execute(code) → FAIL
2. execute → review(code, error) → {fixed_code, confidence}
3. review → apply_fix → execute(fixed_code)
4. If passes: finalize
5. If fails again: review(fixed_code, new_error) → ...
6. After max_retries or low confidence: fail
```

The reviewer sees:
- The failing code
- The full error output (stderr + stdout)
- Which attempt this is (so it can be more aggressive on later attempts)
- The original task description (so it can check for logic errors too)

---

## Prompt Engineering Decisions

1. **JSON-only output:** All agent prompts instruct the model to respond with valid JSON only, no markdown fences or explanations outside the JSON object. This makes parsing reliable.

2. **System + user separation:** System prompts define the agent's role and output format. User messages contain the actual task data. This separation improves instruction following.

3. **Context windowing:** Prior code segments are passed to the coder so it can build on previous work. The reviewer receives the full execution trace, not just the exit code.

4. **Temperature:** Planner and reviewer use `temperature=0.2` for more deterministic structured output. Coder uses `temperature=0.3` to allow some creativity.

---

## Adding a New Agent

1. Create `backend/app/agents/my_agent.py` subclassing `BaseAgent`
2. Implement `_execute(self, input: AgentInput) -> AgentOutput`
3. Create `backend/app/agents/prompts/my_agent.py` with `SYSTEM_PROMPT` and `build_user_prompt()`
4. Add a new node function in `orchestrator.py` using `_create_node_functions`
5. Register it in `build_agent_graph()` with `graph.add_node("my_agent", my_agent_node)`
6. Add edges from/to the new node
