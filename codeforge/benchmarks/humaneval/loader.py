"""HumanEval benchmark loader."""

from __future__ import annotations

import gzip
import json
import logging
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

HUMANEVAL_URL = (
    "https://github.com/openai/human-eval/raw/master/data/HumanEval.jsonl.gz"
)
DEFAULT_DATA_DIR = Path(__file__).parent / "data"


@dataclass
class HumanEvalProblem:
    task_id: str          # e.g. 'HumanEval/0'
    prompt: str           # function signature + docstring
    canonical_solution: str
    test: str             # test function body
    entry_point: str      # function name to test


def download_humaneval(data_dir: str | Path = DEFAULT_DATA_DIR) -> Path:
    """Download HumanEval.jsonl.gz, extract it, and return the .jsonl path."""
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    gz_path = data_dir / "HumanEval.jsonl.gz"
    jsonl_path = data_dir / "HumanEval.jsonl"

    if not jsonl_path.exists():
        logger.info("Downloading HumanEval dataset from %s", HUMANEVAL_URL)
        try:
            urllib.request.urlretrieve(HUMANEVAL_URL, gz_path)
            with gzip.open(gz_path, "rb") as f_in, jsonl_path.open("wb") as f_out:
                f_out.write(f_in.read())
            gz_path.unlink(missing_ok=True)
            logger.info("HumanEval dataset saved to %s", jsonl_path)
        except Exception as exc:
            logger.error("Failed to download HumanEval: %s", exc)
            raise

    return jsonl_path


def load_problems(path: Optional[str | Path] = None) -> list[HumanEvalProblem]:
    """Load HumanEval problems from a JSONL file.

    If path is not provided, downloads to the default data directory.
    """
    if path is None:
        path = download_humaneval()

    path = Path(path)
    problems: list[HumanEvalProblem] = []

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            problems.append(
                HumanEvalProblem(
                    task_id=obj["task_id"],
                    prompt=obj["prompt"],
                    canonical_solution=obj["canonical_solution"],
                    test=obj["test"],
                    entry_point=obj["entry_point"],
                )
            )

    logger.info("Loaded %d HumanEval problems", len(problems))
    return problems
