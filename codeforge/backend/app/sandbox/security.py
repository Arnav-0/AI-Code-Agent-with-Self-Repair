from __future__ import annotations

import re
from typing import Optional

DANGEROUS_IMPORTS: set[str] = {
    "os.system",
    "subprocess",
    "shutil.rmtree",
    "__import__",
    "eval",
    "exec",
    "compile",
}

DANGEROUS_PATTERNS: list[str] = [
    r"import\s+ctypes",
    r"from\s+ctypes",
    r"open\s*\(.*/etc/",
    r"open\s*\(.*/proc/",
    r"socket\.socket",
]

_compiled_patterns = [re.compile(p) for p in DANGEROUS_PATTERNS]


def validate_code(code: str) -> tuple[bool, Optional[str]]:
    """Soft security check. The Docker sandbox provides real isolation.

    Returns (True, None) if safe, or (False, reason) if potentially dangerous.
    """
    for pattern, compiled in zip(DANGEROUS_PATTERNS, _compiled_patterns):
        if compiled.search(code):
            return False, f"Dangerous pattern detected: {pattern}"

    for dangerous in DANGEROUS_IMPORTS:
        # Check for 'import subprocess' style
        if dangerous.startswith("os.") or dangerous.startswith("shutil."):
            module, attr = dangerous.split(".", 1)
            if re.search(rf"\bimport\s+{re.escape(module)}\b", code):
                return False, f"Potentially dangerous module imported: {module}"
        elif dangerous in ("eval", "exec", "compile"):
            if re.search(rf"\b{re.escape(dangerous)}\s*\(", code):
                return False, f"Dangerous built-in used: {dangerous}"
        elif dangerous == "__import__":
            if "__import__" in code:
                return False, "Direct use of __import__ not allowed"
        elif dangerous == "subprocess":
            if re.search(r"\bimport\s+subprocess\b", code) or re.search(
                r"\bfrom\s+subprocess\b", code
            ):
                return False, "subprocess module not allowed"

    return True, None
