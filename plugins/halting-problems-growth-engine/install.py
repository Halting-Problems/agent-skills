#!/usr/bin/env python3
"""Install the Halting Problems Growth Engine into Hermes, Codex, and Antigravity."""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import textwrap

ROOT = pathlib.Path(__file__).resolve().parent
HOME = pathlib.Path.home()
PLAYBOOK = (ROOT / "GROWTH_ENGINE.md").read_text(encoding="utf-8")

AGENTS = [
    {
        "slug": "growth-hacker",
        "name": "Growth Hacker",
        "source": "/home/sam/agency-agents/marketing/marketing-growth-hacker.md",
        "job": "Growth experiments, funnel hypotheses, acquisition loops, and weekly learning reviews.",
    },
    {
        "slug": "seo-specialist",
        "name": "SEO Specialist",
        "source": "/home/sam/agency-agents/marketing/marketing-seo-specialist.md",
        "job": "Technical SEO, topic clusters, structured data, search intent, and cannibalization checks.",
    },
    {
        "slug": "content-creator",
        "name": "Content Creator",
        "source": "/home/sam/agency-agents/marketing/marketing-content-creator.md",
        "job": "Repurpose articles into platform-specific narratives, briefs, and editorial calendars.",
    },
    {
        "slug": "social-media-strategist",
        "name": "Social Media Strategist",
        "source": "/home/sam/agency-agents/marketing/marketing-social-media-strategist.md",
        "job": "LinkedIn, X, Reddit/community, and professional-channel distribution strategy.",
    },
    {
        "slug": "email-marketing-strategist",
        "name": "Email Marketing Strategist",
        "source": "/home/sam/agency-agents/marketing/marketing-email-strategist.md",
        "job": "Subscriber segmentation, lifecycle flows, deliverability, and compliance gates.",
    },
    {
        "slug": "analytics-reporter",
        "name": "Analytics Reporter",
        "source": "/home/sam/agency-agents/support/support-analytics-reporter.md",
        "job": "Metrics snapshots, growth deltas, dashboards, and weekly reporting.",
    },
    {
        "slug": "engineering-devops-automator",
        "name": "DevOps Automator",
        "source": "/home/sam/agency-agents/engineering/engineering-devops-automator.md",
        "job": "Cron, deploy, workflow reliability, and automation guardrails.",
    },
    {
        "slug": "agentic-search-optimizer",
        "name": "Agentic Search Optimizer",
        "source": "/home/sam/agency-agents/marketing/marketing-agentic-search-optimizer.md",
        "job": "LLM/browser-agent discoverability and machine-readable site affordances.",
    },
]

COMMON_INSTRUCTIONS = f"""
# Halting Problems Growth Engine

You are the Halting Problems Growth Engine, a tailored orchestrator that uses selected Agency Agents to grow, scale, and market `/home/sam/halting-problems/repos/haltingproblems.com`.

## Source of truth

Use this canonical operating model:

{PLAYBOOK}

## Mandatory behavior

- Use Agency Agents as specialists, not generic marketing personas.
- Keep Halting Problems' canonical-post rule: follow-up developments update the existing canonical post rather than creating duplicate posts.
- Never invent metrics, rankings, subscriber counts, conversion numbers, or post URLs.
- No automatic posting, crossposting, emailing, ad spend, or deploys without explicit human approval.
- Preserve technical specificity and source-backed claims; do not convert operational threat intelligence into vague marketing copy.
- When data is missing, return `unknown` plus exact collection steps.
""".strip()

