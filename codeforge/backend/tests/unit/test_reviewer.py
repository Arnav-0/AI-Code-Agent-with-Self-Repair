"""Unit tests for the Reviewer agent."""

from __future__ import annotations

import pytest

from app.agents.prompts.reviewer import build_reviewer_user_prompt
from app.agents.reviewer import ReviewerAgent


@pytest.mark.unit
def test_reviewer_prompt_includes_error() -> None:
    """Review prompt should embed the error output."""
    prompt = build_reviewer_user_prompt(
        code="x = 1/0",
        error={"exit_code": 1, "stdout": "", "stderr": "ZeroDivisionError"},
        attempt=1, max_attempts=3, original_task="Compute ratio"
    )
    assert "ZeroDivisionError" in prompt


@pytest.mark.unit
def test_reviewer_prompt_includes_attempt_info() -> None:
    """Review prompt should show current attempt vs max attempts."""
    prompt = build_reviewer_user_prompt(
        code="pass",
        error={"exit_code": 2, "stdout": "", "stderr": "Error"},
        attempt=2, max_attempts=5, original_task="Task"
    )
    assert "2 of 5" in prompt


@pytest.mark.unit
def test_validate_review_valid() -> None:
    """A well-formed review with all required keys passes."""
    from unittest.mock import MagicMock
    agent = ReviewerAgent(MagicMock(), MagicMock())
    review = {
        "root_cause": "Division by zero",
        "error_type": "runtime_error",
        "fix_description": "Avoid zero division",
        "fixed_code": "print(42)",
        "confidence": 0.85,
        "changes_made": ["Fixed line 1"],
    }
    valid, msg = agent._validate_review(review)
    assert valid, f"Expected valid, got: {msg}"


@pytest.mark.unit
def test_validate_review_missing_keys() -> None:
    """Review missing required keys fails validation."""
    from unittest.mock import MagicMock
    agent = ReviewerAgent(MagicMock(), MagicMock())
    review = {"root_cause": "Something went wrong"}
    valid, msg = agent._validate_review(review)
    assert not valid
    assert "missing" in msg.lower() or "fixed_code" in msg.lower() or "confidence" in msg.lower()


@pytest.mark.unit
def test_validate_review_invalid_confidence() -> None:
    """Review with confidence outside [0, 1] fails."""
    from unittest.mock import MagicMock
    agent = ReviewerAgent(MagicMock(), MagicMock())
    review = {
        "root_cause": "Bug",
        "fixed_code": "print(1)",
        "confidence": 1.5,
    }
    valid, msg = agent._validate_review(review)
    assert not valid
    assert "confidence" in msg.lower()


@pytest.mark.unit
def test_validate_review_broken_fixed_code() -> None:
    """Review with syntactically invalid fixed code fails."""
    from unittest.mock import MagicMock
    agent = ReviewerAgent(MagicMock(), MagicMock())
    review = {
        "root_cause": "Bug",
        "fixed_code": "def broken(\n    return 1",
        "confidence": 0.7,
    }
    valid, msg = agent._validate_review(review)
    assert not valid
    assert "syntax" in msg.lower()
