"""Append-only log of every arm command, accepted or refused.

One JSON object per line in runs/YYYY-MM-DD.jsonl. The closure auditor reads these
raw files, so never edit or delete lines.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from swayam import REPO_ROOT


def runs_dir() -> Path:
    """runs/ in the repo, unless SWAYAM_RUNS_DIR points elsewhere (tests do)."""
    return Path(os.environ.get("SWAYAM_RUNS_DIR", REPO_ROOT / "runs"))


def log_event(event: str, **fields) -> None:
    d = runs_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{time.strftime('%Y-%m-%d')}.jsonl"
    record = {"t": time.time(), "event": event, **fields}
    tag = os.environ.get("SWAYAM_RUN_TAG")  # experiment harnesses tag their attempts
    if tag:
        record["run_tag"] = tag
    with path.open("a") as f:
        f.write(json.dumps(record, default=str) + "\n")
