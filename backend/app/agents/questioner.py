"""Questioner agent — generates targeted questions based on research findings."""

from __future__ import annotations

import logging

from app.agents.base import AgentInput, AgentOutput, AgentType, BaseAgent
from app.agents.prompts.questioner import QUESTIONER_SYSTEM, QUESTIONER_USER

logger = logging.getLogger("codeforge.agent.questioner")


class QuestionerAgent(BaseAgent):
    """Analyzes research findings and generates targeted clarification questions."""

    @property
    def agent_type(self) -> AgentType:
        return AgentType.QUESTIONER

    def _build_system_prompt(self) -> str:
        return QUESTIONER_SYSTEM

    def _build_user_prompt(self, input_data: AgentInput) -> str:
        research = input_data.data.get("research", {})

        # Build a readable research summary
        findings = research.get("key_findings", [])
        findings_text = "\n".join(
            f"- [{f.get('confidence', '?')}] {f.get('topic', '')}: {f.get('insight', '')}"
            for f in findings
        )

        gaps = research.get("needs_clarification", [])
        gaps_text = "\n".join(f"- {g}" for g in gaps) if gaps else "None identified"

        libs = research.get("libraries", [])
        libs_text = ", ".join(lib.get("name", "") for lib in libs) if libs else "None specified"

        summary = (
            f"Recommended approach: {research.get('recommended_approach', 'N/A')}\n"
            f"Estimated complexity: {research.get('estimated_complexity', 'unknown')}\n"
            f"Libraries: {libs_text}\n"
            f"Architecture: {research.get('architecture_notes', 'N/A')}\n"
            f"Risks: {', '.join(research.get('risks', []))}\n"
            f"\nKey findings:\n{findings_text}"
        )

        return QUESTIONER_USER.format(
            prompt=input_data.data.get("prompt", ""),
            research_summary=summary,
            gaps=gaps_text,
        )

    async def _execute(self, input_data: AgentInput) -> AgentOutput:
        response = await self._call_llm(
            self._build_user_prompt(input_data),
            self._build_system_prompt(),
        )

        parsed = self._parse_json_response(getattr(response, "content", "{}"))

        tokens = getattr(response, "tokens_used", 0)
        cost = getattr(response, "cost_usd", 0.0)

        return AgentOutput(
            data=parsed,
            reasoning=f"Generated {len(parsed.get('questions', []))} questions",
            tokens_used=tokens,
            cost_usd=cost,
            duration_ms=0,
            success=True,
        )
