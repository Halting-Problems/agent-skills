---
name: site-refresh-orchestrator
description: "Use when automatically refreshing the Halting Problems site from latest source-watcher findings: discover candidate supply-chain incidents, reject already-reported or duplicate sources, and spawn one deep site-worker subagent per new unreported source so the site is updated with detailed research, analysis, and useful Python handling scripts."
---

# Halting Problems Site Refresh Orchestrator

## Mission

Keep the Halting Problems site current with the latest credible supply-chain findings.

This skill coordinates `haltingproblems-source-watcher` and `site-worker`. It first builds a candidate queue from current sources, removes anything already reported or clearly duplicate, and routes follow-up evidence to the canonical existing post when the incident family is already covered. It then dispatches one independent `site-worker` task per survivor. If source-watcher finds five new unreported sources, spawn five independent site-worker subagents.

## Coverage scope gate

All discovery, dedupe, and publishing decisions are scoped to supply-chain attacks or supply-chain-adjacent security events. Survivors must have a clear relationship to repository compromise, package compromise, CI/CD abuse, developer tooling compromise, signed artifact compromise, registry abuse, provenance abuse, dependency confusion, malicious package distribution, maintainer/account takeover, browser/CDN supply-chain exposure, or content supply-chain compromise.

Do not promote generic CVE/KEV vulnerability items, generic KEV roundups, ransomware/vulnerability news, or vendor advisories unless the direct evidence ties the event to a software supply-chain or software-delivery compromise angle. Generic CVE/KEV items should be rejected or pruned under the coverage-scope policy, not sent to site-worker as refresh work.

---

## Inputs

- seed source list, watch pages, advisories, feeds, registries, GitHub URLs, or security blogs
- target Halting Problems site or repository path
- date window and topic scope
- optional existing post index, feed export, or Postgres-backed feed/API export
- optional concurrency limit

---

## Required Workflow

1. Load and follow `haltingproblems-source-watcher`.
2. Run source discovery for the requested date window and topic scope.
3. Build or read an existing-site index:
   - current post slugs
   - source URLs already cited by posts
   - event IDs, package names, advisories, repositories, CVEs, domains, hashes, or registry coordinates already covered
4. Dedupe candidates using stable `dedupe_keys`, exact source URLs, canonicalized URLs, and known post metadata.
5. Reject candidates based only on secondary or syndicated news unless they point to a direct or primary source that can be used.
6. For every remaining survivor candidate, either:
   - spawn a separate `site-worker` for a genuinely new incident, or
   - spawn a `site-worker` in `existing_post_upgrade` mode when a follow-up maps to a canonical post already on-site.
7. Require each site-worker to perform detailed, in-depth analysis, create useful, usable Python scripts inside `~/hp-posts-info/<slug>/`, and run validation checks.
8. Merge completed worker results into a site refresh summary with publish decisions, created/updated files, validation results, and blocking gaps.
9. When scheduled refreshes become too prompt-heavy or trigger provider guardrails, split the workflow into two cron jobs: a discovery/dedupe job that returns strict YAML locally, then a publisher job that consumes that output via `context_from` and returns `[SILENT]` when there are no survivor candidates.

Use `scripts/build_refresh_work_orders.py` when you have source-watcher JSON/YAML output and an index. The script emits one site-worker work order per unreported candidate. Prefer primary feeds and advisories first (for example CISA KEV JSON, vendor RSS, and researcher RSS), then dedupe against canonical Postgres-backed Next.js feed/API exports and known source URLs.

Session-derived pitfalls and indexing notes live in:
- [references/refresh-dedupe-indexing.md](references/refresh-dedupe-indexing.md) — build the index from canonical Postgres-backed feed/API data when available, normalize URLs before comparing, and treat zero survivors as a valid “already covered” result instead of synthesizing workers.
- [references/ioc-validation-pitfall.md](references/ioc-validation-pitfall.md) — bare IP/domain IOC coverage requirements for hunt strings.
- [references/cron-split-pattern.md](references/cron-split-pattern.md) — split guarded cron refreshes into discovery and publisher jobs chained with `context_from`, with `[SILENT]` on empty survivor sets.
- [references/supply-chain-scope-gate.md](references/supply-chain-scope-gate.md) — durable scope gate and cron prompt pattern for keeping refreshes focused on supply-chain attacks and supply-chain-adjacent security events.

When a window yields only already-reported items, return a clean deduped summary rather than forcing a worker dispatch.

---

## Site-Worker Subagent Prompt

Use this prompt shape for each new candidate. Fill the candidate fields exactly from source-watcher output.

