"""Task complexity classifier — advanced heuristic with pattern analysis."""

from __future__ import annotations

import json
import logging
import re
from enum import Enum

logger = logging.getLogger("codeforge.classifier")


class ComplexityLevel(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    HARD = "hard"


# ---------------------------------------------------------------------------
# Keyword dictionaries with weighted scores
# ---------------------------------------------------------------------------

_SIMPLE_INDICATORS: dict[str, float] = {
    "hello world": 0.4,
    "print": 0.15,
    "fizzbuzz": 0.5,
    "fizz buzz": 0.5,
    "reverse string": 0.4,
    "palindrome": 0.3,
    "factorial": 0.3,
    "fibonacci": 0.25,
    "swap": 0.3,
    "sum of": 0.2,
    "count the": 0.2,
    "basic": 0.15,
    "simple": 0.2,
    "single function": 0.3,
    "convert": 0.1,
    "sort a list": 0.2,
    "binary search": 0.15,
    "calculator": 0.15,
}

_HARD_INDICATORS: dict[str, float] = {
    # Architecture & systems
    "multiple files": 0.3,
    "multi-file": 0.3,
    "database": 0.25,
    "rest api": 0.3,
    "graphql": 0.35,
    "microservice": 0.4,
    "websocket": 0.3,
    "authentication": 0.25,
    "authorization": 0.25,
    # Concurrency
    "concurrent": 0.3,
    "distributed": 0.35,
    "async": 0.15,
    "threading": 0.2,
    "multiprocessing": 0.25,
    "parallel": 0.2,
    # Data structures & algorithms
    "red-black tree": 0.4,
    "b-tree": 0.4,
    "avl tree": 0.35,
    "graph algorithm": 0.3,
    "dynamic programming": 0.3,
    "backtracking": 0.25,
    "optimize": 0.15,
    # ML & AI
    "machine learning": 0.35,
    "neural network": 0.4,
    "deep learning": 0.4,
    "training loop": 0.3,
    # Parsing & compilation
    "parser": 0.3,
    "compiler": 0.4,
    "interpreter": 0.35,
    "lexer": 0.35,
    "ast": 0.2,
    # Infrastructure
    "redis": 0.2,
    "kafka": 0.3,
    "docker": 0.2,
    "kubernetes": 0.35,
    "encryption": 0.25,
    "compression": 0.2,
}


class HeuristicClassifier:
    """Advanced keyword/pattern-based complexity classifier."""

    def classify(self, prompt: str) -> tuple[ComplexityLevel, float]:
        lower = prompt.lower()
        words = lower.split()
        word_count = len(words)

        simple_score = 0.0
        hard_score = 0.0

        # --- Weighted keyword matching ---
        for kw, weight in _SIMPLE_INDICATORS.items():
            if kw in lower:
                simple_score += weight

        for kw, weight in _HARD_INDICATORS.items():
            if kw in lower:
                hard_score += weight

        # --- Structural complexity signals ---

        # Prompt length
        if word_count < 20:
            simple_score += 0.25
        elif word_count < 50:
            simple_score += 0.1
        elif word_count > 150:
            hard_score += 0.2
        elif word_count > 300:
            hard_score += 0.3

        # Sentence count (many requirements = complex)
        sentences = len(re.findall(r'[.!?]+', prompt))
        if sentences > 6:
            hard_score += 0.2
        elif sentences > 10:
            hard_score += 0.3

        # Numbered steps / bullet points
        numbered_steps = len(re.findall(r'\b\d+[.)]\s', prompt))
        bullet_points = len(re.findall(r'^[\s]*[-*]\s', prompt, re.MULTILINE))
        step_count = numbered_steps + bullet_points
        if step_count >= 5:
            hard_score += 0.3
        elif step_count >= 3:
            hard_score += 0.15

        # Requirement conjunctions
        req_markers = ["and also", "additionally", "furthermore", "as well as", "along with", "plus"]
        req_count = sum(1 for m in req_markers if m in lower)
        simple_and_count = lower.count(" and ")
        if req_count >= 2 or simple_and_count >= 4:
            hard_score += 0.15

        # Code patterns in the prompt itself
        if "class " in lower and "def " in lower:
            hard_score += 0.15
        elif "class " in lower:
            hard_score += 0.1

        # Testing requirements
        if any(t in lower for t in ["test suite", "unit test", "test cases", "comprehensive test", "edge case"]):
            hard_score += 0.1

        # "with" requirements chain: "with X, Y, and Z"
        with_count = lower.count(" with ")
        if with_count >= 3:
            hard_score += 0.15

        # --- Normalize scores ---
        simple_score = min(simple_score, 1.0)
        hard_score = min(hard_score, 1.0)

        # --- Thresholds ---
        try:
            from app.config import get_settings
            settings = get_settings()
            simple_threshold = settings.complexity_simple_threshold
            complex_threshold = settings.complexity_complex_threshold
        except Exception:
            simple_threshold = 0.3
            complex_threshold = 0.6

        # Decision logic
        if hard_score >= complex_threshold:
            return (ComplexityLevel.HARD, hard_score)
        if simple_score >= simple_threshold and hard_score < 0.15:
            return (ComplexityLevel.SIMPLE, simple_score)
        return (ComplexityLevel.MEDIUM, max(simple_score, hard_score, 0.5))


class LLMClassifier:
    """Uses a cheap LLM for better classification."""

    _SYSTEM = (
        "You are a task complexity classifier for a code generation system.\n"
        "Classify the coding task as SIMPLE, MEDIUM, or HARD.\n\n"
        "SIMPLE: Single function, basic operations, well-known patterns (fizzbuzz, palindrome, sorting).\n"
        "MEDIUM: Multiple functions, error handling, standard libraries, moderate logic.\n"
        "HARD: Multi-step algorithms, multiple modules, complex data structures, "
        "system design, concurrency, parsing, ML.\n\n"
        'Respond with JSON: {"level": "SIMPLE|MEDIUM|HARD", "confidence": 0.0-1.0, "reasoning": "brief"}'
    )

    def __init__(self, llm_provider: object) -> None:
        self._llm = llm_provider
        self._fallback = HeuristicClassifier()

    def classify(self, prompt: str) -> tuple[ComplexityLevel, float]:
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, self._async_classify(prompt))
                    return future.result(timeout=30)
            else:
                return loop.run_until_complete(self._async_classify(prompt))
        except Exception as exc:
            logger.warning("LLMClassifier failed, using heuristic: %s", exc)
            return self._fallback.classify(prompt)

    async def _async_classify(self, prompt: str) -> tuple[ComplexityLevel, float]:
        response = await self._llm.generate_structured(prompt, self._SYSTEM)
        data = json.loads(response.content)
        level_str = data.get("level", "MEDIUM").upper()
        confidence = float(data.get("confidence", 0.5))
        level_map = {
            "SIMPLE": ComplexityLevel.SIMPLE,
            "MEDIUM": ComplexityLevel.MEDIUM,
            "HARD": ComplexityLevel.HARD,
        }
        level = level_map.get(level_str, ComplexityLevel.MEDIUM)
        return (level, confidence)


class TaskClassifier:
    """Main interface for task complexity classification."""

    def __init__(self, llm_provider: object = None, use_llm: bool = False) -> None:
        self._use_llm = use_llm and llm_provider is not None
        self._heuristic = HeuristicClassifier()
        self._llm_classifier = LLMClassifier(llm_provider) if self._use_llm else None

    def classify(self, prompt: str) -> tuple[ComplexityLevel, float]:
        if self._use_llm and self._llm_classifier is not None:
            level, conf = self._llm_classifier.classify(prompt)
        else:
            level, conf = self._heuristic.classify(prompt)
        logger.info("Task classified as %s (confidence=%.2f)", level.name, conf)
        return (level, conf)
