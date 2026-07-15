# Halting Problems Growth Engine Pack

Tailored global agent/plugin pack for using `/home/sam/agency-agents` to grow, scale, and market `/home/sam/halting-problems/repos/haltingproblems.com` across Hermes, Codex, and Antigravity.

## What this installs

| Tool | Installed artifact |
|---|---|
| Hermes plugin | `~/.hermes/plugins/hp-growth-engine/` |
| Hermes skill | `~/.hermes/skills/halting-problems-growth-engine/SKILL.md` |
| Codex custom agent | `~/.codex/agents/halting-problems-growth-engine.toml` |
| Antigravity skill | `~/.gemini/antigravity/skills/halting-problems-growth-engine/SKILL.md` |

## Source agents

The pack wraps selected Agency Agents rather than copying the whole roster into every prompt:

- `growth-hacker`
- `seo-specialist`
- `content-creator`
- `social-media-strategist`
- `email-marketing-strategist`
- `analytics-reporter`
- `engineering-devops-automator`
- `marketing-agentic-search-optimizer`

Canonical operating model: [`GROWTH_ENGINE.md`](GROWTH_ENGINE.md).

## Install

```bash
cd /home/sam/halting-problems/repos/haltingproblems.com
python agent-plugins/halting-problems-growth-engine/install.py
```

The installer is idempotent and only writes the Growth Engine artifacts listed above.

## Validate

```bash
python agent-plugins/halting-problems-growth-engine/tests/validate_growth_engine_pack.py
```

## Hermes usage

After a Hermes restart or new session, use:

```text
Use the halting-problems-growth-engine skill to create a publish_amplification work order for <slug>.
```

If the plugin is loaded, Hermes can call:

- `hp_growth_engine_agents`
- `hp_growth_engine_brief`
- `hp_growth_engine_plan`

The Hermes pack is designed to cooperate with the already-enabled `agency-agents-router` plugin. Use the router to search/load/delegate the selected Agency Agents lazily.

## Codex usage

```text
Use the Halting Problems Growth Engine agent to run a full_growth_audit for /home/sam/halting-problems/repos/haltingproblems.com.
```

## Antigravity usage

```text
Use the halting-problems-growth-engine skill to create a weekly_growth_review.
```

## Safety

This pack intentionally does **not** auto-post, auto-email, buy ads, or deploy changes. It creates work orders, drafts, and review gates. Any external marketing action requires explicit human approval plus relevant credentials/configuration.
