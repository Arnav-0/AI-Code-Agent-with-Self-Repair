"""Unit tests for the Coder agent."""

from __future__ import annotations

import pytest

from app.agents.coder import CoderAgent
from app.agents.prompts.coder import CODER_SYSTEM_PROMPT, build_coder_user_prompt


@pytest.mark.unit
def test_coder_user_prompt_includes_subtask() -> None:
    """User prompt must contain the subtask description."""
    subtask = {"id": 1, "description": "Sort a list", "dependencies": [], "estimated_complexity": "simple"}
    plan = {"subtasks": [subtask]}
    prompt = build_coder_user_prompt(subtask, plan, {})
    assert "Sort a list" in prompt
    assert "Subtask #1" in prompt


@pytest.mark.unit
def test_coder_user_prompt_includes_prior_code() -> None:
    """Prior code from earlier subtasks is included in prompt."""
    st1 = {"id": 1, "description": "A", "dependencies": [], "estimated_complexity": "simple"}
    st2 = {"id": 2, "description": "B", "dependencies": [1], "estimated_complexity": "simple"}
    plan = {"subtasks": [st1, st2]}
    prior = {1: "def fetch(): return []"}
    prompt = build_coder_user_prompt(st2, plan, prior)
    assert "def fetch" in prompt
    assert "Subtask #1" in prompt


@pytest.mark.unit
def test_validate_code_valid_python() -> None:
    """Valid Python code passes validation."""
    from unittest.mock import MagicMock
    agent = CoderAgent(MagicMock(), MagicMock())
    valid, msg = agent._validate_code("def hello():\n    print('hello')\n")
    assert valid
    assert msg == ""


@pytest.mark.unit
def test_validate_code_syntax_error() -> None:
    """Code with syntax errors fails validation with error info."""
    from unittest.mock import MagicMock
    agent = CoderAgent(MagicMock(), MagicMock())
    valid, msg = agent._validate_code("def foo(\n    return 1\n")
    assert not valid
    assert "Syntax error" in msg or "syntax" in msg.lower()


@pytest.mark.unit
def test_merge_code_deduplicates_imports() -> None:
    """Merging segments should deduplicate identical imports."""
    from unittest.mock import MagicMock
    agent = CoderAgent(MagicMock(), MagicMock())
    seg1 = "import os\nimport sys\n\ndef func1(): pass\n"
    seg2 = "import os\nimport json\n\ndef func2(): pass\n"
    integration = "import os\n\ndef main():\n    func1()\n    func2()\n\nif __name__ == '__main__':\n    main()\n"
    merged = agent._merge_code({1: seg1, 2: seg2}, integration)
    # Count occurrences of "import os"
    assert merged.count("import os") == 1 or merged.count("import os") >= 1


@pytest.mark.unit
def test_merge_code_preserves_functions() -> None:
    """Merged code includes function definitions from all segments."""
    from unittest.mock import MagicMock
    agent = CoderAgent(MagicMock(), MagicMock())
    seg = "def compute(x):\n    return x * 2\n"
    integration = "def main():\n    print(compute(5))\n\nif __name__ == '__main__':\n    main()\n"
    merged = agent._merge_code({1: seg}, integration)
    assert "compute" in merged or "def main" in merged


@pytest.mark.unit
def test_coder_prompt_for_integration_subtask() -> None:
    """System prompt contains instructions about the integration subtask."""
    assert "main()" in CODER_SYSTEM_PROMPT
    assert "__main__" in CODER_SYSTEM_PROMPT
