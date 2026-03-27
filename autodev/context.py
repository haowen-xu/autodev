"""Thread context persistence helpers."""

from __future__ import annotations

import json
import time
from pathlib import Path


def load_context(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    thread_id = data.get("thread_id")
    if isinstance(thread_id, str) and thread_id.strip():
        return thread_id.strip()
    return None


def save_context(path: Path, thread_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"thread_id": thread_id}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_timestamped_context_file(context_dir: Path, stage: str) -> Path:
    while True:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        path = context_dir / f"{stage}.{stamp}.json"
        if not path.exists():
            return path
        time.sleep(1)