```text
Use the Halting Problems site-worker skill for one candidate source only.

Candidate:
- candidate_id: {candidate_id}
- title: {title}
- first_seen: {first_seen}
- source_urls: {source_urls}
- dedupe_keys: {dedupe_keys}
- ecosystem: {ecosystem}
- affected_assets: {affected_assets}
- reason: {reason}
- collection_gaps: {collection_gaps}

Objective:
Perform a detailed, in-depth Halting Problems analysis for this candidate and decide whether it should become a new post, update an existing post, attach to a campaign, or be rejected. If it is publishable, create or update the site content and all supporting artifacts needed for a defensible article.

Ecosystem & Storage resolution:
- Create folder `~/hp-posts-info/{candidate_id}/` for all script, mock, and test assets.
- Save the hunt manifest in `~/hp-posts-info/{candidate_id}/manifest.yaml`.
- Save the machine-readable IOC profile in `~/hp-posts-info/{candidate_id}/iocs.json`.

Modular planning requirements:
- Generate `~/hp-posts-info/{candidate_id}/site-worker-plan.json` with `skills/site-worker/scripts/site_worker_plan.py`.
- Validate it with `skills/site-worker/scripts/validate_site_worker_plan.py`.
- Dispatch required agency-agent review lanes from `/home/sam/agency-agents`.
- Answer the critique questions in `skills/site-worker/references/agent-pipeline-critique-questions.md`.
- Require agency-agent review lanes for architecture, data quality/remediation, incident-response usability, workflow QA, and technical documentation before publishability.
- Treat Next.js/Postgres as canonical and do not publish based on Astro/D1/static fallback data.

Depth requirements:
- Prefer direct sources, primary research, registry metadata, repository history, package/release artifacts, advisories, and original researcher posts.
- Build a claim ledger that ties assertion to evidence. Require source attribution for every behavioral claim.
- Distinguish observed behavior from inference.
- Verify package, container, GitHub Action, extension, release, tag, provenance, and builder facts where applicable.
- Preserve uncertainty. Use unknown or not_observed instead of inventing versions, hashes, victims, timelines, or attribution.
- Include detailed downstream impact analysis for credentials, CI/CD, cloud, developer endpoints, browsers/CDNs, and registries when applicable.
- Require an applicability decision before adding endpoint, registry, GitHub, browser, CI/CD, or cloud modules.

Remediation & Advice requirements:
- Require rationale for every recommendation. Do not write generic "rotate everything" checklist templates. Remediations must be prose-driven and specifically reference the packages, registry hooks, or directories defined in the finding.

Python script requirements:
- Create useful, usable Python scripts inside `~/hp-posts-info/{candidate_id}/scripts/` whenever the incident can be audited, hunted, or remediated.
- Require exactly one reviewed hunt manifest in the research repository per script.
- Scripts must be complete and runnable, not placeholders or pseudocode.
- Embed incident-specific constants that are known from evidence, such as package names, versions, domains, hashes, registry paths, repository names, action refs, advisory IDs, and relevant timestamps.
- Include unit tests in `~/hp-posts-info/{candidate_id}/tests/` and mock telemetry fixtures under `~/hp-posts-info/{candidate_id}/fixtures/` to verify scripts run successfully on clean/dirty states.
- Do not leave placeholders such as OWNER/REPO, RUN_ID, PACKAGE, START_DATE, REPLACE_WITH_*, or bracketed TODO values in final article scripts.

Safety & Sandbox constraints:
- Do NOT run, execute, or install downloaded untrusted code under any circumstances (never use npm install, node, bun, or python execution on untrusted packages). Inspect only via safe, static methods.
- To avoid triggering API safety filters, never print raw text containing potentially sensitive or safety-triggering content (such as exploit instructions or bioweapon words) in the terminal output. Use helper python scripts to inspect locally and print only redacted/defanged summaries or metadata.
- Always write, download, extract, or copy untrusted package tarballs, extensions, or files being analyzed directly to the corresponding post directory in the sibling research repository (`~/hp-posts-info/{candidate_id}/`). Never download, write, or extract them to locations outside this repository (such as `/tmp/`, `/home/sam/`, or the website root).

Validation:
- Run the site-worker validation checklist.
- Confirm sourceCount matches numbered sources.
- Confirm final post prose defangs network IOCs outside machine-readable blocks.
- Run `python skills/site-worker/scripts/site_worker_plan.py <event_profile.json> --output ~/hp-posts-info/{candidate_id}/site-worker-plan.json` and validate the result with `python skills/site-worker/scripts/validate_site_worker_plan.py ~/hp-posts-info/{candidate_id}/site-worker-plan.json` before drafting or publishing.
- Run `hp-posts-info` tests for the slug, then run the website Postgres importer dry-run and import against the intended database.
- Run `pnpm check`, `pnpm test`, and `pnpm build` in the website repository before calling the refresh publish-ready.
- Verify `/threat/{candidate_id}`, `/api/feed`, and relevant search/API responses read the expected facts, IOCs, sources, and scripts from Postgres.
- Treat `pnpm run validate:content`, Astro content, D1 sync, and static fallback files as legacy compatibility checks only, not as the canonical publication gate.

Return:
- site_worker_result YAML
- created or updated files across both repositories
- script paths and how each script helps defenders
- validation results
- blocking gaps and exact next collection steps if not publish-ready
```

---

## Output Contract

```yaml
site_refresh_result:
  date_window: ""
  source_watcher_run: ""
  total_candidates: 0
  already_reported: []
  rejected_candidates: []
  new_unreported_candidates: []
  spawned_site_workers:
    - task_id: ""
      candidate_id: ""
      title: ""
      source_urls: []
      prompt_file: ""
      status: "queued|running|complete|failed"
  completed_artifacts: []
  validation_results: []
  blocking_gaps: []
  recommended_next_action: ""
```

---

## Rules

- Spawn one site-worker per new unreported candidate. Do not batch unrelated incidents into a single worker.
- Run independent site-worker tasks concurrently when the environment supports subagents and the candidates do not depend on one another.
- Keep syndicated-only items in `rejected_candidates` or `blocking_gaps` unless a direct source is located.
- Reject secondary-analysis or follow-up blog posts that point to an already-covered incident family when the dedupe keys, package/artifact identity, or primary-source lineage map to an existing post, unless the new evidence materially upgrades that canonical post. In that case, route the candidate to `existing_post_upgrade` mode for the original post instead of creating a follow-up article.
- Do not declare the site fully updated unless all new unreported candidates have a worker result or a documented rejection reason.
- Do not publish shallow summaries. The goal is deep research with operationally useful handling scripts.
- If a refresh run produces no publishable survivors, avoid metadata-only churn: do not make an empty commit, and revert regenerated index artifacts such as `site-index.json` if they were produced only for local dedupe verification.
- If subagents are unavailable, process the work orders sequentially and label each candidate result separately.
