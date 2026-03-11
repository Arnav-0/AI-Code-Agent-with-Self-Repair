"""MBPP benchmark loader."""

from __future__ import annotations

import json
import logging
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MBPP_URL = (
    "https://raw.githubusercontent.com/google-research/google-research"
    "/master/mbpp/mbpp.jsonl"
)
DEFAULT_DATA_DIR = Path(__file__).parent / "data"


@dataclass
class MBPPProblem:
    task_id: int
    text: str               # task description
    code: str               # reference solution
    test_list: list[str]    # assertion strings
    test_setup_code: str = ""


def download_mbpp(data_dir: str | Path = DEFAULT_DATA_DIR) -> Path:
    """Download mbpp.jsonl and return the file path."""
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = data_dir / "mbpp.jsonl"

    if not jsonl_path.exists():
        logger.info("Downloading MBPP dataset from %s", MBPP_URL)
        try:
            urllib.request.urlretrieve(MBPP_URL, jsonl_path)
            logger.info("MBPP dataset saved to %s", jsonl_path)
        except Exception as exc:
            logger.error("Failed to download MBPP: %s", exc)
            raise

    return jsonl_path


def load_problems(path: Optional[str | Path] = None) -> list[MBPPProblem]:
    """Load MBPP problems from a JSONL file.

    If path is not provided, downloads to the default data directory.
    """
    if path is None:
        path = download_mbpp()

    path = Path(path)
    problems: list[MBPPProblem] = []

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            problems.append(
                MBPPProblem(
                    task_id=obj["task_id"],
                    text=obj["text"],
                    code=obj["code"],
                    test_list=obj.get("test_list", []),
                    test_setup_code=obj.get("test_setup_code", ""),
                )
            )

    logger.info("Loaded %d MBPP problems", len(problems))
    return problems
