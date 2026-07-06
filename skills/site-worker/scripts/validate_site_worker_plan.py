#!/usr/bin/env python3
"""Validate modular site-worker plan contracts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_REVIEW_LANES = {
    "architecture_review",
    "data_quality_review",
    "incident_response_review",
    "workflow_qa_review",
    "technical_writing_review",
}


REQUIRED_TASK_SUFFIXES = {
    "01-scope-gate",
    "02-dedupe-and-disposition",
    "03-evidence-plan",
    "04-research-packet",
    "05-artifact-provenance",
    "06-soc-actionability",
    "07-ioc-package-normalization",
    "08-script-pack",
    "09-downstream-impact",
    "10-detection-pack",
    "11-post-draft",
    "12-schema-normalization",
    "13-architecture-review",
    "14-data-quality-review",
    "15-incident-response-review",
    "16-workflow-qa-review",
    "17-technical-writing-review",
    "18-synthesis-conflict-resolution",
    "19-publishability-gate",
}


def load_plan(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def task_suffix(task_id: str) -> str:
    parts = task_id.split("-")
    for index, part in enumerate(parts):
        if len(part) == 2 and part.isdigit():
            return "-".join(parts[index:])
    return task_id


def validate_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("site_worker_plan_version") != "2.0":
        errors.append("site_worker_plan_version must be 2.0")
    if plan.get("canonical_publication_target") != "nextjs-postgres":
        errors.append("canonical_publication_target must be nextjs-postgres")
    if plan.get("run_ledger_schema") != "skills/site-worker/references/site-worker-run-ledger-schema.json":
        errors.append("run_ledger_schema must reference skills/site-worker/references/site-worker-run-ledger-schema.json")

    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return errors + ["tasks must be a non-empty list"]

    task_ids: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict):
            errors.append("task must be an object")
            continue

        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            errors.append("task has missing task_id")
            continue
        if task_id in task_ids:
            errors.append(f"duplicate task_id: {task_id}")
        task_ids.add(task_id)

        if not task.get("artifact_path"):
            errors.append(f"{task_id}: missing artifact_path")
        if not task.get("acceptance_criteria"):
            errors.append(f"{task_id}: missing acceptance_criteria")
        if not isinstance(task.get("depends_on", []), list):
            errors.append(f"{task_id}: depends_on must be a list")

        if task.get("task_type") == "agency_review":
            if not task.get("review_lane"):
                errors.append(f"{task_id}: missing review_lane")
            agent_profile_path = task.get("agent_profile_path")
            if not isinstance(agent_profile_path, str) or not agent_profile_path.startswith(
                "/home/sam/agency-agents/"
            ):
                errors.append(f"{task_id}: agent_profile_path must reference /home/sam/agency-agents/")

    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = task.get("task_id", "<unknown>")
        dependencies = task.get("depends_on", [])
        if not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            if dependency not in task_ids:
                errors.append(f"{task_id}: unknown dependency {dependency}")

    suffix_counts: dict[str, int] = {}
    for task_id in task_ids:
        suffix = task_suffix(task_id)
        suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1

    for suffix in sorted(REQUIRED_TASK_SUFFIXES):
        if suffix not in suffix_counts:
            errors.append(f"missing required task suffix: {suffix}")
        elif suffix_counts[suffix] > 1:
            errors.append(f"duplicate required task suffix: {suffix}")

    review_lanes = {task.get("review_lane") for task in tasks if task.get("task_type") == "agency_review"}
    for lane in sorted(REQUIRED_REVIEW_LANES):
        if lane not in review_lanes:
            errors.append(f"missing required agency review lane: {lane}")

    publish_gates = [
        task for task in tasks if isinstance(task, dict) and task.get("task_id", "").endswith("19-publishability-gate")
    ]
    if len(publish_gates) != 1:
        errors.append("exactly one 19-publishability-gate task is required")
    elif publish_gates[0].get("blocks_publish") is not True:
        errors.append("publishability-gate must block publish")

    synthesis_tasks = [
        task
        for task in tasks
        if isinstance(task, dict) and task.get("task_id", "").endswith("18-synthesis-conflict-resolution")
    ]
    if len(synthesis_tasks) == 1:
        synthesis_dependencies = set(synthesis_tasks[0].get("depends_on", []))
        review_task_ids = {task["task_id"] for task in tasks if task.get("task_type") == "agency_review"}
        missing_reviews = sorted(review_task_ids - synthesis_dependencies)
        for review_id in missing_reviews:
            errors.append(f"{synthesis_tasks[0]['task_id']}: missing agency review dependency {review_id}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()

    errors = validate_plan(load_plan(args.plan))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("site-worker plan validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
