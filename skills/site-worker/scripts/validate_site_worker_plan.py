#!/usr/bin/env python3
"""Validate adaptive site-worker plans and, optionally, their execution artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePath
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from jsonschema.exceptions import SchemaError
except ImportError:  # Execution validation must fail closed when unavailable.
    Draft202012Validator = None
    FormatChecker = None
    SchemaError = Exception


REPO_ROOT = Path(__file__).resolve().parents[3]
AGENCY_PROFILE_ROOT = Path("/home/sam/agency-agents").resolve()
RUNNERS = {"halting_skill", "agency_review", "command", "gate"}
STATUSES = {"pending", "running", "completed", "blocked", "failed", "skipped"}
REQUIRED_REVIEW_LANES = {
    "architecture_review",
    "data_quality_review",
    "incident_response_review",
    "workflow_qa_review",
    "technical_writing_review",
}
REQUIRED_TASK_NAMES = {
    "scope-gate",
    "dedupe-and-disposition",
    "evidence-plan",
    "research-packet",
    "ioc-package-normalization",
    "soc-actionability",
    "post-draft",
    "schema-normalization",
    "synthesis-conflict-resolution",
    "postgres-import",
    "production-verification",
    "publishability-gate",
}


def load_plan(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def task_name(task_id: str, event_id: str = "") -> str:
    if event_id and task_id.startswith(f"{event_id}-"):
        remainder = task_id[len(event_id) + 1 :]
        sequence, separator, name = remainder.partition("-")
        if separator and len(sequence) == 2 and sequence.isdigit():
            return name
    parts = task_id.rsplit("-", 2)
    if len(parts) == 3 and len(parts[1]) == 2 and parts[1].isdigit():
        return parts[2]
    return task_id


def path_has_traversal(value: str) -> bool:
    return not value or "\x00" in value or value.startswith("~") or ".." in PurePath(value).parts


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else REPO_ROOT / path


def canonical_path(value: str) -> Path | None:
    try:
        unresolved = resolve_path(value)
        for parent in (unresolved, *unresolved.parents):
            if parent.is_symlink():
                parent.resolve(strict=True)
        return unresolved.resolve(strict=False)
    except (OSError, RuntimeError):
        return None


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def artifact_schema_errors(task_id: str, payload: Any, schema_path: Path) -> list[str]:
    if Draft202012Validator is None or FormatChecker is None:
        return [f"{task_id}: jsonschema dependency is unavailable"]
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validation_errors = sorted(
            Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(payload),
            key=lambda error: list(error.absolute_path),
        )
    except (OSError, json.JSONDecodeError, SchemaError) as error:
        return [f"{task_id}: invalid artifact schema: {error}"]
    return [
        f"{task_id}: does not satisfy artifact schema at "
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in validation_errors
    ]


def markdown_artifact_errors(task_id: str, artifact: Path) -> list[str]:
    try:
        content = artifact.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return [f"{task_id}: Markdown artifact cannot be read: {error}"]
    frontmatter = re.match(r"\A---\s*\n(.*?)\n---\s*\n", content, flags=re.DOTALL)
    if frontmatter is None:
        return [f"{task_id}: Markdown artifact is missing YAML frontmatter"]
    metadata = frontmatter.group(1)
    required_keys = {"title", "date", "severity", "tags", "summary", "sourceCount"}
    present_keys = {
        match.group(1)
        for match in re.finditer(r"^([A-Za-z][A-Za-z0-9]*):", metadata, flags=re.MULTILINE)
    }
    errors = [
        f"{task_id}: Markdown artifact is missing frontmatter key {key}"
        for key in sorted(required_keys - present_keys)
    ]
    required_sections = {
        "Executive Summary",
        "Evidence Assessment",
        "Detection and Hunting",
        "Remediation and Recovery Gates",
        "Indicators of Compromise",
        "Sources",
    }
    headings = set(re.findall(r"^##\s+(.+?)\s*$", content, flags=re.MULTILINE))
    errors.extend(
        f"{task_id}: Markdown artifact is missing section {section}"
        for section in sorted(required_sections - headings)
    )
    count_match = re.search(r"^sourceCount:\s*(\d+)\s*$", metadata, flags=re.MULTILINE)
    source_references = re.findall(
        r"^(?:\[\d+\]|\d+\.)\s+https?://\S+",
        content,
        flags=re.MULTILINE,
    )
    if count_match is None:
        errors.append(f"{task_id}: Markdown artifact sourceCount must be an integer")
    elif int(count_match.group(1)) != len(source_references):
        errors.append(f"{task_id}: Markdown artifact sourceCount does not match source references")
    return errors


def _cycle_errors(tasks: list[dict[str, Any]], task_ids: set[str]) -> list[str]:
    dependencies = {
        task["task_id"]: [
            item
            for item in task.get("depends_on", [])
            if isinstance(item, str) and item in task_ids
        ]
        if isinstance(task.get("depends_on"), list)
        else []
        for task in tasks
        if isinstance(task.get("task_id"), str)
    }
    visiting: set[str] = set()
    visited: set[str] = set()
    errors: list[str] = []

    def visit(task_id: str, stack: list[str]) -> None:
        if task_id in visiting:
            start = stack.index(task_id) if task_id in stack else 0
            errors.append(f"dependency cycle: {' -> '.join(stack[start:] + [task_id])}")
            return
        if task_id in visited:
            return
        visiting.add(task_id)
        stack.append(task_id)
        for dependency in dependencies.get(task_id, []):
            visit(dependency, stack)
        stack.pop()
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in dependencies:
        visit(task_id, [])
    return errors


def _execution_errors(plan: dict[str, Any], tasks: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    source_time = parse_time(plan.get("source_version_at"))
    source_hash = str(plan.get("source_version_hash") or "")
    event_id = str(plan.get("event_id") or "")
    if source_time is None:
        errors.append("source_version_at must be a valid timestamp in execution mode")
    if not source_hash or source_hash == "unknown":
        errors.append("source_version_hash must identify the source version in execution mode")
    profile_value = plan.get("profile_path")
    expected_profile_hash = plan.get("profile_content_hash")
    if not isinstance(profile_value, str) or not isinstance(expected_profile_hash, str):
        errors.append("profile content identity is missing in execution mode")
    else:
        profile_path = canonical_path(profile_value)
        try:
            actual_profile_hash = (
                hashlib.sha256(profile_path.read_bytes()).hexdigest()
                if profile_path is not None and profile_path.is_file()
                else None
            )
        except OSError:
            actual_profile_hash = None
        if actual_profile_hash != expected_profile_hash:
            errors.append("profile content changed since plan generation")
    parsed_artifacts: dict[str, Any] = {}

    for task in tasks:
        task_id = str(task.get("task_id", "<unknown>"))
        artifact_value = task.get("artifact_path")
        if not isinstance(artifact_value, str) or path_has_traversal(artifact_value):
            continue
        artifact_source = resolve_path(artifact_value)
        if artifact_source.is_symlink():
            errors.append(f"{task_id}: artifact must be a regular file, not a symlink")
            continue
        artifact = canonical_path(artifact_value)
        if artifact is None:
            errors.append(f"{task_id}: cannot resolve artifact safely: {artifact_value}")
            continue
        if not artifact.exists():
            errors.append(f"{task_id}: artifact does not exist: {artifact_value}")
            continue
        if not artifact.is_file():
            errors.append(f"{task_id}: artifact must be a regular file: {artifact_value}")
            continue
        if source_time is not None:
            modified_at = datetime.fromtimestamp(artifact.stat().st_mtime, tz=timezone.utc)
            if modified_at < source_time:
                errors.append(f"{task_id}: stale artifact predates source version: {artifact_value}")
        schema_value = task.get("artifact_schema")
        schema: Path | None = None
        if isinstance(schema_value, str) and schema_value:
            schema = canonical_path(schema_value)
            if schema is None:
                errors.append(f"{task_id}: cannot resolve artifact schema safely: {schema_value}")
            elif not schema.exists():
                errors.append(f"{task_id}: artifact schema does not exist: {schema_value}")
            elif not schema.is_file():
                errors.append(f"{task_id}: artifact schema must be a file: {schema_value}")
        if artifact.is_file() and artifact.suffix.lower() == ".json":
            try:
                payload = json.loads(artifact.read_text(encoding="utf-8"))
                parsed_artifacts[task_id] = payload
                if schema is not None and schema.is_file():
                    errors.extend(artifact_schema_errors(task_id, payload, schema))
                if not isinstance(payload, dict):
                    errors.append(f"{task_id}: JSON artifact must be an object")
                else:
                    if payload.get("task_id") != task_id:
                        errors.append(f"{task_id}: artifact task_id does not match")
                    if not source_hash or source_hash == "unknown" or payload.get("source_version_hash") != source_hash:
                        errors.append(f"{task_id}: artifact source version is stale or missing")
                    completed_at = parse_time(payload.get("completed_at"))
                    if completed_at is None:
                        errors.append(f"{task_id}: artifact completed_at is missing or invalid")
                    elif source_time is not None and completed_at < source_time:
                        errors.append(f"{task_id}: stale artifact completion predates source version")
                    if task.get("runner") == "command" and (
                        payload.get("exit_code") != 0 or payload.get("command") != task.get("command")
                    ):
                        errors.append(f"{task_id}: command success evidence is missing or mismatched")
            except (OSError, json.JSONDecodeError):
                if task.get("runner") == "agency_review":
                    errors.append(f"{task_id}: malformed review artifact")
                else:
                    errors.append(f"{task_id}: malformed JSON artifact")
        elif artifact.suffix.lower() == ".md":
            errors.extend(markdown_artifact_errors(task_id, artifact))
        if task.get("blocks_publish") is True and task.get("status") != "completed":
            errors.append(f"{task_id}: publish-blocking task must be completed in execution mode")

    for task in tasks:
        if task.get("runner") != "agency_review":
            continue
        task_id = str(task.get("task_id", "<unknown>"))
        if task.get("status") != "completed":
            errors.append(f"{task_id}: agency review must be completed in execution mode")
        artifact = parsed_artifacts.get(task_id)
        if not isinstance(artifact, dict):
            if not any(error.startswith(f"{task_id}: malformed review") for error in errors):
                errors.append(f"{task_id}: malformed review artifact")
            continue
        decision = artifact.get("decision")
        if decision not in {"pass", "pass_with_warnings", "block"}:
            errors.append(f"{task_id}: invalid or missing review decision")
        if task.get("blocks_publish") is True and decision == "block":
            errors.append(f"{task_id}: review decision block")
        findings = artifact.get("blocking_findings", [])
        if not isinstance(findings, list):
            errors.append(f"{task_id}: blocking_findings must be a list")
        elif task.get("blocks_publish") is True and findings:
            errors.append(f"{task_id}: blocking finding prevents publication")
        artifact_hash = artifact.get("source_version_hash")
        if source_hash and artifact_hash != source_hash:
            errors.append(f"{task_id}: review source version is stale or missing")

    for task in tasks:
        if task.get("runner") != "gate" or task.get("blocks_publish") is not True:
            continue
        name = task_name(str(task.get("task_id", "")), event_id)
        task_id = str(task.get("task_id", "<unknown>"))
        artifact = parsed_artifacts.get(task_id)
        if not isinstance(artifact, dict):
            continue
        decision = artifact.get("decision")
        findings = artifact.get("blocking_findings")
        if name == "scope-gate":
            allowed = {"in_scope", "pass", "pass_with_warnings"}
        elif name == "dedupe-and-disposition":
            allowed = {"new", "update", "campaign", "pass", "pass_with_warnings"}
        elif name == "publishability-gate":
            allowed = {"publish_ready", "pass", "pass_with_warnings"}
        else:
            allowed = {"pass", "pass_with_warnings"}
        if decision not in allowed or not isinstance(findings, list) or findings:
            errors.append(f"{name} does not allow publication")

    import_task = next((task for task in tasks if task_name(str(task.get("task_id", "")), event_id) == "postgres-import"), None)
    verification_task = next((task for task in tasks if task_name(str(task.get("task_id", "")), event_id) == "production-verification"), None)
    if import_task is not None and import_task.get("status") != "completed":
        errors.append("Postgres import must be completed before publication")
    if verification_task is not None and verification_task.get("status") != "completed":
        errors.append("production verification must be completed before publication")
    return errors


def validate_plan(plan: dict[str, Any], *, execution: bool = False) -> list[str]:
    errors: list[str] = []
    if plan.get("site_worker_plan_version") != "3.0":
        errors.append("site_worker_plan_version must be 3.0")
    if plan.get("canonical_publication_target") != "nextjs-postgres":
        errors.append("canonical_publication_target must be nextjs-postgres")
    if plan.get("run_ledger_schema") != "skills/site-worker/references/site-worker-run-ledger-schema.json":
        errors.append("run_ledger_schema must reference skills/site-worker/references/site-worker-run-ledger-schema.json")
    profile_path = plan.get("profile_path")
    artifact_root = plan.get("artifact_root")
    event_id = str(plan.get("event_id") or "")
    if not isinstance(profile_path, str) or path_has_traversal(profile_path):
        errors.append("profile_path must be a safe path")
    if not isinstance(artifact_root, str) or path_has_traversal(artifact_root):
        errors.append("artifact_root must be a safe path")
        canonical_artifact_root = None
    else:
        canonical_artifact_root = canonical_path(artifact_root)
        if canonical_artifact_root is None:
            errors.append("artifact_root cannot be resolved safely")

    raw_tasks = plan.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        return errors + ["tasks must be a non-empty list"]
    tasks = [task for task in raw_tasks if isinstance(task, dict)]
    if len(tasks) != len(raw_tasks):
        errors.append("task must be an object")

    task_ids: set[str] = set()
    artifact_producers: dict[str, str] = {}
    canonical_artifact_producers: dict[str, str] = {}
    positions: dict[str, int] = {}
    for position, task in enumerate(tasks):
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            errors.append("task has missing task_id")
            continue
        if task_id in task_ids:
            errors.append(f"duplicate task_id: {task_id}")
        task_ids.add(task_id)
        positions[task_id] = position
        for field in ["runner", "inputs", "artifact_path", "artifact_schema", "depends_on", "blocks_publish", "status", "acceptance_criteria"]:
            if field not in task:
                errors.append(f"{task_id}: missing {field}")
        if task.get("runner") not in RUNNERS:
            errors.append(f"{task_id}: invalid runner")
        if task.get("runner") == "command":
            command = task.get("command")
            if not isinstance(command, list) or not command or not all(isinstance(argument, str) and argument for argument in command):
                errors.append(f"{task_id}: command must be a non-empty argv list")
        if task.get("status") not in STATUSES:
            errors.append(f"{task_id}: invalid status")
        if not isinstance(task.get("blocks_publish"), bool):
            errors.append(f"{task_id}: blocks_publish must be a boolean")
        if not isinstance(task.get("inputs"), list):
            errors.append(f"{task_id}: inputs must be a list")
        if not isinstance(task.get("depends_on"), list):
            errors.append(f"{task_id}: depends_on must be a list")
        if not isinstance(task.get("acceptance_criteria"), list) or not task.get("acceptance_criteria"):
            errors.append(f"{task_id}: missing acceptance_criteria")
        for path_field in ["artifact_path", "artifact_schema"]:
            value = task.get(path_field)
            if not isinstance(value, str):
                errors.append(f"{task_id}: {path_field} must be a string")
            elif value and path_has_traversal(value):
                errors.append(f"{task_id}: {path_field} contains path traversal")
        artifact_path = task.get("artifact_path")
        if isinstance(artifact_path, str) and artifact_path:
            artifact_producers[artifact_path] = task_id
            canonical_artifact = canonical_path(artifact_path)
            if canonical_artifact is None:
                errors.append(f"{task_id}: cannot resolve artifact_path safely")
            else:
                canonical_key = str(canonical_artifact)
                if canonical_key in canonical_artifact_producers:
                    errors.append(f"duplicate artifact_path: {artifact_path}")
                canonical_artifact_producers[canonical_key] = task_id
                if canonical_artifact_root is not None and not canonical_artifact.is_relative_to(canonical_artifact_root):
                    errors.append(f"{task_id}: artifact_path is outside artifact_root")
        if task.get("runner") == "agency_review":
            lane = task.get("review_lane")
            if not isinstance(lane, str) or lane not in REQUIRED_REVIEW_LANES:
                errors.append(f"{task_id}: missing or invalid review_lane")
            agent_profile = task.get("agent_profile_path")
            canonical_agent_profile = (
                canonical_path(agent_profile)
                if isinstance(agent_profile, str) and not path_has_traversal(agent_profile)
                else None
            )
            if (
                canonical_agent_profile is None
                or not canonical_agent_profile.is_relative_to(AGENCY_PROFILE_ROOT)
            ):
                errors.append(f"{task_id}: invalid agent_profile_path")

    errors.extend(_cycle_errors(tasks, task_ids))
    external_inputs = {profile_path} if isinstance(profile_path, str) else set()
    for task in tasks:
        task_id = task.get("task_id")
        if not isinstance(task_id, str):
            continue
        dependencies = task.get("depends_on", [])
        if not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            if not isinstance(dependency, str):
                errors.append(f"{task_id}: dependency must be a task_id string")
            elif dependency not in task_ids:
                errors.append(f"{task_id}: unknown dependency {dependency}")
            elif positions[dependency] >= positions[task_id]:
                errors.append(f"{task_id}: dependency {dependency} violates topological order")
        inputs = task.get("inputs", [])
        if not isinstance(inputs, list):
            continue
        for value in inputs:
            if not isinstance(value, str) or path_has_traversal(value):
                errors.append(f"{task_id}: input contains path traversal")
                continue
            if value in external_inputs:
                continue
            producer = artifact_producers.get(value)
            if producer is None:
                errors.append(f"{task_id}: missing input producer for {value}")
            elif producer not in dependencies:
                errors.append(f"{task_id}: input producer {producer} is not a direct dependency")

    names = {task_name(task_id, event_id) for task_id in task_ids}
    for name in sorted(REQUIRED_TASK_NAMES - names):
        errors.append(f"missing required task: {name}")
    review_lanes = {
        task.get("review_lane")
        for task in tasks
        if task.get("runner") == "agency_review" and isinstance(task.get("review_lane"), str)
    }
    for lane in sorted(REQUIRED_REVIEW_LANES - review_lanes):
        errors.append(f"missing required agency review lane: {lane}")

    synthesis = next((task for task in tasks if task_name(str(task.get("task_id", "")), event_id) == "synthesis-conflict-resolution"), None)
    if synthesis is not None:
        synthesis_dependencies = {
            dependency
            for dependency in synthesis.get("depends_on", [])
            if isinstance(dependency, str)
        } if isinstance(synthesis.get("depends_on"), list) else set()
        for review in [task for task in tasks if task.get("runner") == "agency_review"]:
            if review.get("task_id") not in synthesis_dependencies:
                errors.append(f"{synthesis['task_id']}: missing agency review dependency {review.get('task_id')}")

    publish_gate = next((task for task in tasks if task_name(str(task.get("task_id", "")), event_id) == "publishability-gate"), None)
    import_task = next((task for task in tasks if task_name(str(task.get("task_id", "")), event_id) == "postgres-import"), None)
    verification_task = next((task for task in tasks if task_name(str(task.get("task_id", "")), event_id) == "production-verification"), None)
    if publish_gate is not None:
        if publish_gate.get("blocks_publish") is not True:
            errors.append("publishability-gate must block publish")
        raw_dependencies = publish_gate.get("depends_on", [])
        dependencies = {
            dependency for dependency in raw_dependencies if isinstance(dependency, str)
        } if isinstance(raw_dependencies, list) else set()
        if import_task is not None and import_task.get("task_id") not in dependencies:
            errors.append("publishability-gate must depend on Postgres import")
        if verification_task is not None and verification_task.get("task_id") not in dependencies:
            errors.append("publishability-gate must depend on production verification")
    if verification_task is not None and import_task is not None:
        raw_dependencies = verification_task.get("depends_on", [])
        dependencies = {
            dependency for dependency in raw_dependencies if isinstance(dependency, str)
        } if isinstance(raw_dependencies, list) else set()
        if import_task.get("task_id") not in dependencies:
            errors.append("production verification must depend on Postgres import")

    if execution:
        errors.extend(_execution_errors(plan, tasks))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--artifacts", action="store_true", help="Validate execution artifacts and publish gates")
    args = parser.parse_args()
    try:
        plan = load_plan(args.plan)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"invalid site-worker plan: {error}", file=sys.stderr)
        return 2
    errors = validate_plan(plan, execution=args.artifacts)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("site-worker plan validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
