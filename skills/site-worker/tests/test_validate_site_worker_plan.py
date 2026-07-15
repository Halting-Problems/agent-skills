from __future__ import annotations

import importlib.util
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_site_worker_plan.py"
MERGER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "merge_site_worker_outputs.py"
PLANNER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "site_worker_plan.py"

validator_spec = importlib.util.spec_from_file_location("validate_site_worker_plan", VALIDATOR_PATH)
assert validator_spec is not None and validator_spec.loader is not None
validator = importlib.util.module_from_spec(validator_spec)
validator_spec.loader.exec_module(validator)

planner_spec = importlib.util.spec_from_file_location("site_worker_plan", PLANNER_PATH)
assert planner_spec is not None and planner_spec.loader is not None
planner = importlib.util.module_from_spec(planner_spec)
planner_spec.loader.exec_module(planner)


def valid_plan(tmp_path: Path) -> dict:
    profile = {
        "event_id": "case-one",
        "event_name": "Case One",
        "attack_types": ["known exploited vulnerability"],
        "source_version_hash": "a" * 64,
        "source_version_at": "2026-07-11T00:00:00Z",
    }
    profile_path = tmp_path / "profile.json"
    profile_path.write_text("{}", encoding="utf-8")
    return planner.make_tasks(profile_path, profile, artifact_root=tmp_path / "artifacts")


def by_suffix(plan: dict, suffix: str) -> dict:
    return next(task for task in plan["tasks"] if task["task_id"].endswith(suffix))


def test_validator_accepts_valid_adaptive_plan(tmp_path: Path):
    assert validator.validate_plan(valid_plan(tmp_path)) == []


def test_validator_rejects_missing_executable_field(tmp_path: Path):
    plan = valid_plan(tmp_path)
    plan["tasks"][0].pop("runner")
    assert any("missing runner" in error for error in validator.validate_plan(plan))


def test_validator_rejects_unknown_dependency_and_cycle(tmp_path: Path):
    plan = valid_plan(tmp_path)
    plan["tasks"][1]["depends_on"].append("missing-task")
    assert any("unknown dependency" in error for error in validator.validate_plan(plan))

    cyclic = valid_plan(tmp_path)
    first = cyclic["tasks"][0]
    second = cyclic["tasks"][1]
    first["depends_on"] = [second["task_id"]]
    first["inputs"] = [second["artifact_path"]]
    errors = validator.validate_plan(cyclic)
    assert any("cycle" in error for error in errors)


def test_validator_rejects_dependency_after_consumer(tmp_path: Path):
    plan = valid_plan(tmp_path)
    plan["tasks"][0], plan["tasks"][1] = plan["tasks"][1], plan["tasks"][0]
    assert any("topological order" in error for error in validator.validate_plan(plan))


def test_validator_rejects_duplicate_artifacts_and_path_traversal(tmp_path: Path):
    plan = valid_plan(tmp_path)
    plan["tasks"][1]["artifact_path"] = plan["tasks"][0]["artifact_path"]
    assert any("duplicate artifact_path" in error for error in validator.validate_plan(plan))

    traversing = valid_plan(tmp_path)
    traversing["tasks"][0]["artifact_path"] = "../escape.json"
    assert any("path traversal" in error for error in validator.validate_plan(traversing))


def test_validator_rejects_missing_input_producer(tmp_path: Path):
    plan = valid_plan(tmp_path)
    plan["tasks"][3]["inputs"].append(str(tmp_path / "artifacts" / "unproduced.json"))
    assert any("missing input producer" in error for error in validator.validate_plan(plan))


def test_validator_requires_all_agency_reviews_and_synthesis_dependencies(tmp_path: Path):
    plan = valid_plan(tmp_path)
    removed = next(task for task in plan["tasks"] if task.get("review_lane") == "incident_response_review")
    plan["tasks"].remove(removed)
    errors = validator.validate_plan(plan)
    assert any("incident_response_review" in error for error in errors)

    plan = valid_plan(tmp_path)
    synthesis = by_suffix(plan, "synthesis-conflict-resolution")
    synthesis["depends_on"].pop()
    errors = validator.validate_plan(plan)
    assert any("missing agency review dependency" in error for error in errors)


