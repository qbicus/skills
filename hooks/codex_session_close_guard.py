#!/usr/bin/env python3
"""
Codex Stop hook guard for session-close.

This script is intentionally conservative. It only asks Codex to continue and run
session-close when a repository appears to have meaningful unclosed work.

Expected use from ~/.codex/hooks.json:

{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"%USERPROFILE%\\.ai\\hooks\\codex_session_close_guard.py\"",
            "statusMessage": "Checking whether session-close is needed"
          }
        ]
      }
    ]
  }
}
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def emit(obj: dict) -> None:
    print(json.dumps(obj))


def run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, timeout=5)
        return p.returncode, p.stdout, p.stderr
    except Exception as exc:
        return 1, "", str(exc)


def find_repo(start: Path) -> Path | None:
    current = start.resolve()
    for p in [current, *current.parents]:
        if (p / ".git").exists():
            return p
    return None


def dirty_hash(status: str) -> str:
    return hashlib.sha256(status.encode("utf-8")).hexdigest()


def main() -> None:
    raw = sys.stdin.read() or "{}"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = {}

    # Avoid hook loops.
    if payload.get("stop_hook_active"):
        emit({"continue": True})
        return

    cwd = Path(payload.get("cwd") or os.getcwd())
    repo = find_repo(cwd)
    if repo is None:
        emit({"continue": True})
        return

    ai_dir = repo / ".ai"
    if not ai_dir.exists():
        emit({"continue": True})
        return

    code, status, _ = run(["git", "status", "--porcelain"], repo)
    if code != 0 or not status.strip():
        emit({"continue": True})
        return

    state_file = ai_dir / ".session-state.json"
    current_dirty_hash = dirty_hash(status)
    state = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    if state.get("lastKnownDirtyHash") == current_dirty_hash:
        emit({"continue": True})
        return

    reason = (
        "Before stopping or switching context, run the `session-close` skill. "
        "Update .ai/current-work.md, .ai/decisions.md if decisions were made, "
        "task trackers such as dev-todos.md if present, blockers, next steps, and restart notes. "
        "Then update .ai/.session-state.json with lastSessionCloseUtc and lastKnownDirtyHash."
    )
    emit({"decision": "block", "reason": reason})


if __name__ == "__main__":
    main()
