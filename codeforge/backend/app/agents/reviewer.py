"""Reviewer agent — analyzes execution failures and suggests fixes."""

from __future__ import annotations

import logging

from app.agents.base import AgentInput, AgentOutput, AgentType, BaseAgent
from app.agents.prompts.reviewer import REVIEWER_SYSTEM_PROMPT, build_reviewer_user_prompt

logger = logging.getLogger("codeforge.agent.reviewer")


class ReviewerAgent(BaseAgent):
    @property
    def agent_type(self) -> AgentType:
        return AgentType.REVIEWER

    def _build_system_prompt(self) -> str:
        return REVIEWER_SYSTEM_PROMPT

    def _build_user_prompt(self, input_data: AgentInput) -> str:
        return build_reviewer_user_prompt(
            code=input_data.data.get("code", ""),
            error=input_data.data.get("error", {}),
            attempt=input_data.data.get("attempt", 1),
            max_attempts=input_data.data.get("max_attempts", 3),
            original_task=input_data.data.get("original_task", ""),
            previous_fixes=input_data.data.get("previous_fixes"),
        )

    async def _execute(self, input_data: AgentInput) -> AgentOutput:
        user_prompt = self._build_user_prompt(input_data)
        response = await self._call_llm(user_prompt, structured=True)

        content = getattr(response, "content", "")
        review = self._parse_json_response(content)

        valid, error_msg = self._validate_review(review)
        if not valid:
            raise ValueError(f"Invalid review output: {error_msg}")

        tokens = getattr(response, "total_tokens", 0)
        rec = self.cost_tracker.record(response) if hasattr(self.cost_tracker, "record") else None
        cost = rec.cost_usd if rec else 0.0

        return AgentOutput(
            data=review,
            reasoning=review.get("root_cause", ""),
            tokens_used=tokens,
            cost_usd=cost,
            duration_ms=0,
            success=True,
        )

    def _validate_review(self, review: dict) -> tuple[bool, str]:
        """Validate the review output structure."""
        required = ["root_cause", "fixed_code", "confidence"]
        for key in required:
            if key not in review:
                return (False, f"Missing key: {key}")

        if not isinstance(review["confidence"], (int, float)):
            return (False, "confidence must be a number")

        if not 0 <= review["confidence"] <= 1:
            return (False, "confidence must be between 0 and 1")

        try:
            compile(review["fixed_code"], "<fix>", "exec")
        except SyntaxError as e:
            return (False, f"Fixed code has syntax error: {e}")

        return (True, "")
