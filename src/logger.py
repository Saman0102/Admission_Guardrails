"""Simple JSON-lines decision logger for the assignment."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class DecisionLogger:
    """Append one complete decision record per request."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, record: dict[str, Any]) -> None:
        payload = dict(record)
        payload.setdefault(
            "timestamp",
            datetime.now(timezone.utc).isoformat(),
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
