from __future__ import annotations

import importlib.util
import json
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
VALID_POST_DRAFT = """---
title: "Execution Case"
date: 2026-07-11
severity: "high"
tags:
  - test
summary: "Validated execution artifact."
sourceCount: 1
---

## Executive Summary
Validated summary.

## Evidence Assessment
Validated evidence.

## Detection and Hunting
Validated detection guidance.

## Remediation and Recovery Gates
Validated remediation.

## Indicators of Compromise
No published indicators.

## Sources
[1] https://example.test/source
"""


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


planner = load_module("site_worker_plan")
validator = load_module("validate_site_worker_plan")
merger = load_module("merge_site_worker_outputs")


def execution_plan(tmp_path: Path) -> dict:
    profile_path = tmp_path / "profile.json"
    profile_path.write_text("{}", encoding="utf-8")
    plan = planner.make_tasks(
        profile_path,
        {
            "event_id": "execution-case",
            "event_name": "Execution Case",
            "attack_types": ["known exploited vulnerability"],
            "source_version_hash": "b" * 64,
            "source_version_at": "2020-01-01T00:00:00Z",
        },
        artifact_root=tmp_path / "artifacts",
    )
    for task in plan["tasks"]:
        path = Path(task["artifact_path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "task_id": task["task_id"],
            "source_version_hash": plan["source_version_hash"],
            "completed_at": "2026-07-11T01:00:00Z",
        }
        if task["runner"] in {"agency_review", "gate"}:
            payload.update({"decision": "pass", "blocking_findings": [], "warnings": []})
        if task["runner"] == "command":
            payload.update({"command": task["command"], "exit_code": 0})
        if path.suffix == ".md":
            path.write_text(VALID_POST_DRAFT, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        task["status"] = "completed"
    return plan


def by_suffix(plan: dict, suffix: str) -> dict:
    return next(task for task in plan["tasks"] if task["task_id"].endswith(suffix))


def test_execution_mode_accepts_complete_fresh_artifacts(tmp_path: Path):
    plan = execution_plan(tmp_path)
    assert validator.validate_plan(plan, execution=True) == []


def test_execution_mode_rejects_missing_artifact_and_schema(tmp_path: Path):
    plan = execution_plan(tmp_path)
    Path(plan["tasks"][2]["artifact_path"]).unlink()
    errors = validator.validate_plan(plan, execution=True)
    assert any("artifact does not exist" in error for error in errors)

    plan = execution_plan(tmp_path)
    plan["tasks"][0]["artifact_schema"] = str(tmp_path / "missing.schema.json")
    errors = validator.validate_plan(plan, execution=True)
    assert any("artifact schema does not exist" in error for error in errors)


def test_execution_mode_rejects_stale_artifact(tmp_path: Path):
    plan = execution_plan(tmp_path)
    plan["source_version_at"] = "2030-01-01T00:00:00Z"
    errors = validator.validate_plan(plan, execution=True)
    assert any("stale artifact" in error for error in errors)


def test_execution_mode_rejects_blocking_or_malformed_required_review(tmp_path: Path):
    plan = execution_plan(tmp_path)
    review = next(task for task in plan["tasks"] if task.get("review_lane") == "architecture_review")
    Path(review["artifact_path"]).write_text(
        json.dumps({"decision": "block", "blocking_findings": ["unsafe dependency"]}),
        encoding="utf-8",
    )
    errors = validator.validate_plan(plan, execution=True)
    assert any("review decision block" in error for error in errors)
    assert any("blocking finding" in error for error in errors)

    plan = execution_plan(tmp_path)
    review = next(task for task in plan["tasks"] if task.get("review_lane") == "data_quality_review")
    Path(review["artifact_path"]).write_text("not-json", encoding="utf-8")
    assert any("malformed review artifact" in error for error in validator.validate_plan(plan, execution=True))


def test_execution_mode_requires_completed_import_and_production_verification(tmp_path: Path):
    plan = execution_plan(tmp_path)
    by_suffix(plan, "postgres-import")["status"] = "pending"
    by_suffix(plan, "production-verification")["status"] = "blocked"
    errors = validator.validate_plan(plan, execution=True)
    assert any("Postgres import must be completed" in error for error in errors)
    assert any("production verification must be completed" in error for error in errors)


def test_merger_rejects_missing_blocking_artifact(tmp_path: Path):
    plan = execution_plan(tmp_path)
    blocking_paths = [task["artifact_path"] for task in plan["tasks"] if task["blocks_publish"]]
    missing = blocking_paths.pop()
    try:
        merger.merge_outputs(
            plan=plan,
            event_id="execution-case",
            mode="new_incident_post",
            decision="publish_ready",
            artifacts=blocking_paths,
            blocking_gaps=[],
        )
    except ValueError as error:
        assert missing in str(error)
    else:
        raise AssertionError("merge_outputs accepted a missing publish-blocking artifact")

    result = merger.merge_outputs(
        plan=plan,
        event_id="execution-case",
        mode="new_incident_post",
        decision="publish_ready",
        artifacts=[task["artifact_path"] for task in plan["tasks"]],
        blocking_gaps=[],
    )
    assert result["decision"] == "publish_ready"
    assert len(result["completed_artifacts"]) == len(plan["tasks"])


def test_execution_mode_requires_valid_source_version_metadata(tmp_path: Path):
    plan = execution_plan(tmp_path)
    plan["source_version_at"] = "not-a-timestamp"
    assert any("source_version_at" in error for error in validator.validate_plan(plan, execution=True))

    plan = execution_plan(tmp_path)
    artifact = Path(plan["tasks"][0]["artifact_path"])
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["source_version_hash"] = "stale"
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    assert any("artifact source version" in error for error in validator.validate_plan(plan, execution=True))

    plan = execution_plan(tmp_path)
    artifact = Path(plan["tasks"][0]["artifact_path"])
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["completed_at"] = "2019-01-01T00:00:00Z"
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    assert any("completion predates source version" in error for error in validator.validate_plan(plan, execution=True))


def test_merger_rejects_a_plan_that_bypasses_publish_gates(tmp_path: Path):
    plan = execution_plan(tmp_path)
    by_suffix(plan, "publishability-gate")["blocks_publish"] = False
    try:
        merger.merge_outputs(
            plan=plan,
            event_id="execution-case",
            mode="new_incident_post",
            decision="publish_ready",
            artifacts=[task["artifact_path"] for task in plan["tasks"]],
            blocking_gaps=[],
        )
    except ValueError as error:
        assert "plan validation failed" in str(error)
    else:
        raise AssertionError("merge_outputs accepted an invalid publication plan")


def test_execution_mode_requires_every_review_to_be_completed(tmp_path: Path):
    plan = execution_plan(tmp_path)
    review = next(task for task in plan["tasks"] if task.get("review_lane") == "technical_writing_review")
    assert review["blocks_publish"] is False
    review["status"] = "pending"
    assert any("agency review must be completed" in error for error in validator.validate_plan(plan, execution=True))


def test_execution_mode_requires_schema_to_be_a_file(tmp_path: Path):
    plan = execution_plan(tmp_path)
    schema_directory = tmp_path / "schema-directory"
    schema_directory.mkdir()
    plan["tasks"][0]["artifact_schema"] = str(schema_directory)
    assert any("artifact schema must be a file" in error for error in validator.validate_plan(plan, execution=True))


def test_execution_rejects_directory_artifacts(tmp_path: Path):
    plan = execution_plan(tmp_path)
    artifact = Path(plan["tasks"][0]["artifact_path"])
    artifact.unlink()
    artifact.mkdir()
    assert any("artifact must be a regular file" in error for error in validator.validate_plan(plan, execution=True))


def test_execution_rejects_symlink_artifacts(tmp_path: Path):
    plan = execution_plan(tmp_path)
    artifact = Path(plan["tasks"][0]["artifact_path"])
    target = artifact.with_name("real-artifact.json")
    artifact.rename(target)
    artifact.symlink_to(target)
    assert any("not a symlink" in error for error in validator.validate_plan(plan, execution=True))


def test_execution_applies_declared_json_schema(tmp_path: Path):
    plan = execution_plan(tmp_path)
    artifact = Path(plan["tasks"][0]["artifact_path"])
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["completed_at"] = 123
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    assert any("does not satisfy artifact schema" in error for error in validator.validate_plan(plan, execution=True))


def test_execution_rejects_malformed_declared_schema(tmp_path: Path):
    plan = execution_plan(tmp_path)
    schema = tmp_path / "malformed.schema.json"
    schema.write_text("not-json", encoding="utf-8")
    plan["tasks"][0]["artifact_schema"] = str(schema)
    assert any("invalid artifact schema" in error for error in validator.validate_plan(plan, execution=True))


def test_execution_validates_markdown_post_contract(tmp_path: Path):
    plan = execution_plan(tmp_path)
    post = by_suffix(plan, "post-draft")
    Path(post["artifact_path"]).write_text("arbitrary text", encoding="utf-8")
    assert any("Markdown artifact" in error for error in validator.validate_plan(plan, execution=True))


def test_merger_rejects_publish_ready_when_gate_blocks(tmp_path: Path):
    plan = execution_plan(tmp_path)
    gate = by_suffix(plan, "publishability-gate")
    gate_path = Path(gate["artifact_path"])
    payload = json.loads(gate_path.read_text(encoding="utf-8"))
    payload.update({"decision": "block", "blocking_findings": ["unresolved conflict"]})
    gate_path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        merger.merge_outputs(
            plan=plan,
            event_id="execution-case",
            mode="new_incident_post",
            decision="publish_ready",
            artifacts=[task["artifact_path"] for task in plan["tasks"]],
            blocking_gaps=[],
        )
    except ValueError as error:
        assert "publishability-gate does not allow publication" in str(error)
    else:
        raise AssertionError("merge_outputs accepted publish_ready for a blocking gate")


def test_advisory_review_findings_do_not_block_publication(tmp_path: Path):
    plan = execution_plan(tmp_path)
    review = next(task for task in plan["tasks"] if task.get("review_lane") == "technical_writing_review")
    assert review["blocks_publish"] is False
    path = Path(review["artifact_path"])
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update({"decision": "block", "blocking_findings": ["editorial warning"]})
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert validator.validate_plan(plan, execution=True) == []


def test_execution_rejects_profile_content_mutation(tmp_path: Path):
    plan = execution_plan(tmp_path)
    Path(plan["profile_path"]).write_text('{"changed": true}', encoding="utf-8")
    assert any("profile content changed" in error for error in validator.validate_plan(plan, execution=True))


def test_execution_requires_command_success_evidence(tmp_path: Path):
    plan = execution_plan(tmp_path)
    command = next(task for task in plan["tasks"] if task["runner"] == "command")
    path = Path(command["artifact_path"])
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.pop("exit_code", None)
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert any("command success evidence" in error for error in validator.validate_plan(plan, execution=True))


def test_execution_accepts_task_specific_gate_decisions(tmp_path: Path):
    plan = execution_plan(tmp_path)
    decisions = {
        "scope-gate": "in_scope",
        "dedupe-and-disposition": "new",
        "publishability-gate": "publish_ready",
    }
    for suffix, decision in decisions.items():
        task = by_suffix(plan, suffix)
        path = Path(task["artifact_path"])
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["decision"] = decision
        path.write_text(json.dumps(payload), encoding="utf-8")
    assert validator.validate_plan(plan, execution=True) == []
