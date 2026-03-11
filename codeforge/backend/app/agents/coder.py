"""Coder agent — generates Python code for each subtask."""

from __future__ import annotations

import ast
import logging
import re
import subprocess
import tempfile

from app.agents.base import AgentInput, AgentOutput, AgentType, BaseAgent
from app.agents.prompts.coder import CODER_SYSTEM_PROMPT, build_coder_user_prompt

logger = logging.getLogger("codeforge.agent.coder")

_ALLOWED_PACKAGES = {
    "numpy", "pandas", "matplotlib", "scipy", "sklearn", "requests",
    "bs4", "beautifulsoup4", "sympy", "PIL", "Pillow", "networkx",
}

_STDLIB_MODULES = {
    "abc", "argparse", "array", "ast", "asyncio", "base64", "bisect",
    "calendar", "cmath", "collections", "concurrent", "contextlib", "copy",
    "csv", "dataclasses", "datetime", "decimal", "difflib", "enum",
    "errno", "functools", "glob", "hashlib", "heapq", "hmac", "html",
    "http", "importlib", "inspect", "io", "itertools", "json", "logging",
    "math", "multiprocessing", "operator", "os", "pathlib", "pickle",
    "platform", "pprint", "queue", "random", "re", "shutil", "signal",
    "socket", "sqlite3", "statistics", "string", "struct", "subprocess",
    "sys", "tempfile", "textwrap", "threading", "time", "timeit",
    "traceback", "typing", "typing_extensions", "unittest", "urllib",
    "uuid", "warnings", "xml", "zipfile",
}


class CoderAgent(BaseAgent):
    @property
    def agent_type(self) -> AgentType:
        return AgentType.CODER

    def _build_system_prompt(self) -> str:
        return CODER_SYSTEM_PROMPT

    def _build_user_prompt(self, input_data: AgentInput) -> str:
        return build_coder_user_prompt(
            input_data.data["subtask"],
            input_data.data["plan"],
            input_data.data.get("prior_code", {}),
        )

    async def _execute(self, input_data: AgentInput) -> AgentOutput:
        user_prompt = self._build_user_prompt(input_data)
        response = await self._call_llm(user_prompt, structured=True)

        content = getattr(response, "content", "")
        result = self._parse_json_response(content)

        code = result.get("code", "")
        imports = result.get("imports", [])
        explanation = result.get("explanation", "")

        if not code:
            raise ValueError("Coder returned empty code")

        valid, error_msg = self._validate_code(code)
        if not valid:
            retry_prompt = (
                f"{user_prompt}\n\nYour previous code had a syntax error: {error_msg}\n"
                "Please fix the syntax and return valid JSON only."
            )
            response = await self._call_llm(retry_prompt, structured=True)
            content = getattr(response, "content", "")
            result = self._parse_json_response(content)
            code = result.get("code", "")
            valid, error_msg = self._validate_code(code)
            if not valid:
                raise ValueError(f"Generated code has syntax error: {error_msg}")

        # Auto-format
        code = self._format_code(code)

        # Validate imports
        import_warnings = self._validate_imports(code)
        if import_warnings:
            logger.warning("Import warnings for task: %s", import_warnings)

        tokens = getattr(response, "total_tokens", 0)
        rec = self.cost_tracker.record(response) if hasattr(self.cost_tracker, "record") else None
        cost = rec.cost_usd if rec else 0.0

        return AgentOutput(
            data={"code": code, "imports": imports, "explanation": explanation},
            reasoning=explanation,
            tokens_used=tokens,
            cost_usd=cost,
            duration_ms=0,
            success=True,
        )

    def _validate_code(self, code: str) -> tuple[bool, str]:
        """Check if code is syntactically valid Python."""
        try:
            compile(code, "<generated>", "exec")
            return (True, "")
        except SyntaxError as e:
            return (False, f"Syntax error at line {e.lineno}: {e.msg}")

    def _format_code(self, code: str) -> str:
        """Auto-format code with ruff if available."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                f.flush()
                subprocess.run(
                    ["python3", "-m", "ruff", "format", f.name],
                    capture_output=True, timeout=5,
                )
                subprocess.run(
                    ["python3", "-m", "ruff", "check", "--fix", "--select", "I,F401", f.name],
                    capture_output=True, timeout=5,
                )
                with open(f.name, 'r') as rf:
                    formatted = rf.read()
            import os
            os.unlink(f.name)
            return formatted
        except Exception:
            return code  # Return unformatted if ruff unavailable

    def _validate_imports(self, code: str) -> list[str]:
        """Extract and validate imports against allowed packages."""
        warnings = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split('.')[0]
                        if top not in _STDLIB_MODULES and top not in _ALLOWED_PACKAGES:
                            warnings.append(f"Non-standard import: {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        top = node.module.split('.')[0]
                        if top not in _STDLIB_MODULES and top not in _ALLOWED_PACKAGES:
                            warnings.append(f"Non-standard import: {node.module}")
        except SyntaxError:
            pass
        return warnings

    @staticmethod
    def _merge_code(code_segments: dict[int, str], integration_code: str) -> str:
        """Merge all code segments into a single file using AST-based extraction."""
        all_imports: list[str] = []
        all_bodies: list[str] = []
        main_block: str = ""

        for _sid, code in sorted(code_segments.items()):
            try:
                tree = ast.parse(code)
            except SyntaxError:
                # If AST fails, include raw code as-is
                all_bodies.append(code)
                continue

            import_lines: list[str] = []
            body_lines: list[str] = []
            source_lines = code.splitlines()

            for node in tree.body:
                # Extract the source lines for this AST node
                start = node.lineno - 1
                end = getattr(node, "end_lineno", node.lineno)
                node_source = "\n".join(source_lines[start:end])

                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if node_source not in all_imports:
                        import_lines.append(node_source)
                elif isinstance(node, ast.If):
                    # Detect if __name__ == "__main__" block
                    test = node.test
                    is_main = False
                    if isinstance(test, ast.Compare):
                        left = test.left
                        if isinstance(left, ast.Name) and left.id == "__name__":
                            is_main = True
                        elif isinstance(left, ast.Attribute) and getattr(left, "attr", "") == "__name__":
                            is_main = True
                    if is_main:
                        main_block = node_source
                    else:
                        body_lines.append(node_source)
                else:
                    body_lines.append(node_source)

            all_imports.extend(import_lines)
            body = "\n\n".join(body_lines)
            if body.strip():
                all_bodies.append(body)

        # Deduplicate imports preserving order
        seen: set[str] = set()
        deduped: list[str] = []
        for imp in all_imports:
            if imp not in seen:
                seen.add(imp)
                deduped.append(imp)

        parts = deduped
        if parts:
            parts.append("")
        parts.append("")
        parts.extend(all_bodies)
        if main_block:
            parts.append("")
            parts.append("")
            parts.append(main_block)

        return "\n".join(parts)
