#!/usr/bin/env python3
"""DEPRECATED wrapper for TypeScript disposition and work-order planning.

Use `pnpm tsx tooling/orchestration/disposition-candidates.ts <candidates> --work-orders`.
The TypeScript path loads canonical Postgres facts, emits Next.js/Postgres work
orders, and keeps D1 subordinate as an explicitly versioned D1 read replica.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SKILLS_REPO_ROOT = Path(__file__).resolve().parents[3]
WEBSITE_ROOT = SKILLS_REPO_ROOT.parent / "haltingproblems.com"
TS_CLI = WEBSITE_ROOT / "tooling" / "orchestration" / "disposition-candidates.ts"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates", type=Path, help="source-watcher JSON/YAML output")
    parser.add_argument("--existing-index", type=Path, help="DEPRECATED and ignored; Postgres is canonical")
    parser.add_argument("--update-slug", type=str, help="slug of post to run in update mode")
    parser.add_argument("--out", type=Path, help="write JSON output to this path")
    parser.add_argument("--facts", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()

    print(
        "DEPRECATED: work-order planning now runs in tooling/orchestration/disposition-candidates.ts; "
        "--existing-index is ignored.",
        file=sys.stderr,
    )
    command = ["pnpm", "exec", "tsx", str(TS_CLI), str(args.candidates), "--work-orders"]
    if args.update_slug:
        command.extend(["--update-slug", args.update_slug])
    if args.out:
        command.extend(["--out", str(args.out)])
    if args.facts:
        command.extend(["--facts", str(args.facts)])
    completed = subprocess.run(command, cwd=WEBSITE_ROOT, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
