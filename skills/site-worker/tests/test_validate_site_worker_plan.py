from __future__ import annotations

import importlib.util
from pathlib import Path


VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_site_worker_plan.py"
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
    profile = {"event_id": "case-one", "event_name": "Case One", "attack_types": ["npm"]}
    profile_path = tmp_path / "profile.json"
    profile_path.write_text("{}", encoding="utf-8")
    return planner.make_tasks(profile_path, profile)


def test_validator_accepts_valid_modular_plan(tmp_path: Path):
    errors = validator.validate_plan(valid_plan(tmp_path))
    assert errors == []


def test_validator_rejects_missing_required_pipeline_task(tmp_path: Path):
    plan = valid_plan(tmp_path)
    plan["tasks"] = [
        task for task in plan["tasks"] if not task["task_id"].endswith("08-script-pack")
    ]
    errors = validator.validate_plan(plan)
    assert any("08-script-pack" in error for error in errors)


def test_validator_rejects_missing_agency_review(tmp_path: Path):
    plan = valid_plan(tmp_path)
    plan["tasks"] = [
        task for task in plan["tasks"] if task.get("review_lane") != "incident_response_review"
    ]
    errors = validator.validate_plan(plan)
    assert any("incident_response_review" in error for error in errors)


def test_validator_rejects_unknown_dependency(tmp_path: Path):
    plan = valid_plan(tmp_path)
    plan["tasks"][1]["depends_on"].append("missing-task")
    errors = validator.validate_plan(plan)
    assert any("unknown dependency" in error for error in errors)


def test_validator_rejects_legacy_canonical_target(tmp_path: Path):
    plan = valid_plan(tmp_path)
    plan["canonical_publication_target"] = "astro"
    errors = validator.validate_plan(plan)
    assert any("canonical_publication_target" in error for error in errors)


def test_validator_requires_run_ledger_schema_reference(tmp_path: Path):
    plan = valid_plan(tmp_path)
    plan.pop("run_ledger_schema", None)
    errors = validator.validate_plan(plan)
    assert any("run_ledger_schema" in error for error in errors)


def test_validator_rejects_missing_synthesis_task(tmp_path: Path):
    plan = valid_plan(tmp_path)
    plan["tasks"] = [
        task
        for task in plan["tasks"]
        if not task["task_id"].endswith("18-synthesis-conflict-resolution")
    ]
    errors = validator.validate_plan(plan)
    assert any("18-synthesis-conflict-resolution" in error for error in errors)


def test_validator_rejects_nonblocking_publishability_gate(tmp_path: Path):
    plan = valid_plan(tmp_path)
    gate = next(task for task in plan["tasks"] if task["task_id"].endswith("19-publishability-gate"))
    gate["blocks_publish"] = False
    errors = validator.validate_plan(plan)
    assert any("publishability-gate must block publish" in error for error in errors)