HERMES_PLUGIN = r'''
"""Hermes plugin: Halting Problems Growth Engine."""
from __future__ import annotations

import json
from typing import Any

AGENTS = __AGENTS_JSON__

BRIEF = """__BRIEF__"""

MODES = {
    "publish_amplification": {
        "purpose": "Turn a verified canonical article into approved channel-native distribution assets.",
        "agents": ["content-creator", "social-media-strategist", "seo-specialist", "growth-hacker"],
        "steps": [
            "Verify canonical article URL, /api/feed, and /api/search before drafting distribution.",
            "Extract exact article angle, affected ecosystem, key claims, and source-backed takeaway.",
            "Draft Reddit, LinkedIn, X/thread, and newsletter variants with approval gates.",
            "Define metrics: referral clicks, subscribers, discussion quality, and search impressions when available.",
        ],
    },
    "seo_backlog": {
        "purpose": "Create a search-focused backlog for technical SEO, topic clusters, structured data, and internal links.",
        "agents": ["seo-specialist", "content-creator", "marketing-agentic-search-optimizer", "analytics-reporter"],
        "steps": [
            "Audit crawl/index basics, sitemap, canonical URLs, title/meta/OG, and structured data opportunities.",
            "Map topic clusters around supply-chain compromise, malicious packages, CI/CD abuse, and developer tooling compromise.",
            "Identify internal links from related canonical posts without causing keyword cannibalization.",
            "Rank work by expected search/user value and verification effort.",
        ],
    },
    "subscriber_lifecycle": {
        "purpose": "Design consent-safe subscriber capture and lifecycle flows.",
        "agents": ["email-marketing-strategist", "content-creator", "analytics-reporter"],
        "steps": [
            "Inspect available subscriber fields and consent basis before proposing any send.",
            "Define segments, exclusions, exit conditions, unsubscribe handling, bounces, and complaints.",
            "Draft welcome/nurture/reactivation concepts only after sender authentication and compliance gates are explicit.",
            "Optimize for CTR, CTOR, and conversions rather than open rate alone.",
        ],
    },
    "weekly_growth_review": {
        "purpose": "Summarize shipped work, growth signals, blockers, and next experiments.",
        "agents": ["growth-hacker", "analytics-reporter", "seo-specialist", "engineering-devops-automator"],
        "steps": [
            "List posts shipped or updated this week and verification status.",
            "Report only observed metrics; mark missing analytics as unknown with collection steps.",
            "Review automation health for cron, deploys, imports, and syndication scripts.",
            "Choose the next three experiments with hypothesis, metric, owner, and stop condition.",
        ],
    },
    "full_growth_audit": {
        "purpose": "Review positioning, SEO, content, social, email, automation, and agentic discoverability.",
        "agents": [agent["slug"] for agent in AGENTS],
        "steps": [
            "Audit current repo/site state before recommendations.",
            "Create prioritized backlog across SEO, content, distribution, subscribers, analytics, and automation.",
            "Separate quick wins from credential/platform blockers.",
            "Return a 30-day execution roadmap with approval gates.",
        ],
    },
}


def _json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def register(ctx):
    def agents(args: dict[str, Any] | None = None, **kwargs: Any) -> str:
        del args, kwargs
        return _json({
            "success": True,
            "site": "/home/sam/halting-problems/repos/haltingproblems.com",
            "agency_router": "agency-agents-router",
            "agents": AGENTS,
            "usage": "Search/load/delegate these specialists lazily with agency-agents-router when deeper specialist context is needed.",
        })

    def brief(args: dict[str, Any] | None = None, **kwargs: Any) -> str:
        del args, kwargs
        return _json({"success": True, "brief": BRIEF})

    def plan(args: dict[str, Any] | None = None, **kwargs: Any) -> str:
        del kwargs
        args = args or {}
        mode = str(args.get("mode", "weekly_growth_review")).strip() or "weekly_growth_review"
        slug = str(args.get("slug", "")).strip()
        canonical_url = str(args.get("canonical_url", "")).strip()
        if mode not in MODES:
            return _json({"success": False, "error": f"unknown mode: {mode}", "available_modes": sorted(MODES)})
        mode_spec = MODES[mode]
        work_order = {
            "mode": mode,
            "site_repo": "/home/sam/halting-problems/repos/haltingproblems.com",
            "canonical_authoring_repo": "/home/sam/halting-problems/repos/hp-posts-info",
            "article_slug": slug,
            "canonical_url": canonical_url,
            "required_agents": mode_spec["agents"],
            "purpose": mode_spec["purpose"],
            "steps": mode_spec["steps"],
            "outputs": [
                "evidence-backed work order",
                "channel/native asset drafts when applicable",
                "metrics checklist with unknowns clearly marked",
                "approval gates before external side effects",
            ],
            "gates": [
                "explicit_human_approval",
                "verify_canonical_site_outputs",
                "no automatic posting",
                "no automatic emailing",
                "no invented metrics",
            ],
            "agency_router_instruction": "Use agency-agents-router to load/delegate only the required agent slugs for this mode.",
        }
        return _json({"success": True, "work_order": work_order})

    ctx.register_tool(
        name="hp_growth_engine_agents",
        toolset="hp_growth_engine",
        schema={"type": "object", "properties": {}},
        handler=agents,
        description="Return the Agency Agents selected for the Halting Problems Growth Engine and how to route them.",
    )
    ctx.register_tool(
        name="hp_growth_engine_brief",
        toolset="hp_growth_engine",
        schema={"type": "object", "properties": {}},
        handler=brief,
        description="Return the compact Halting Problems Growth Engine operating brief.",
    )
    ctx.register_tool(
        name="hp_growth_engine_plan",
        toolset="hp_growth_engine",
        schema={
            "type": "object",
            "properties": {
                "mode": {"type": "string", "description": "publish_amplification, seo_backlog, subscriber_lifecycle, weekly_growth_review, or full_growth_audit"},
                "slug": {"type": "string", "description": "Optional Halting Problems article slug."},
                "canonical_url": {"type": "string", "description": "Optional canonical article URL."},
            },
        },
        handler=plan,
        description="Create a structured growth/scaling/marketing work order for Halting Problems.",
    )
'''


