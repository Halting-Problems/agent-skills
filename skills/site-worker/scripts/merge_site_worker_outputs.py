#!/usr/bin/env python3
"""Merge validated specialist outputs into a site-worker result manifest."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


VALIDATOR_PATH = Path(__file__).resolve().with_name("validate_site_worker_plan.py")
_validator_spec = importlib.util.spec_from_file_location("site_worker_plan_merger_validator", VALIDATOR_PATH)
if _validator_spec is None or _validator_spec.loader is None:
    raise RuntimeError(f"cannot load site-worker validator: {VALIDATOR_PATH}")
_validator_module = importlib.util.module_from_spec(_validator_spec)
_validator_spec.loader.exec_module(_validator_module)
validate_plan = _validator_module.validate_plan
canonical_path = _validator_module.canonical_path


def load_plan(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(path: str) -> str:
    canonical = canonical_path(path)
    if canonical is None:
        raise ValueError(f"cannot resolve artifact path safely: {path}")
    return str(canonical)


def merge_outputs(
    *,
    plan: dict[str, Any],
    event_id: str,
    mode: str,
    decision: str,
    artifacts: list[str],
    blocking_gaps: list[str],
) -> dict[str, Any]:
    tasks = plan.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("plan tasks must be a list")
    if plan.get("event_id") != event_id:
        raise ValueError(f"event_id does not match plan: {event_id}")
    validation_errors = validate_plan(plan, execution=True)
    if validation_errors:
        raise ValueError(f"plan validation failed: {'; '.join(validation_errors)}")
    provided = {normalized(path) for path in artifacts}
    missing: list[str] = []
    for task in tasks:
        if not isinstance(task, dict) or task.get("blocks_publish") is not True:
            continue
        artifact = task.get("artifact_path")
        canonical_artifact = canonical_path(artifact) if isinstance(artifact, str) else None
        if (
            canonical_artifact is None
            or str(canonical_artifact) not in provided
            or not canonical_artifact.exists()
        ):
            missing.append(str(artifact))
    if missing:
        raise ValueError(f"missing publish-blocking artifacts: {', '.join(sorted(missing))}")
    if decision == "publish_ready" and blocking_gaps:
        raise ValueError("publish_ready cannot contain blocking gaps")
    task_ids = [task.get("task_id") for task in tasks if isinstance(task, dict)]
    return {
        "site_worker_result_version": "2.0",
        "mode": mode,
        "decision": decision,
        "event_id": event_id,
        "slug": event_id,
        "parent_campaign_id": "none",
        "spawned_tasks": task_ids,
        "completed_artifacts": artifacts,
        "validation_results": ["all declared publish-blocking artifacts exist"],
        "blocking_gaps": blocking_gaps,
        "recommended_next_action": "Review blocking gaps" if blocking_gaps else "Run publication gate",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--mode", default="new_incident_post")
    parser.add_argument("--decision", default="needs_review")
    parser.add_argument("--artifact", action="append", default=[], help="Path to completed artifact")
    parser.add_argument("--blocking-gap", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = load_plan(args.plan)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"invalid site-worker plan: {error}", file=sys.stderr)
        return 2
    try:
        result = merge_outputs(
            plan=plan,
            event_id=args.event_id,
            mode=args.mode,
            decision=args.decision,
            artifacts=args.artifact,
            blocking_gaps=args.blocking_gap,
        )
    except ValueError as error:
        print(f"ERROR: {error}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
