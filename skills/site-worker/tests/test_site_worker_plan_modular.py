from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "site_worker_plan.py"
spec = importlib.util.spec_from_file_location("site_worker_plan", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sample_profile() -> dict:
    return {
        "event_id": "example-npm-token-theft",
        "event_name": "Example npm Token Theft",
        "attack_types": ["npm package compromise", "credential theft", "github actions"],
        "affected_assets": {
            "ecosystems": ["npm"],
            "credentials_at_risk": ["npm token", "GitHub Actions OIDC"],
            "developer_tools": [],
        },
        "source_urls": ["https://research.example/report"],
    }


def task(plan: dict, task_id: str) -> dict:
    return next(item for item in plan["tasks"] if item["task_id"] == task_id)


def test_plan_emits_modular_chained_tasks_with_concrete_dependencies(tmp_path: Path):
    profile_path = tmp_path / "event.json"
    profile_path.write_text("{}", encoding="utf-8")

    plan = module.make_tasks(profile_path, sample_profile())

    task_ids = [item["task_id"] for item in plan["tasks"]]
    assert task_ids[:6] == [
        "example-npm-token-theft-01-scope-gate",
        "example-npm-token-theft-02-dedupe-and-disposition",
        "example-npm-token-theft-03-evidence-plan",
        "example-npm-token-theft-04-research-packet",
        "example-npm-token-theft-05-artifact-provenance",
        "example-npm-token-theft-06-soc-actionability",
    ]

    for item in plan["tasks"]:
        assert item["artifact_path"].startswith("~/hp-posts-info/example-npm-token-theft/")
        assert isinstance(item["acceptance_criteria"], list)
        assert item["acceptance_criteria"]
        for dependency in item["depends_on"]:
            assert dependency in task_ids


def test_plan_includes_agency_agent_review_lanes(tmp_path: Path):
    profile_path = tmp_path / "event.json"
    profile_path.write_text("{}", encoding="utf-8")

    plan = module.make_tasks(profile_path, sample_profile())

    reviews = [item for item in plan["tasks"] if item["task_type"] == "agency_review"]
    review_ids = {item["review_lane"] for item in reviews}
    assert {
        "architecture_review",
        "data_quality_review",
        "incident_response_review",
        "workflow_qa_review",
        "technical_writing_review",
    }.issubset(review_ids)
    assert all(item["agent_profile_path"].startswith("/home/sam/agency-agents/") for item in reviews)


def test_plan_has_publish_gate_and_canonical_postgres_validation(tmp_path: Path):
    profile_path = tmp_path / "event.json"
    profile_path.write_text("{}", encoding="utf-8")

    plan = module.make_tasks(profile_path, sample_profile())

    assert plan["canonical_publication_target"] == "nextjs-postgres"
    assert "astro" in plan["legacy_paths_disallowed"]
    assert "d1-primary" in plan["legacy_paths_disallowed"]
    publish_gate = task(plan, "example-npm-token-theft-19-publishability-gate")
    assert publish_gate["blocks_publish"] is True
    assert any("Postgres" in criterion for criterion in publish_gate["acceptance_criteria"])
