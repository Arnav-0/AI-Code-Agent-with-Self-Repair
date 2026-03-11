"""Web search service for research-driven agent pipeline.

Supports Tavily API, SerpAPI, or falls back to LLM-based knowledge synthesis.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger("codeforge.web_search")


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    score: float = 0.0


@dataclass
class ResearchFindings:
    query: str
    results: list[SearchResult] = field(default_factory=list)
    synthesis: str = ""
    source: str = "none"


class WebSearchService:
    """Performs web searches using available API keys, with graceful fallback."""

    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        serp_api_key: Optional[str] = None,
    ) -> None:
        self.tavily_api_key = tavily_api_key
        self.serp_api_key = serp_api_key
        self._client = httpx.AsyncClient(timeout=15.0)

    async def search(self, query: str, max_results: int = 5) -> ResearchFindings:
        """Search using the best available provider."""
        if self.tavily_api_key:
            try:
                return await self._search_tavily(query, max_results)
            except Exception as exc:
                logger.warning("Tavily search failed: %s", exc)

        if self.serp_api_key:
            try:
                return await self._search_serp(query, max_results)
            except Exception as exc:
                logger.warning("SerpAPI search failed: %s", exc)

        # No search API available — return empty results
        # The researcher agent will use its own LLM knowledge
        return ResearchFindings(query=query, source="llm_knowledge")

    async def _search_tavily(self, query: str, max_results: int) -> ResearchFindings:
        resp = await self._client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": self.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "advanced",
                "include_answer": True,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("content", ""),
                score=r.get("score", 0.0),
            )
            for r in data.get("results", [])
        ]

        return ResearchFindings(
            query=query,
            results=results,
            synthesis=data.get("answer", ""),
            source="tavily",
        )

    async def _search_serp(self, query: str, max_results: int) -> ResearchFindings:
        resp = await self._client.get(
            "https://serpapi.com/search",
            params={
                "api_key": self.serp_api_key,
                "q": query,
                "num": max_results,
                "engine": "google",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("link", ""),
                snippet=r.get("snippet", ""),
                score=float(r.get("position", 0)),
            )
            for r in data.get("organic_results", [])[:max_results]
        ]

        answer_box = data.get("answer_box", {})
        synthesis = answer_box.get("answer", "") or answer_box.get("snippet", "")

        return ResearchFindings(
            query=query,
            results=results,
            synthesis=synthesis,
            source="serpapi",
        )

    async def multi_search(
        self, queries: list[str], max_results_per: int = 3
    ) -> list[ResearchFindings]:
        """Run multiple search queries in parallel."""
        import asyncio

        tasks = [self.search(q, max_results_per) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        findings = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning("Search query %d failed: %s", i, result)
                findings.append(ResearchFindings(query=queries[i], source="error"))
            else:
                findings.append(result)
        return findings

    async def close(self) -> None:
        await self._client.aclose()
