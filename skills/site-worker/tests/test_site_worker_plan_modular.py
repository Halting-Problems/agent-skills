from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "site_worker_plan.py"
spec = importlib.util.spec_from_file_location("site_worker_plan", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def profile(**overrides) -> dict:
    value = {
        "event_id": "example-event",
        "event_name": "Example Event",
        "attack_types": [],
        "affected_assets": {
            "ecosystems": [],
            "credentials_at_risk": [],
            "developer_tools": [],
        },
        "source_urls": ["https://example.test/advisory"],
        "source_version_hash": "a" * 64,
        "source_version_at": "2026-07-11T00:00:00Z",
    }
    value.update(overrides)
    return value


def suffixes(plan: dict) -> set[str]:
    values: set[str] = set()
    for task in plan["tasks"]:
        parts = task["task_id"].split("-")
        index = next(index for index, part in enumerate(parts) if len(part) == 2 and part.isdigit())
        values.add("-".join(parts[index + 1 :]))
    return values


def by_suffix(plan: dict, suffix: str) -> dict:
    return next(task for task in plan["tasks"] if task["task_id"].endswith(suffix))


def test_lightweight_kev_keeps_real_gates_without_package_ceremony(tmp_path: Path):
    profile_path = tmp_path / "event.json"
    profile_path.write_text("{}", encoding="utf-8")
    plan = module.make_tasks(
        profile_path,
        profile(attack_types=["known exploited vulnerability"], event_id="lightweight-kev"),
    )

    task_suffixes = suffixes(plan)
    for required in {
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
    }:
        assert required in task_suffixes
    assert {
        "registry-analysis",
        "artifact-diff",
        "provenance-audit",
        "endpoint-forensics",
        "credential-impact",
        "browser-exposure",
        "cloud-oidc-audit",
        "campaign-graph",
        "detection-pack",
        "script-pack",
    }.isdisjoint(task_suffixes)


def test_compromised_npm_adds_required_specialist_modules(tmp_path: Path):
    profile_path = tmp_path / "event.json"
    profile_path.write_text("{}", encoding="utf-8")
    compromised = profile(
        event_id="npm-compromise",
        attack_types=["npm package compromise", "credential theft"],
        affected_assets={
            "ecosystems": ["npm"],
            "credentials_at_risk": ["npm token"],
            "developer_tools": [],
        },
    )
    task_suffixes = suffixes(module.make_tasks(profile_path, compromised))
    assert {
        "registry-analysis",
        "artifact-diff",
        "provenance-audit",
        "endpoint-forensics",
        "credential-impact",
        "detection-pack",
        "script-pack",
    }.issubset(task_suffixes)
    assert "browser-exposure" not in task_suffixes


def test_optional_modules_follow_explicit_applicability_signals(tmp_path: Path):
    profile_path = tmp_path / "event.json"
    profile_path.write_text("{}", encoding="utf-8")
    rich = profile(
        attack_types=["browser CDN compromise", "GitHub Actions OIDC abuse"],
        is_campaign_level=True,
    )
    task_suffixes = suffixes(module.make_tasks(profile_path, rich))
    assert {"browser-exposure", "cloud-oidc-audit", "campaign-graph"}.issubset(task_suffixes)


def test_every_task_has_executable_fields_and_topological_inputs(tmp_path: Path):
    profile_path = tmp_path / "event.json"
    profile_path.write_text("{}", encoding="utf-8")
    plan = module.make_tasks(profile_path, profile(attack_types=["npm package compromise"]))
    seen: set[str] = set()
    artifacts: dict[str, str] = {}
    for task in plan["tasks"]:
        assert task["runner"] in {"halting_skill", "agency_review", "command", "gate"}
        assert isinstance(task["inputs"], list)
        assert "artifact_path" in task
        assert "artifact_schema" in task
        assert task["status"] == "pending"
        assert task["acceptance_criteria"]
        assert all(dependency in seen for dependency in task["depends_on"])
        produced_inputs = {artifacts[dependency] for dependency in task["depends_on"]}
        if task["depends_on"]:
            assert produced_inputs.issubset(set(task["inputs"]))
        seen.add(task["task_id"])
        artifacts[task["task_id"]] = task["artifact_path"]


def test_reviews_synthesis_import_verification_and_publish_dependency_remain(tmp_path: Path):
    profile_path = tmp_path / "event.json"
    profile_path.write_text("{}", encoding="utf-8")
    plan = module.make_tasks(profile_path, profile())
    reviews = [task for task in plan["tasks"] if task["runner"] == "agency_review"]
    assert {task["review_lane"] for task in reviews} == {
        "architecture_review",
        "data_quality_review",
        "incident_response_review",
        "workflow_qa_review",
        "technical_writing_review",
    }
    synthesis = by_suffix(plan, "synthesis-conflict-resolution")
    assert {task["task_id"] for task in reviews}.issubset(set(synthesis["depends_on"]))
    import_task = by_suffix(plan, "postgres-import")
    verification = by_suffix(plan, "production-verification")
    gate = by_suffix(plan, "publishability-gate")
    assert import_task["task_id"] in verification["depends_on"]
    assert {import_task["task_id"], verification["task_id"]}.issubset(set(gate["depends_on"]))
    assert gate["blocks_publish"] is True


def test_profile_cannot_override_artifact_root(tmp_path: Path):
    profile_path = tmp_path / "event.json"
    profile_path.write_text("{}", encoding="utf-8")
    untrusted = profile(artifact_root="/tmp/untrusted-output")
    plan = module.make_tasks(profile_path, untrusted)
    assert plan["artifact_root"] == str(Path("/home/sam/hp-posts-info/example-event").resolve())

    trusted_root = tmp_path / "trusted-output"
    overridden = module.make_tasks(profile_path, untrusted, artifact_root=trusted_root)
    assert overridden["artifact_root"] == str(trusted_root.resolve())


def test_import_plan_has_explicit_dry_run_and_execution(tmp_path: Path):
    profile_path = tmp_path / "event.json"
    profile_path.write_text("{}", encoding="utf-8")
    plan = module.make_tasks(profile_path, profile())
    dry_run = by_suffix(plan, "postgres-import-dry-run")
    import_task = by_suffix(plan, "postgres-import")
    assert "--dry-run" in dry_run["command"]
    assert "--dry-run" not in import_task["command"]
    assert dry_run["task_id"] in import_task["depends_on"]


def test_command_and_gate_tasks_use_runner_specific_schemas(tmp_path: Path):
    profile_path = tmp_path / "event.json"
    profile_path.write_text("{}", encoding="utf-8")
    plan = module.make_tasks(profile_path, profile())
    for task in plan["tasks"]:
        if task["runner"] == "command":
            assert task["artifact_schema"].endswith("site-worker-command-artifact.schema.json")
        if task["runner"] == "gate":
            assert task["artifact_schema"].endswith("site-worker-decision-artifact.schema.json")


def test_planner_preserves_candidate_source_binding(tmp_path: Path):
    profile_path = tmp_path / "event.json"
    profile_path.write_text("{}", encoding="utf-8")
    candidate_profile = profile(
        source_version_hash=None,
        source_version_at=None,
        sourceVersionHash="c" * 64,
        firstSeenAt="2026-06-23T00:00:00.000Z",
        sourceItemKey="cisa-kev:CVE-2026-34908",
    )
    plan = module.make_tasks(profile_path, candidate_profile)
    assert plan["source_version_hash"] == "c" * 64
    assert plan["source_version_at"] == "2026-06-23T00:00:00.000Z"
    assert plan["source_item_key"] == "cisa-kev:CVE-2026-34908"
