"""Append-only log of every arm command, accepted or refused.

One JSON object per line in runs/YYYY-MM-DD.jsonl. The closure auditor reads these
raw files, so never edit or delete lines.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from swayam import REPO_ROOT

RUNS_DIR = REPO_ROOT / "runs"


def log_event(event: str, **fields) -> None:
    RUNS_DIR.mkdir(exist_ok=True)
    path = RUNS_DIR / f"{time.strftime('%Y-%m-%d')}.jsonl"
    record = {"t": time.time(), "event": event, **fields}
    with path.open("a") as f:
        f.write(json.dumps(record, default=str) + "\n")
