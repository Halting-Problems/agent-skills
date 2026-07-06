from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PLAN_PATH = ROOT / "skills/site-worker/examples/site_worker_plan.modular.example.json"
LEDGER_PATH = ROOT / "skills/site-worker/examples/modular-pipeline-run-ledger.example.json"


def test_example_plan_and_ledger_have_matching_task_ids():
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))

    plan_task_ids = {task["task_id"] for task in plan["tasks"]}
    ledger_task_ids = {task["task_id"] for task in ledger["task_results"]}

    assert ledger["canonical_publication_target"] == "nextjs-postgres"
    assert ledger_task_ids == plan_task_ids
    assert ledger["publish_decision"] in {
        "publish_ready",
        "needs_review",
        "reject",
        "update_existing",
        "attach_to_campaign",
        "duplicate",
    }
