"""Reviewer agent prompts."""

from __future__ import annotations

import re

REVIEWER_SYSTEM_PROMPT = '''You are an expert code debugging agent. Analyze failed code execution and produce a precise, minimal fix.

## Error Taxonomy and Fix Strategies

| Error Type        | Common Causes                                | Fix Strategy                                |
|-------------------|----------------------------------------------|---------------------------------------------|
| syntax_error      | Missing colon, unmatched parens, bad indent  | Patch: fix the specific syntax issue        |
| import_error      | ModuleNotFoundError for non-stdlib package   | Replace with stdlib equivalent (see below)  |
| runtime_error     | TypeError, ValueError, KeyError, IndexError  | Patch: add type check, default, or guard    |
| logic_error       | Wrong output, off-by-one, incorrect formula  | Patch if localized; rewrite function if not |
| timeout           | Infinite loop, O(n!) algorithm               | Rewrite: simplify algorithm or add limit    |
| memory_error      | Unbounded data structure, massive allocation | Rewrite: use generator/streaming approach   |
| network_error     | ConnectionError, DNS failure, socket timeout | Rewrite: replace real HTTP with mock data   |

## Stdlib Replacement Guide (for import_error and network_error)

- `requests` / `aiohttp` -> `urllib.request` (sync) or mock data (preferred in sandbox)
- `flask` / `django` -> `http.server` from stdlib
- `numpy` -> `math`, `statistics`, list comprehensions
- `pandas` -> `csv` module + dicts/lists
- `PIL` / `Pillow` -> describe output as text (no image processing in sandbox)
- Any unavailable module -> simulate its behavior with stdlib equivalents

## When to Patch vs. Rewrite

- **Patch** (confidence >= 0.7): The root cause is a single localized mistake (wrong variable name, missing None check, incorrect index, missing import). Change only the affected lines.
- **Rewrite** (confidence < 0.7 OR error persists after 2+ attempts): The approach itself is flawed. Rewrite the failing function or section with a fundamentally different strategy, but keep working parts intact.

## Critical Async Patterns

- `asyncio.run()` takes a coroutine, NOT a Future. Always: `async def main(): await asyncio.gather(...)` then `asyncio.run(main())`.
- `urllib.request` is synchronous. In async code: `await loop.run_in_executor(None, urllib.request.urlopen, url)`.
- Never `await` a non-coroutine. Check the return type.

## Output Format

Output ONLY valid JSON (no markdown fences, no text outside the JSON):

{
  "root_cause": "Clear 1-2 sentence description of WHY the code failed",
  "error_type": "syntax_error | runtime_error | logic_error | import_error | timeout | memory_error | network_error",
  "fix_description": "What the fix changes and why it resolves the root cause",
  "fixed_code": "<complete corrected Python code -- must be syntactically valid>",
  "confidence": <float 0.0-1.0>,
  "changes_made": ["Line N: description of change", ...]
}

## Few-Shot Example

Input error:
```
Traceback (most recent call last):
  File "/tmp/task.py", line 45, in <module>
    asyncio.run(asyncio.gather(*tasks))
  File "/usr/lib/python3.11/asyncio/runners.py", line 186, in run
    raise ValueError("a coroutine was expected, got %r" % coro,)
ValueError: a coroutine was expected, got <coroutine object gather at 0x7f...>
```

Output:
{
  "root_cause": "asyncio.run() requires a coroutine object, but asyncio.gather() returns a Future. The gather call must be wrapped inside an async function.",
  "error_type": "runtime_error",
  "fix_description": "Wrapped the asyncio.gather() call inside an `async def main()` coroutine and pass that to asyncio.run() instead of passing gather directly.",
  "fixed_code": "import asyncio\\n\\nasync def fetch(url: str) -> str:\\n    \"\"\"Simulate fetching a URL.\"\"\"\\n    await asyncio.sleep(0.01)\\n    return f\\\"Response from {url}\\\"\\n\\nasync def main() -> None:\\n    \"\"\"Run all fetch tasks concurrently.\"\"\"\\n    urls = [\\\"http://example.com/1\\\", \\\"http://example.com/2\\\"]\\n    tasks = [fetch(url) for url in urls]\\n    results = await asyncio.gather(*tasks)\\n    for url, result in zip(urls, results):\\n        print(f\\\"{url}: {result}\\\")\\n\\nif __name__ == \\\"__main__\\\":\\n    asyncio.run(main())\\n",
  "confidence": 0.95,
  "changes_made": [
    "Line 45: replaced `asyncio.run(asyncio.gather(*tasks))` with `asyncio.run(main())`",
    "Added `async def main()` wrapper that calls `await asyncio.gather(*tasks)` internally"
  ]
}'''


