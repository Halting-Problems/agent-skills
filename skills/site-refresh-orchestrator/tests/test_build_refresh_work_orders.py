from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_refresh_work_orders.py"
spec = importlib.util.spec_from_file_location("build_refresh_work_orders", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_wrapper_targets_the_sibling_website_typed_planner():
    assert module.TS_CLI == (
        module.SKILLS_REPO_ROOT.parent
        / "haltingproblems.com"
        / "tooling"
        / "orchestration"
        / "disposition-candidates.ts"
    )


def test_wrapper_delegates_arguments_without_reimplementing_disposition(monkeypatch, tmp_path: Path):
    candidates = tmp_path / "candidates.json"
    output = tmp_path / "work-orders.json"
    captured = {}

    class Completed:
        returncode = 7

    def fake_run(command, *, cwd, check):
        captured.update(command=command, cwd=cwd, check=check)
        return Completed()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(MODULE_PATH),
            str(candidates),
            "--existing-index",
            str(tmp_path / "ignored.json"),
            "--update-slug",
            "existing-incident",
            "--out",
            str(output),
        ],
    )

    assert module.main() == 7
    assert captured == {
        "command": [
            "pnpm",
            "exec",
            "tsx",
            str(module.TS_CLI),
            str(candidates),
            "--work-orders",
            "--update-slug",
            "existing-incident",
            "--out",
            str(output),
        ],
        "cwd": module.WEBSITE_ROOT,
        "check": False,
    }
