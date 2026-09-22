#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: ai <command> [args]")
        print("Commands: repo-init")
        return 1

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "repo-init":
        return subprocess.call([sys.executable, str(ROOT / "scripts" / "repo-init.py"), *args])

    print(f"Unknown command: {cmd}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