def _parse_error_info(stderr: str) -> dict:
    """Extract structured error info from Python traceback.

    Handles multiline tracebacks, chained exceptions, and non-standard
    error formats. Extracts the final (most relevant) exception.
    """
    info: dict = {
        "error_class": "",
        "error_message": "",
        "error_line": None,
        "traceback_depth": 0,
        "full_exception": "",
    }

    if not stderr or not stderr.strip():
        return info

    lines = stderr.strip().splitlines()

    # Count traceback depth (number of stack frames)
    file_lines = [ln for ln in lines if ln.strip().startswith("File ")]
    info["traceback_depth"] = len(file_lines)

    # Find error line number from the last File reference (closest to the crash)
    if file_lines:
        m = re.search(r'line (\d+)', file_lines[-1])
        if m:
            info["error_line"] = int(m.group(1))

    # Extract the final exception line(s).
    # Python tracebacks end with "ExceptionClass: message" or just "ExceptionClass".
    # Chained exceptions use "During handling..." or "The above exception..." as
    # separators -- we want the LAST exception block.
    #
    # Strategy: walk backward from the end, skip blank lines, collect the
    # exception line. Some error messages span multiple lines (e.g., SyntaxError
    # shows a caret line), so we look for the pattern "ClassName: ..." or
    # "ClassName" as the primary line.
    exception_line = ""
    for line in reversed(lines):
        stripped = line.strip()
        if not stripped:
            continue
        # Skip lines that are part of the traceback frame (File "...", line N)
        # or the "Traceback (most recent call last):" header.
        if stripped.startswith("File ") or stripped.startswith("Traceback "):
            continue
        # Skip caret/context lines from SyntaxError display (e.g., "    ^^^^^")
        if re.match(r'^[\s\^~]+$', stripped):
            continue
        # Skip lines that are just the offending source code (indented, no colon
        # pattern matching an exception class).
        # An exception line typically starts with an uppercase letter or a
        # module-qualified name like "module.ClassName".
        if re.match(r'^[A-Za-z_][\w.]*(?:Error|Exception|Warning|Exit|Interrupt|Fault)',
                     stripped):
            exception_line = stripped
            break
        if ":" in stripped:
            before_colon = stripped.split(":", 1)[0].strip()
            # Check if the part before colon looks like an exception class name
            if before_colon.replace(".", "").isidentifier() and before_colon[0].isupper():
                exception_line = stripped
                break
        # If we hit a line that looks like source code context, keep scanning
        # (SyntaxError prints the offending line before the error)

    if exception_line:
        info["full_exception"] = exception_line
        if ":" in exception_line:
            parts = exception_line.split(":", 1)
            info["error_class"] = parts[0].strip()
            info["error_message"] = parts[1].strip()
        else:
            info["error_class"] = exception_line.strip()
            info["error_message"] = ""

    return info


def build_reviewer_user_prompt(
    code: str,
    error: dict,
    attempt: int,
    max_attempts: int,
    original_task: str,
    previous_fixes: list | None = None,
) -> str:
    # Parse structured error info from stderr
    stderr_text = error.get('stderr', '')
    error_info = _parse_error_info(stderr_text) if stderr_text else {
        "error_class": "", "error_message": "", "error_line": None,
        "traceback_depth": 0, "full_exception": "",
    }

    prompt = f"""Fix this failed code execution.

ORIGINAL TASK: {original_task}

ATTEMPT: {attempt} of {max_attempts}

CODE THAT FAILED:
```python
{code}
```

EXIT CODE: {error.get('exit_code', 'unknown')}

STDOUT:
{error.get('stdout', '(empty)')}

STDERR:
{error.get('stderr', '(empty)')}

STRUCTURED ERROR ANALYSIS:
- Error Class: {error_info['error_class'] or 'unknown'}
- Error Message: {error_info['error_message'] or 'unknown'}
- Error Line: {error_info['error_line'] or 'unknown'}
- Traceback Depth: {error_info['traceback_depth']}
- Full Exception: {error_info.get('full_exception', '') or 'unknown'}

ENVIRONMENT CONSTRAINTS (your fix MUST obey these):
- ONLY the Python standard library is available. Replace any external packages (aiohttp, requests, flask, numpy, pandas, etc.) with stdlib equivalents.
- If the error is ModuleNotFoundError, replace the missing module with a stdlib alternative or simulate its behavior.
- NO network access. If the error is a connection/DNS/socket failure, replace real HTTP calls with mock/simulated responses returning realistic fake data.
- urllib.request is SYNCHRONOUS. In async code, wrap with `await loop.run_in_executor(None, func)`. Do NOT try to await urllib calls directly.
- asyncio.run() requires a coroutine, NOT a Future. Always wrap gather: `async def main(): results = await asyncio.gather(*tasks)` then `asyncio.run(main())`."""

    if previous_fixes:
        prompt += "\n\nPREVIOUS FIX ATTEMPTS THAT FAILED (do NOT repeat these approaches):\n"
        for fix in previous_fixes:
            prompt += (
                f"- Attempt {fix.get('attempt', '?')}: "
                f"{fix.get('fix_description', 'unknown')} "
                f"[confidence: {fix.get('confidence', '?')}]\n"
            )
        prompt += (
            "\nSince previous fixes failed, you MUST try a DIFFERENT strategy. Consider:\n"
            "- If you patched before, rewrite the failing function with a different algorithm\n"
            "- If an external module was replaced but still fails, use pure mock data instead\n"
            "- If async patterns keep failing, rewrite as synchronous code\n"
            "- If the logic is wrong, re-read the original task and reconsider the approach\n"
            "- Simplify: remove unnecessary complexity that may be causing cascading failures"
        )

    if attempt >= max_attempts:
        prompt += (
            "\n\nThis is the FINAL attempt. Prioritize a SIMPLE, WORKING solution over "
            "an elegant one. Strip the code to its minimum viable form if needed."
        )

    prompt += "\n\nAnalyze the error and provide a fix in the required JSON format."
    return prompt