def write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path}")


def toml_literal(value: str) -> str:
    return "'''" + value.replace("'''", "''\\''") + "'''"


def make_hermes_plugin() -> tuple[str, str]:
    manifest = """name: hp-growth-engine
version: 0.1.0
description: Halting Problems Growth Engine tools using selected Agency Agents.
provides_tools:
  - hp_growth_engine_agents
  - hp_growth_engine_brief
  - hp_growth_engine_plan
"""
    brief = "Use selected Agency Agents to create safe, approval-gated growth work orders for /home/sam/halting-problems/repos/haltingproblems.com. No automatic posting, emailing, ad spend, or deploys."
    plugin = HERMES_PLUGIN.replace("__AGENTS_JSON__", json.dumps(AGENTS, ensure_ascii=False, indent=4))
    plugin = plugin.replace("__BRIEF__", brief.replace('"""', '\"\"\"'))
    return manifest, plugin.lstrip()


def make_hermes_skill() -> str:
    return f"""---
name: halting-problems-growth-engine
description: Tailored Agency Agents growth, scaling, SEO, content, social, subscriber, and analytics workflow for Halting Problems.
version: 0.1.0
author: Hermes Agent + Agency Agents
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [haltingproblems, growth, marketing, seo, agency-agents, automation]
---

{COMMON_INSTRUCTIONS}

## Hermes-specific workflow

- Prefer `hp_growth_engine_plan` when the `hp-growth-engine` plugin is loaded.
- Use the existing `agency-agents-router` plugin to search/load/delegate selected specialists.
- Example router flow:
  1. `agency_agents_search` with a focused query such as `SEO technical audit for Halting Problems threat intel site`.
  2. `agency_agents_load` with `agent: seo-specialist` or another selected slug.
  3. `agency_agents_delegate` only for bounded review/research tasks.

## Common prompts

```text
Use the halting-problems-growth-engine skill to create a publish_amplification work order for <slug>.
```

```text
Use the halting-problems-growth-engine skill and agency-agents-router to run a full_growth_audit for /home/sam/halting-problems/repos/haltingproblems.com.
```
"""


def make_codex_agent() -> str:
    return "\n".join([
        'name = "Halting Problems Growth Engine"',
        'description = "Tailored Agency Agents orchestrator for growing, scaling, and marketing haltingproblems.com with approval-gated SEO, content, social, subscriber, analytics, and automation workflows."',
        f"developer_instructions = {toml_literal(COMMON_INSTRUCTIONS)}",
        "",
    ])


def make_antigravity_skill() -> str:
    return f"""---
name: halting-problems-growth-engine
description: Tailored Agency Agents growth, scaling, SEO, content, social, subscriber, and analytics workflow for Halting Problems.
risk: medium
source: local
date_added: '2026-07-05'
---

{COMMON_INSTRUCTIONS}

## Antigravity activation

```text
Use the halting-problems-growth-engine skill to create a weekly_growth_review for /home/sam/halting-problems/repos/haltingproblems.com.
```
"""


def enable_hermes_plugin() -> None:
    hermes = shutil.which("hermes")
    if not hermes:
        print("hermes CLI not found; plugin written but not enabled")
        return
    result = subprocess.run(
        [hermes, "plugins", "enable", "hp-growth-engine"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        print("warning: hermes plugin enable returned non-zero; files are still installed")


def main() -> int:
    manifest, plugin = make_hermes_plugin()
    write(HOME / ".hermes/plugins/hp-growth-engine/plugin.yaml", manifest)
    write(HOME / ".hermes/plugins/hp-growth-engine/__init__.py", plugin)
    write(HOME / ".hermes/skills/halting-problems-growth-engine/SKILL.md", make_hermes_skill())
    write(HOME / ".codex/agents/halting-problems-growth-engine.toml", make_codex_agent())
    write(HOME / ".gemini/antigravity/skills/halting-problems-growth-engine/SKILL.md", make_antigravity_skill())
    enable_hermes_plugin()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