def test_publish_gate_requires_import_and_production_verification(tmp_path: Path):
    plan = valid_plan(tmp_path)
    gate = by_suffix(plan, "publishability-gate")
    verification = by_suffix(plan, "production-verification")
    gate["depends_on"].remove(verification["task_id"])
    gate["inputs"].remove(verification["artifact_path"])
    errors = validator.validate_plan(plan)
    assert any("production verification" in error for error in errors)

    plan = valid_plan(tmp_path)
    gate = by_suffix(plan, "publishability-gate")
    gate["blocks_publish"] = False
    assert any("must block publish" in error for error in validator.validate_plan(plan))


def test_validator_rejects_legacy_publication_target_and_missing_ledger(tmp_path: Path):
    plan = valid_plan(tmp_path)
    plan["canonical_publication_target"] = "d1-primary"
    assert any("canonical_publication_target" in error for error in validator.validate_plan(plan))
    missing = deepcopy(valid_plan(tmp_path))
    missing.pop("run_ledger_schema")
    assert any("run_ledger_schema" in error for error in validator.validate_plan(missing))


def test_validator_handles_numeric_slug_segments(tmp_path: Path):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text("{}", encoding="utf-8")
    plan = planner.make_tasks(
        profile_path,
        {
            "event_id": "cve-2024-12-case",
            "attack_types": ["known exploited vulnerability"],
            "artifact_root": str(tmp_path / "artifacts"),
            "source_version_hash": "a" * 64,
            "source_version_at": "2026-07-11T00:00:00Z",
        },
        artifact_root=tmp_path / "artifacts",
    )
    assert validator.validate_plan(plan) == []


def test_validator_rejects_artifacts_outside_root_and_symlink_escapes(tmp_path: Path):
    plan = valid_plan(tmp_path)
    plan["tasks"][0]["artifact_path"] = str(tmp_path / "outside.json")
    assert any("outside artifact_root" in error for error in validator.validate_plan(plan))

    plan = valid_plan(tmp_path)
    root = Path(plan["artifact_root"])
    root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "escape").symlink_to(outside, target_is_directory=True)
    escaped = str(root / "escape" / "artifact.json")
    original = plan["tasks"][0]["artifact_path"]
    plan["tasks"][0]["artifact_path"] = escaped
    plan["tasks"][1]["inputs"] = [escaped if value == original else value for value in plan["tasks"][1]["inputs"]]
    assert any("outside artifact_root" in error for error in validator.validate_plan(plan))

    plan = valid_plan(tmp_path)
    root = Path(plan["artifact_root"])
    root.mkdir(parents=True, exist_ok=True)
    (root / "loop").symlink_to("loop")
    looped = str(root / "loop" / "artifact.json")
    original = plan["tasks"][0]["artifact_path"]
    plan["tasks"][0]["artifact_path"] = looped
    plan["tasks"][1]["inputs"] = [looped if value == original else value for value in plan["tasks"][1]["inputs"]]
    assert any("cannot resolve artifact_path" in error for error in validator.validate_plan(plan))


def test_validator_requires_command_argv_for_command_runners(tmp_path: Path):
    plan = valid_plan(tmp_path)
    command = next(task for task in plan["tasks"] if task["runner"] == "command")
    command.pop("command")
    assert any("command must be a non-empty argv list" in error for error in validator.validate_plan(plan))


def test_validator_reports_malformed_dependency_and_review_types(tmp_path: Path):
    plan = valid_plan(tmp_path)
    plan["tasks"][1]["depends_on"] = [[]]
    review = next(task for task in plan["tasks"] if task["runner"] == "agency_review")
    review["review_lane"] = []
    errors = validator.validate_plan(plan)
    assert any("dependency must be a task_id string" in error for error in errors)
    assert any("missing or invalid review_lane" in error for error in errors)


def test_validator_canonically_contains_agency_profiles(tmp_path: Path):
    plan = valid_plan(tmp_path)
    review = next(task for task in plan["tasks"] if task["runner"] == "agency_review")
    review["agent_profile_path"] = "/home/sam/agency-agents/../outside.md"
    assert any("invalid agent_profile_path" in error for error in validator.validate_plan(plan))


def test_validator_cli_reports_malformed_json_without_traceback(tmp_path: Path):
    plan_path = tmp_path / "malformed.json"
    plan_path.write_text("not-json", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(plan_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "invalid site-worker plan" in result.stderr


def test_merger_cli_reports_malformed_json_without_traceback(tmp_path: Path):
    plan_path = tmp_path / "malformed.json"
    output_path = tmp_path / "result.json"
    plan_path.write_text("not-json", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(MERGER_PATH),
            "--plan",
            str(plan_path),
            "--event-id",
            "case-one",
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "invalid site-worker plan" in result.stderr
