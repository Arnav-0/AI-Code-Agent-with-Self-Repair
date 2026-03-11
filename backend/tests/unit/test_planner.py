"""Unit tests for the Planner agent."""

from __future__ import annotations

import pytest

from app.agents.planner import PlannerAgent
from app.agents.prompts.planner import PLANNER_SYSTEM_PROMPT, build_planner_user_prompt


@pytest.mark.unit
def test_planner_system_prompt_contains_key_instructions() -> None:
    """System prompt should include critical JSON schema instructions."""
    assert "subtasks" in PLANNER_SYSTEM_PROMPT
    assert "JSON" in PLANNER_SYSTEM_PROMPT
    assert "dependencies" in PLANNER_SYSTEM_PROMPT
    assert "integration" in PLANNER_SYSTEM_PROMPT.lower() or "main()" in PLANNER_SYSTEM_PROMPT


@pytest.mark.unit
def test_planner_user_prompt_includes_task() -> None:
    """User prompt should embed the provided task description."""
    task = "Build a binary search tree"
    prompt = build_planner_user_prompt(task)
    assert task in prompt


@pytest.mark.unit
def test_validate_plan_valid() -> None:
    """A well-formed plan with valid dependencies passes validation."""
    from unittest.mock import MagicMock
    agent = PlannerAgent(MagicMock(), MagicMock())
    plan = {
        "subtasks": [
            {"id": 1, "description": "Fetch data", "dependencies": [], "estimated_complexity": "simple"},
            {"id": 2, "description": "Process", "dependencies": [1], "estimated_complexity": "medium"},
            {"id": 3, "description": "Main", "dependencies": [1, 2], "estimated_complexity": "simple"},
        ],
        "reasoning": "Three-step pipeline",
    }
    valid, msg = agent._validate_plan(plan)
    assert valid, f"Expected valid, got error: {msg}"


@pytest.mark.unit
def test_validate_plan_missing_subtasks() -> None:
    """Plan without 'subtasks' key fails validation."""
    from unittest.mock import MagicMock
    agent = PlannerAgent(MagicMock(), MagicMock())
    valid, msg = agent._validate_plan({"reasoning": "no subtasks"})
    assert not valid
    assert "subtasks" in msg.lower()


@pytest.mark.unit
def test_validate_plan_circular_dependency() -> None:
    """Plan with circular deps (A -> B -> A) is rejected."""
    from unittest.mock import MagicMock
    agent = PlannerAgent(MagicMock(), MagicMock())
    plan = {
        "subtasks": [
            {"id": 1, "description": "A", "dependencies": [2], "estimated_complexity": "simple"},
            {"id": 2, "description": "B", "dependencies": [1], "estimated_complexity": "simple"},
        ]
    }
    valid, msg = agent._validate_plan(plan)
    assert not valid
    assert "circular" in msg.lower() or "cycle" in msg.lower()


@pytest.mark.unit
def test_validate_plan_invalid_dependency_id() -> None:
    """Dependency referencing non-existent subtask ID fails."""
    from unittest.mock import MagicMock
    agent = PlannerAgent(MagicMock(), MagicMock())
    plan = {
        "subtasks": [
            {"id": 1, "description": "Step 1", "dependencies": [99], "estimated_complexity": "simple"},
        ]
    }
    valid, msg = agent._validate_plan(plan)
    assert not valid
    assert "99" in msg or "unknown" in msg.lower()


@pytest.mark.unit
def test_validate_plan_empty_subtasks() -> None:
    """Plan with empty subtasks list fails validation."""
    from unittest.mock import MagicMock
    agent = PlannerAgent(MagicMock(), MagicMock())
    valid, msg = agent._validate_plan({"subtasks": []})
    assert not valid
