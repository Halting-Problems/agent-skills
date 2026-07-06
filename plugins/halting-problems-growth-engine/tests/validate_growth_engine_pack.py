#!/usr/bin/env python3
"""Validate the Halting Problems Growth Engine global agent/plugin pack."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import pathlib
import sys
import tomllib
from collections.abc import Callable
from typing import Any, cast

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOME = pathlib.Path.home()

REQUIRED_AGENTS = [
    "growth-hacker",
    "seo-specialist",
    "content-creator",
    "social-media-strategist",
    "email-marketing-strategist",
    "analytics-reporter",
    "engineering-devops-automator",
    "agentic-search-optimizer",
]

SOURCE_FILES = [
    ROOT / "README.md",
    ROOT / "GROWTH_ENGINE.md",
    ROOT / "install.py",
]

INSTALLED_FILES = {
    "hermes_plugin_yaml": HOME / ".hermes/plugins/hp-growth-engine/plugin.yaml",
    "hermes_plugin_py": HOME / ".hermes/plugins/hp-growth-engine/__init__.py",
    "hermes_skill": HOME / ".hermes/skills/halting-problems-growth-engine/SKILL.md",
    "codex_agent": HOME / ".codex/agents/halting-problems-growth-engine.toml",
    "antigravity_skill": HOME / ".gemini/antigravity/skills/halting-problems-growth-engine/SKILL.md",
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(path: pathlib.Path) -> str:
    assert_true(path.exists(), f"missing file: {path}")
    return path.read_text(encoding="utf-8")


class FakeCtx:
    def __init__(self) -> None:
        self.tools: dict[str, Callable[[dict[str, Any]], str]] = {}

    def register_tool(self, *, name: str, handler: Callable[[dict[str, Any]], str], **kwargs: Any) -> None:
        self.tools[name] = handler


def validate_source_pack() -> None:
    for path in SOURCE_FILES:
        text = read(path)
        assert_true("Halting Problems" in text, f"{path} does not mention Halting Problems")

    playbook = read(ROOT / "GROWTH_ENGINE.md")
    for agent in REQUIRED_AGENTS:
        assert_true(agent in playbook, f"GROWTH_ENGINE.md missing {agent}")
    assert_true("~/haltingproblems.com" in playbook, "playbook missing site path")
    assert_true("no automatic posting" in playbook.lower(), "playbook missing posting safety rule")


def validate_hermes_plugin() -> None:
    yaml_text = read(INSTALLED_FILES["hermes_plugin_yaml"])
    assert_true("name: hp-growth-engine" in yaml_text, "Hermes plugin manifest has wrong name")
    for tool in ["hp_growth_engine_plan", "hp_growth_engine_agents", "hp_growth_engine_brief"]:
        assert_true(tool in yaml_text, f"Hermes manifest missing {tool}")

    plugin_path = INSTALLED_FILES["hermes_plugin_py"]
    read(plugin_path)
    spec = importlib.util.spec_from_file_location("hp_growth_engine_plugin", plugin_path)
    assert_true(spec is not None and spec.loader is not None, "could not load plugin spec")
    checked_spec = cast(importlib.machinery.ModuleSpec, spec)
    loader = checked_spec.loader
    if loader is None:
        raise AssertionError("could not load plugin loader")
    module = importlib.util.module_from_spec(checked_spec)
    loader.exec_module(module)
    ctx = FakeCtx()
    module.register(ctx)
    for tool in ["hp_growth_engine_plan", "hp_growth_engine_agents", "hp_growth_engine_brief"]:
        assert_true(tool in ctx.tools, f"registered tools missing {tool}")

    agents_payload = json.loads(ctx.tools["hp_growth_engine_agents"]({}))
    assert_true(agents_payload["success"] is True, "agents tool failed")
    slugs = {item["slug"] for item in agents_payload["agents"]}
    for agent in REQUIRED_AGENTS:
        assert_true(agent in slugs, f"agents tool missing {agent}")

    plan_payload = json.loads(ctx.tools["hp_growth_engine_plan"]({"mode": "publish_amplification", "slug": "example-threat"}))
    assert_true(plan_payload["success"] is True, "plan tool failed")
    assert_true(plan_payload["work_order"]["mode"] == "publish_amplification", "wrong work order mode")
    assert_true("explicit_human_approval" in plan_payload["work_order"]["gates"], "missing approval gate")


def validate_hermes_skill() -> None:
    text = read(INSTALLED_FILES["hermes_skill"])
    assert_true("name: halting-problems-growth-engine" in text, "Hermes skill frontmatter wrong")
    for needle in ["agency-agents-router", "~/haltingproblems.com", "Growth Hacker", "SEO Specialist"]:
        assert_true(needle in text, f"Hermes skill missing {needle}")


def validate_codex_agent() -> None:
    text = read(INSTALLED_FILES["codex_agent"])
    data = tomllib.loads(text)
    assert_true(data["name"] == "Halting Problems Growth Engine", "Codex agent has wrong name")
    assert_true("developer_instructions" in data, "Codex agent missing developer_instructions")
    for agent in REQUIRED_AGENTS:
        assert_true(agent in data["developer_instructions"], f"Codex instructions missing {agent}")


def validate_antigravity_skill() -> None:
    text = read(INSTALLED_FILES["antigravity_skill"])
    assert_true(text.startswith("---\n"), "Antigravity skill missing frontmatter")
    assert_true("name: halting-problems-growth-engine" in text, "Antigravity skill wrong name")
    assert_true("risk: medium" in text, "Antigravity skill missing risk")
    for agent in REQUIRED_AGENTS:
        assert_true(agent in text, f"Antigravity skill missing {agent}")


def main() -> int:
    checks = [
        validate_source_pack,
        validate_hermes_plugin,
        validate_hermes_skill,
        validate_codex_agent,
        validate_antigravity_skill,
    ]
    failures: list[str] = []
    for check in checks:
        try:
            check()
            print(f"PASS {check.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"FAIL {check.__name__}: {exc}")
            print(failures[-1])
    if failures:
        print(f"\n{len(failures)} validation failure(s)")
        return 1
    print("\nAll Halting Problems Growth Engine pack checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
