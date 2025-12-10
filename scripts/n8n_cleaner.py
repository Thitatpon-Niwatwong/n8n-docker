#!/usr/bin/env python3
"""Normalize n8n workflow JSON for consistent diffs."""

from __future__ import annotations

import json
import sys


def main() -> int:
    raw = sys.stdin.read()
    try:
        # Preserve key order but normalize whitespace/indentation.
        payload = json.loads(raw)
    except json.JSONDecodeError:
        sys.stdout.write(raw)
        return 0

    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
