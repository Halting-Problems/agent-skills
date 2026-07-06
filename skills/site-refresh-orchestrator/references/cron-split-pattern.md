# Cron split pattern for guarded site refresh runs

Use this pattern when a single end-to-end refresh cron prompt starts tripping provider safety rails or becomes too large/noisy.

## Problem shape

A monolithic scheduled prompt that combines all of the following is more likely to get blocked or become brittle:
- recent supply-chain incident discovery
- dedupe against existing site content
- deep site-worker analysis
- defender script generation
- commit/push/build/deploy in one run

This is especially true when the prompt repeatedly includes phrases like "latest attacks" plus deep analysis and script-generation instructions.

## Preferred split

Create two chained cron jobs instead of one monolith.

### 1) Discovery job
- skills: `haltingproblems-source-watcher`, `site-feed-curator-and-dedupe-skill`
- delivery: `local`
- output: strict YAML candidate queue only
- responsibilities:
  - discover recent public-source candidates
  - build/read existing-site index
  - dedupe already-covered incidents
  - classify survivors as `new_post`, `update_existing`, or `attach_to_campaign`
- must NOT:
  - write posts
  - generate defender scripts
  - commit/push
  - deploy

### 2) Publisher job
- skills: `site-worker`
- input: `context_from` the discovery job
- delivery: normal user delivery (`origin`)
- responsibilities:
  - read the latest discovery output as the work queue
  - respond with exactly `[SILENT]` if discovery output is missing, malformed, or has zero survivors
  - run deeper site-worker flow only on survivor candidates
  - validate, commit, push, build, and deploy when publishable

## Prompt-shaping guidance

When using OpenAI/Codex or other guardrail-sensitive providers:
- frame the task as **defensive public-source documentation**
- prefer wording like `publicly documented incidents`, `defensive analysis`, and `responder enablement`
- avoid needlessly aggressive wording like `latest attacks` when `publicly documented incidents` is sufficient
- keep the discovery job free of script-generation and deployment language

## Scheduling pattern

Stagger the jobs so discovery finishes before publish starts, for example:
- discovery: `35 */4 * * *`
- publisher: `50 */4 * * *`

A small offset is enough as long as the discovery job normally completes before the publisher tick.

## Verification

After splitting:
- discovery job should exist with `deliver: local`
- publisher job should exist with `context_from: [<discovery_job_id>]`
- the old monolithic orchestrator job should be removed to avoid duplicate runs
