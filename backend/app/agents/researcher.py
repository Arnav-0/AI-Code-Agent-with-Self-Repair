"""Researcher agent — performs deep research before code generation."""

from __future__ import annotations

import logging
from typing import Any

from app.agents.base import AgentInput, AgentOutput, AgentType, BaseAgent
from app.agents.prompts.researcher import RESEARCHER_REFINE, RESEARCHER_SYSTEM, RESEARCHER_USER

logger = logging.getLogger("codeforge.agent.researcher")


class ResearcherAgent(BaseAgent):
    """Researches the task domain, identifies patterns, libraries, and risks."""

    def __init__(
        self,
        llm: Any,
        cost_tracker: Any,
        callback: Any = None,
        web_search: Any = None,
    ) -> None:
        super().__init__(llm, cost_tracker, callback)
        self.web_search = web_search

    @property
    def agent_type(self) -> AgentType:
        return AgentType.RESEARCHER

    def _build_system_prompt(self) -> str:
        return RESEARCHER_SYSTEM

    def _build_user_prompt(self, input_data: AgentInput) -> str:
        return RESEARCHER_USER.format(
            prompt=input_data.data.get("prompt", ""),
            search_context=input_data.data.get("search_context", "No web search results available. Use your knowledge."),
        )

    async def _execute(self, input_data: AgentInput) -> AgentOutput:
        prompt = input_data.data.get("prompt", "")

        # Phase 1: Initial analysis to generate search queries
        try:
            response = await self._call_llm(
                self._build_user_prompt(input_data),
                self._build_system_prompt(),
            )
            initial_findings = self._parse_json_response(getattr(response, "content", "{}"))
        except Exception as exc:
            logger.error("Research LLM call failed: %s", exc)
            return AgentOutput(
                data={"search_results_used": False, "key_findings": [], "recommended_approach": "LLM research failed — proceeding with task as-is."},
                reasoning=f"Research failed: {exc}",
                tokens_used=0,
                cost_usd=0.0,
                duration_ms=0,
                success=False,
            )

        # Phase 2: If web search is available, search and refine
        search_queries = initial_findings.get("search_queries", [])
        search_results_text = ""

        if self.web_search and search_queries:
            try:
                findings_list = await self.web_search.multi_search(
                    search_queries[:5], max_results_per=3
                )
                # Format search results for the LLM
                parts = []
                for f in findings_list:
                    parts.append(f"## Query: {f.query}")
                    if f.synthesis:
                        parts.append(f"Summary: {f.synthesis}")
                    for r in f.results:
                        parts.append(f"- [{r.title}]({r.url}): {r.snippet}")
                    parts.append("")
                search_results_text = "\n".join(parts)
            except Exception as exc:
                logger.warning("Web search failed during research: %s", exc)

        # Phase 3: Refine with search results if we got any
        if search_results_text:
            import json

            refine_prompt = RESEARCHER_REFINE.format(
                prompt=prompt,
                initial_findings=json.dumps(initial_findings, indent=2),
                search_results=search_results_text,
            )
            refine_response = await self._call_llm(refine_prompt, self._build_system_prompt())
            refined = self._parse_json_response(getattr(refine_response, "content", "{}"))

            tokens = getattr(response, "tokens_used", 0) + getattr(refine_response, "tokens_used", 0)
            cost = getattr(response, "cost_usd", 0.0) + getattr(refine_response, "cost_usd", 0.0)

            return AgentOutput(
                data={**refined, "search_results_used": True, "search_count": len(search_queries)},
                reasoning=refined.get("recommended_approach", ""),
                tokens_used=tokens,
                cost_usd=cost,
                duration_ms=0,
                success=True,
            )

        tokens = getattr(response, "tokens_used", 0)
        cost = getattr(response, "cost_usd", 0.0)

        return AgentOutput(
            data={**initial_findings, "search_results_used": bool(search_results_text)},
            reasoning=initial_findings.get("recommended_approach", ""),
            tokens_used=tokens,
            cost_usd=cost,
            duration_ms=0,
            success=True,
        )
