#!/usr/bin/env python3
"""DEPRECATED compatibility wrapper for the TypeScript disposition engine.

Usage:
  python dedupe_feed_decision.py candidate.json [ignored-existing-profiles ...]

The existing-profile arguments are accepted only for command compatibility.
Canonical facts are loaded from Postgres by scripts/disposition-candidates.ts.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TS_CLI = REPO_ROOT / "scripts" / "disposition-candidates.ts"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("existing", nargs="*", help="deprecated and ignored; Postgres is canonical")
    parser.add_argument("--facts", type=Path, help="test-only disposition facts JSON")
    args = parser.parse_args()

    print(
        "DEPRECATED: use `pnpm tsx scripts/disposition-candidates.ts`; "
        "legacy existing-profile files are ignored.",
        file=sys.stderr,
    )
    command = ["pnpm", "exec", "tsx", str(TS_CLI), str(args.candidate)]
    if args.facts:
        command.extend(["--facts", str(args.facts)])
    completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
