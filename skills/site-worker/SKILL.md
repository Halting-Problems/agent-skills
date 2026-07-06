---
name: site-worker
description: Use when operating the Halting Problems threat-intel site pipeline end-to-end, coordinating researcher/writer/enrichment/detection/provenance/cloud/artifact skills, planning specialized subagent work, migrating posts, or preparing publish-ready threat analyses.
---

# Halting Problems Site Worker

## Purpose

`site-worker` is the orchestrator for the Halting Problems threat-intel workflow. It does not replace specialist skills. It coordinates them, assigns bounded tasks, merges outputs, validates contracts, and decides whether work should become a new post, update an existing post, attach to a campaign, or stop for human review.

It coordinates research, planning, testing, formatting, and Postgres-backed publishing across two repositories: `haltingproblems.com` (for the Next.js app, Postgres importer, CTI schema, pages, and APIs) and `hp-posts-info` (for canonical analysis prose, IOCs, hunt scripts, manifests, tests, and fixtures).

The site-worker should produce operationally useful output: evidence-backed research packets, artifact verification, enrichment recipes, detection packs, downstream credential audits, remediation plans, publish-ready posts, and machine-readable event profiles.

## Core Rule

Never let the pipeline collapse technical detail into decorative prose. If a specialist produces commands, queries, audit recipes, detection logic, or remediation gates, preserve that detail.

When reporting Halting Problems work back to Sam, use plain human wording. Avoid repeatedly saying “canonical”; say “main post,” “source of truth,” “Postgres-backed,” or omit the concept unless it is technically necessary.

Handling output must be complete scripts, not script-shaped placeholders. Reject final posts that contain placeholder incident values such as `OWNER/REPO`, `RUN_ID`, `PACKAGE`, `START_DATE`, `REPLACE_WITH_*`, or bracket placeholders in Detection and Hunting or Downstream Abuse Audits.

All hunter and collector scripts must be written to the sibling repository `~/hp-posts-info/<slug>/scripts/`, described by `~/hp-posts-info/<slug>/manifest.yaml`, paired with `analysis.md` or `analysis.mdx`, and verified with unit tests and mock telemetry fixtures under `~/hp-posts-info/<slug>/tests/` and `fixtures/` before Postgres import.

## Canonical Pipeline Rule

The canonical publication pipeline is Next.js/Postgres. Astro content, D1, and static fallback data are legacy compatibility paths and must not be treated as the source of truth for new pipeline outputs.

For each event, generate and validate a modular task graph:

```bash
python skills/site-worker/scripts/site_worker_plan.py <event_profile.json> --output ~/hp-posts-info/<slug>/site-worker-plan.json
python skills/site-worker/scripts/validate_site_worker_plan.py ~/hp-posts-info/<slug>/site-worker-plan.json
```

The task graph must include:

- Scope gate.
- Dedupe/disposition gate.
- Evidence plan.
- Research packet.
- Artifact/provenance verification.
- SOC/actionability review.
- IOC/package normalization.
- Script pack with fixtures and tests.
- Downstream impact/remediation review.
- Detection pack.
- Draft, schema normalization, agency-agent reviews, synthesis, and publishability gate.

Use `references/agent-pipeline-critique-questions.md` for final critique. Use `references/agency-agent-review-lanes.md` for required `/home/sam/agency-agents` review lanes.

## Script Lifecycle Contract

Treat `hp-posts-info` as the source of truth for executable hunt content.

1. Store each incident's scripts, manifest, fixtures, tests, and IOC support files under `~/hp-posts-info/<slug>/`.
2. Ensure each `manifest.yaml` hunt has a stable `id`, incident-specific metadata, and a `script_path` pointing to the tested script under that slug.
3. Test scripts in `hp-posts-info` with the repo's pytest suite or the focused slug tests before importing.
4. From `haltingproblems.com`, run `pnpm exec tsx scripts/import-posts-info-to-postgres.ts --posts-info-dir ../hp-posts-info --dry-run`; the importer must prove structured data, prose, manifests, and script paths are valid.
5. Import to Postgres only from a checkout that has the sibling `~/hp-posts-info` repository present and the intended database configured.
6. After import, verify `/threat/<slug>`, `/api/feed`, and `/api/search?q=<known-term>` read the expected prose, facts, IOCs, and script rows from Postgres.

Never treat Markdown code blocks, `scripts/threat-posts/`, generated frontend output, or frontend fixtures as the canonical source. Those are legacy or compatibility surfaces; tested `hp-posts-info` folders imported into Postgres are what the Next.js app must serve.

## When To Use

Use for:

- Running a candidate supply-chain incident through the full Halting Problems pipeline.
- Creating or updating `hp-posts-info/<slug>/` post folders.
- Reviewing existing posts for schema drift, shallow detections, weak citations, or missing actionability.
- Coordinating multiple specialist skills or subagents.
- Building campaign-level updates from several child events.
- Generating detection packs, IOC exports, or credential-rotation plans attached to posts.
- Deciding whether a finding is a new post, an update, campaign child, duplicate, or reject.

Do not use for:

- Pure vulnerability advisories with no supply-chain compromise, artifact tampering, registry abuse, CI/CD abuse, developer tooling compromise, signed artifact compromise, or content supply-chain angle. Generic CVE/KEV posts and KEV roundup posts should be pruned from Halting Problems rather than refreshed.
- Publishing claims from syndicated news alone.
- Attribution claims not supported by the research packet and attribution rubric.

For site-wide scope pruning, use the tested coverage-scope pattern in [references/coverage-scope-policy.md](references/coverage-scope-policy.md): CVE/KEV content must carry explicit supply-chain exception tags or be removed from `src/content/`.

## Specialist Skill Roster

Use these skills as subagents when available. If the environment does not support subagents, emulate the flow sequentially and label each specialist output clearly.

| Order | Skill | Job |
| --- | --- | --- |
| 1 | `source-watcher` | Discover candidate incidents and source URLs. |
| 2 | `site-feed-curator-and-dedupe-skill` | Decide new post, update, campaign child, duplicate, or reject. |
| 3 | `supply-chain-compromise-researcher` | Build the evidence-backed research packet and claim ledger. |
| 4 | `supply-chain-artifact-diff-lab` | Verify package/container/action/extension artifact differences. |
| 5 | `provenance-and-publishing-integrity-auditor` | Verify tag, release, source, signing, provenance, and builder integrity. |
| 6 | `campaign-clustering-and-event-graph-builder` | Link or separate incidents using hard correlation rules. |
| 7 | `soc-ir-enrichment-engineer` | Convert recommendations into audit recipes with commands/queries, exit code specs, and mock fixtures. |
| 8 | `cloud-oidc-and-ci-cd-abuse-hunter` | Add deep GitHub/cloud/OIDC downstream abuse audits. |
| 9 | `browser-side-supply-chain-exposure-analyst` | Add frontend/CDN/browser exposure workflow when applicable. |
| 10 | `developer-endpoint-forensics-runbooker` | Add workstation and IDE extension triage when applicable. |
| 11 | `detection-pack-generator` | Produce KQL, SPL, Sigma, YARA, osquery, shell, and cloud queries. |
| 12 | `ioc-normalizer-and-sharing-exporter` | Normalize indicators and produce CSV/STIX/MISP-lite exports. |
| 13 | `remediation-and-credential-rotation-planner` | Generate credential-specific rotation and recovery plans. |
| 14 | `supply-chain-compromise-technical-writer` | Produce the final Halting Problems post, dynamically loading and compiling the tested scripts from the sibling research repository. |
| 15 | `post-schema-normalizer-and-migrator` | Normalize frontmatter, JSON profile, defanging, and old-format posts. |
| 16 | `site-worker` | Merge, validate, decide, and produce the final work order. |

## Work Modes

### Mode A: New Incident Post

Use when a candidate event may become a new threat post.

Pipeline:

1. Candidate intake.
2. Dedupe and campaign relationship decision.
3. Research packet.
4. Artifact diff and provenance checks.
5. Campaign graph update, if relevant.
6. SOC/IR enrichment (write scripts, manifests, fixtures, and mock tests to `~/hp-posts-info/<slug>/`).
7. Cloud/OIDC, browser, endpoint, registry, or deployment modules as applicable.
8. Detection pack and IOC exports.
9. Remediation plan.
10. Technical writer post.
11. Run `hp-posts-info` pytest and website importer dry-run validation.
12. Run the Postgres import from the website repo only after confirming `~/hp-posts-info` is present and the target database is configured.
13. Verify `/threat/<slug>`, `/api/feed`, and `/api/search` return the tested manifest hunts and imported CTI data.
14. Schema normalization and contract validation.
15. Final publish/readiness decision.

### Mode B: Existing Post Upgrade

Use when improving old posts on haltingproblems.com.

Pipeline:

1. Extract current post frontmatter, markdown sections, sources, and JSON profile.
2. Scaffold target folder `~/hp-posts-info/<slug>/` and move existing scripts there.
3. Run schema normalizer.
4. Run actionability review.
5. Add missing hunt recipes, downstream audits, remediation gates, and source mapping.
6. Verify scripts pass syntax/mock checks in `hp-posts-info`.
7. Run importer dry-run, then import so updated `manifest.yaml`, script bodies, IOCs, and analysis sections populate Postgres.
8. Validate post contract and Next.js page/API availability.

### Mode C: Campaign Update

Use when several events share hard indicators or a direct source defines a campaign.

Pipeline:

1. Collect child event profiles.
2. Build campaign graph.
3. Validate cluster evidence.
4. Update parent campaign post and child `parent_campaign_id` fields.
5. Do not merge incidents based only on ecosystem, dates, or generic malware behavior.

### Mode D: Detection Pack Only

Use when the user wants defender-ready detections without a full article.

Pipeline:

1. Ingest event profile or post.
2. Extract behaviors and IOCs.
3. Generate detection pack.
4. Validate queries include telemetry, fields, positive signals, false positives, and escalation.

### Mode E: Site-Wide Audit

Use when reviewing many posts.

Pipeline:

1. Crawl or inspect posts.
2. Validate frontmatter and source counts.
3. Detect old machine-readable profile formats.
4. Identify posts missing actionability sections.
5. Produce a prioritized migration backlog.

## Subagent Spawning Protocol

When subagents are supported, spawn each specialist with a narrow task contract:

```yaml
subagent_task:
  task_id: "unique-id"
  specialist: "skill-name"
  objective: "one precise outcome"
  inputs:
    event_profile: "path or inline JSON"
    research_packet: "path or inline markdown"
    source_urls: []
    artifacts: []
  constraints:
    - "Use only supplied sources unless explicitly allowed to research."
    - "Do not invent package versions, timestamps, hashes, or victim counts."
    - "Return unknown when evidence is missing."
  required_output:
    format: "markdown|yaml|json"
    sections: []
  validation:
    scripts: []
```

Run independent tasks concurrently only when their inputs do not depend on one another. Artifact diff, provenance audit, and source enrichment can often run in parallel after the research scope is fixed. Writing must wait until research, enrichment, and validation are complete.

## Merge Rules

- Treat the research packet claim ledger as the source of truth for factual claims.
- Specialist outputs may add detail only when sourced or derived from reproducible artifact analysis.
- Preserve uncertainty labels: `confirmed`, `likely`, `unclear`, `not_observed`, `disputed`.
- If specialists disagree, create a conflict block instead of averaging claims.
- Prefer direct source, registry metadata, exact commits, advisories, and original researcher posts over secondary writeups.
- Use raw IOCs only in machine-readable JSON or exports. Defang network IOCs in prose and human-readable YAML.

## Required Site-Worker Output

For every orchestration run, produce:

```yaml
site_worker_result:
  mode: "new_incident_post|existing_post_upgrade|campaign_update|detection_pack_only|site_wide_audit"
  decision: "publish_ready|needs_review|reject|update_existing|attach_to_campaign|duplicate"
  event_id: ""
  slug: ""
  parent_campaign_id: "none"
  spawned_tasks: []
  completed_artifacts: []
  validation_results: []
  blocking_gaps: []
  recommended_next_action: ""
```

## Clean Deploy Isolation

When deploying one logical Halting Problems change while `/home/sam/haltingproblems.com` has unrelated dirty work, use a temporary git worktree from `origin/main`, commit/push/deploy only the intended files from that worktree, verify production URLs, then remove the worktree. See `references/haltingproblems-clean-deploy-worktree.md`.

## Validation Checklist

Before declaring a post publish-ready:

- Research packet is not `reject`.
- Affected package/artifact identity is known or explicitly unknown with explanation.
- Malicious version, digest, tag, or workflow reference is known or explicitly unknown.
- Standardized post template [post-template.md](file:///home/sam/haltingproblems.com/skills/site-worker/references/post-template.md) was followed for layout.
- Narrative sections contain source attribution for every behavioral claim and clearly distinguish observed behavior from inference.
- Every remediation and recommendation has a clear rationale and is uniquely written (no generic boilerplate checklist templates).
- An explicit applicability decision was made mapping threat vectors to platforms before adding endpoint, registry, GitHub, browser, CI/CD, or cloud audit modules.
- Exactly one reviewed hunt manifest exists in the research repository per script, and each manifest `script_path` resolves under `~/hp-posts-info/<slug>/`.
- Core claims appear in the claim ledger.
- Every claim-heavy paragraph in the final post has nearby citations, and markdown validators may require an explicit citation marker like `[1]` even when links already appear in the sentence.
- Detection section contains actionable hunt recipes, not vague bullets.
- Downstream credential audits exist when credentials are at risk.
- Handling scripts live in the `hp-posts-info` sibling repository, embed exact incident packages, versions, hashes, domains, action refs, timestamps, and audit event names as literals.
- Keep `affected_assets.packages` canonical and unversioned; put scoped version constraints in `iocs.package_versions` so package-prefix tests pass.
- Handling scripts require only reader-specific scope values such as `ORG`, `REPOS_FILE`, cloud account/project/subscription IDs, or exported telemetry directories.
- GitHub and cloud scripts enumerate run/session IDs dynamically and do not contain `RUN_ID` placeholders.
- `~/hp-posts-info` exists before any import; importing without the intended sibling repo can omit canonical scripts, IOCs, or analysis prose.
- In isolated worktrees, importer dry-run still expects the sibling research checkout at `../hp-posts-info` relative to the website repo unless `--posts-info-dir` points elsewhere.
- Postgres migrations have been applied and the importer has loaded tested `hp-posts-info` script bodies into `threat_scripts`; deploy success alone is not enough. Withhold `publish_ready` until `/threat/<slug>` and API checks prove the expected rows are present.
- `/threat/<slug>` renders expected prose, IOCs, package facts, sources, timeline, and hunts for every imported post.
- If a legacy compile run rewrites many unrelated posts in a worktree, treat that as incidental churn unless you intend a broad migration refresh. Validate the candidate with the modular site-worker plan, `hp-posts-info` tests, the Postgres importer dry-run/import, `pnpm check`, `pnpm test`, `pnpm build`, and DB-backed page/API checks instead of treating generated markdown parity as authoritative.
- If a legacy content validator reports stale content for unrelated slugs, record that as repo-wide legacy parity debt. Do not treat it as a candidate-specific regression when the candidate's modular plan, scripts, importer, Postgres rows, Next.js build, and DB-backed page/API checks pass.
- If a refresh prunes or replaces most authoring content, do not add Next app fallback/mock data. Update importer fixtures and DB-backed tests instead.
- After deploy, verify both the preview/custom-domain article URL and DB-backed API outputs. If simple scripted fetches return a false 403 at the edge, retry with an explicit browser-like `User-Agent` before treating verification as failed.
- For `/api/feed`, verify content depth rather than just HTTP status: every affected package row should appear, packages without exact version data should not be dropped, and observable facts should be exported as `iocs[]`. See `references/feed-packages-iocs-export.md` for the regression and production spot-check pattern.
- For production Postgres imports and Cloudflare deploys, use `references/postgres-import-deploy-hyperdrive-pitfalls.md`: when local `.env.local` is absent, use the protected remote admin importer; set `CANONICAL_DATA_SOURCE=postgres` so search/feed do not stay on legacy paths; verify all new `/threat/<slug>`, `/api/search`, `/api/feed`, and `/api/health/canonical` responses; and if intermittent Worker `1101` hung-request errors appear, tail the Worker and check for stale module-level Hyperdrive/postgres client reuse.
- When rendering tested scripts on Next threat pages, use `references/threat-page-hunting-script-rendering.md`: `threat_scripts` is the canonical tested-script surface, so filter imported `Hunt Manifest:` analysis sections from the public Analysis flow and keep code blocks styled/focusable.
- When migrating subscriber capture from legacy D1/Functions into the Next.js/OpenNext + Postgres path, use `references/postgres-subscriber-migration.md`: add a Postgres `subscribers` table and Drizzle schema, implement `/api/subscribe` as an App Router endpoint, migrate D1 rows through a protected admin action when direct DB access is unavailable, and verify production row counts plus homepage/API behavior.
- When production threat pages link to `hp-posts-info/blob/main/...`, push the corresponding research folders to `hp-posts-info` `main` and verify raw/script URLs return `200`; importing local-only or preview-branch folders leaves broken source links even if Postgres rows render.
- When Sam asks for a dev/preview page but says not to publish production, a temporary local Next server plus localtunnel is an acceptable review surface after full local verification. Keep it explicitly dev-only, verify `/`, `/api/search?q=<known-term>`, and at least one `/threat/<known-slug>`. If `pnpm start` reports `EADDRINUSE`, check whether an existing Next server is already serving the current checkout before starting/killing processes. See `references/dev-preview-next-localtunnel.md` for the exact pattern, process hygiene, and Cloudflare Pages caveat.
- If attempting Cloudflare Pages preview for this Next app, do not blindly add `runtime = 'edge'` to dynamic routes if shared data modules import Node/Postgres dependencies; that can break `pnpm build` with missing `net`, `tls`, `stream`, or `perf_hooks`. Prefer the localtunnel preview for review-only work unless the task is specifically to migrate the app to Cloudflare Edge compatibility.
- If the site deploy succeeds but Postgres migration/import fails or was intentionally not run, do not call the article fully `publish_ready`: report a partial app deploy or `needs_review`, verify the DB-backed page/API outputs, and state exactly what data is missing.
- In a dirty main checkout with unrelated user changes, prefer a temporary clean git worktree based on `origin/main` for the final publish commit/deploy. Copy only the candidate post into that worktree, run `pnpm check` and `pnpm build` there, commit, push `HEAD:main`, deploy, then verify URLs. Do not `git pull --rebase` through unrelated untracked posts that may be overwritten.
- If a publisher workflow should syndicate a newly deployed article to Reddit, run the Reddit poster only after the site publish/deploy succeeds, configure required subreddit flair IDs ahead of time, and seed the Reddit dedupe state before enabling automation so the first cron run does not repost the latest article manually pushed earlier.
- If Sam asks to pause Reddit syndication, do not pause the whole site refresh pipeline. Update the publisher cron prompt to explicitly prohibit `scripts/reddit_user_crossposter/run_sync.sh`, posting, crossposting, and syndication, then verify the old automatic Reddit-runner instruction is gone.
- Treat a zero-exit Reddit sync as insufficient proof of syndication by itself. Review the JSON result for `submitted_direct_posts`, `submitted_crossposts`, or other submitted-item arrays; if they are empty, report that no Reddit post was actually made even when `errors` is empty.
- Remediation workflow includes containment, eradication, recovery, and closure gates.
- Machine-readable event profile is valid JSON.
- Legacy Astro frontmatter is migration-reference material only; new publish-ready outputs must be validated through the Next.js/Postgres pipeline.
- `sourceCount` equals numbered source entries.
- Network IOCs are defanged outside machine-readable blocks.
- Open questions are not hidden.
- `pnpm run validate:content` is a legacy compatibility check, not the authoritative publication gate. Use the modular plan validator, `hp-posts-info` tests, Postgres importer validation, `pnpm build`, and DB-backed Next.js page/API checks as the canonical readiness gates.
- If `pnpm run compile:posts` creates an accidental duplicate or campaign-only draft, delete the stray markdown before the final validation pass and re-run the compiler so the site and research repository stay aligned.
- Prefer one canonical incident slug; only split into a campaign post when the evidence establishes a real parent/child relationship.
- When creating support files for a refresh candidate, keep session notes under `references/` rather than the slug root. The slug root should stay reserved for the canonical manifest, IOC profile, scripts, tests, fixtures, and published-support files that the validators expect.
- If a queued orchestration candidate is marked `recommended_mode: new_incident_post` and `canonical_existing_slug` is empty, treat it as a true net-new post candidate. Do not prune its research slug as stray merely because no site Markdown exists yet; instead scaffold `~/hp-posts-info/<candidate_id>/`, preserve fetched registry metadata and tarballs under `references/` or `artifacts/`, and continue through the new-post decision flow.
- For anti-analysis or safety-triggering npm artifacts (for example giant single-file packages that rely on prompt-injection text, context flooding, or other poison-pill content), keep inspection static and metadata-driven: capture registry timestamps, maintainer metadata, tarball hashes, file inventory, package.json fields, code-size metrics, and safe keyword/count summaries without printing raw payload text into the transcript.
- If a validator complains that IOC values are not represented in a manifest script, add incident-specific constants for the cited domains, URLs, package versions, and file patterns directly into the script and make the scan logic reference them so the checks stay green.
- When migrating older Astro/blog roundup coverage into the canonical Next.js/Postgres pipeline, use `references/astro-roundup-to-postgres-migration.md`: dedupe existing threat posts and `hp-posts-info`, scaffold missing incidents as conservative `needs_review` folders with source-backed selectors, validate with `hp-posts-info` pytest and Postgres importer dry-runs, and do not claim publish-ready until live Postgres import plus DB-backed route/API checks pass.
- When a post/refresh compiles but `validate:content` flags a stray `research.md`, move or delete the root-level draft and keep the reviewed note in `references/`.

See [references/site-refresh-validation-pitfalls.md](references/site-refresh-validation-pitfalls.md), [references/refresh-post-generation-pitfalls.md](references/refresh-post-generation-pitfalls.md), [references/refresh-validation-debt.md](references/refresh-validation-debt.md), [references/reddit-syndication.md](references/reddit-syndication.md), [references/new-post-clean-worktree-and-syndication-pitfalls.md](references/new-post-clean-worktree-and-syndication-pitfalls.md), [references/deploy-d1-sync-ordering.md](references/deploy-d1-sync-ordering.md), [references/static-publish-with-d1-script-gap.md](references/static-publish-with-d1-script-gap.md), [references/coverage-scope-policy.md](references/coverage-scope-policy.md), [references/research-parity-repair.md](references/research-parity-repair.md), [references/postgres-import-deploy-hyperdrive-pitfalls.md](references/postgres-import-deploy-hyperdrive-pitfalls.md), [references/postgres-subscriber-migration.md](references/postgres-subscriber-migration.md), [references/agency-frontend-ux-review-implementation.md](references/agency-frontend-ux-review-implementation.md), [references/feed-packages-iocs-export.md](references/feed-packages-iocs-export.md), and [references/dev-preview-next-localtunnel.md](references/dev-preview-next-localtunnel.md) for June 2026 validator, refresh, clean-worktree publication, legacy deploy/D1/static compatibility notes, coverage-scope pruning, research/frontend parity repair, production Postgres import and Hyperdrive deploy pitfalls, subscriber migration to Postgres, Agency Agents-driven frontend UX/accessibility implementation, feed package/IOC export checks, dev-only Next previews, and post-deploy Reddit automation notes.

## Safety and Sandbox Constraints

When performing static analysis, research, or testing:
1. **Never Execute Untrusted Code**: Do NOT run, execute, or install downloaded packages, scripts, binary extensions, or other artifact contents (never run `node`, `npm install`, `bun`, `pip install`, `python` code executions, or open extensions in an active editor shell). Inspect files statically using safe read-only operations.
2. **Avoid API Guardrail Triggers (Poison Pill Protection)**: When a file contains safety-triggering concepts (such as detailed exploit instructions, prompt injection lines, or biological/chemical weapon keywords), do **NOT** print or include the raw text content of these files in the tool execution outputs or terminal dumps. Doing so will immediately trigger backend LLM safety/biosecurity guardrails and break the gateway.
3. **Safe Inspection Protocol**:
   - Write a helper Python script to process the file locally on the sandbox filesystem.
   - The script should scan, match patterns, or count keywords internally and return only high-level metadata (such as sizes, hashes, presence of imports, or boolean flags) or defanged/redacted summaries to the agent context (e.g., `contains_dangerous_keywords: true`, `words_matched: ['[REDACTED_BIO_TERM]']`).
   - If snippets must be shown, replace dangerous keyword tokens with redactions before outputting them to stdout.
4. **Isolate Downloaded Files in the Research Repo**: Always write, download, extract, or copy untrusted package tarballs, extensions, or files being analyzed directly to the corresponding post directory in the sibling research repository (`~/hp-posts-info/<slug>/`). Never download, write, or extract them to locations outside this repository, such as `/tmp/`, `/home/sam/`, or the website root.



## Failure Behavior

If blocked, produce a review memo instead of a post. Include:

- missing direct or primary sources
- unresolved package/version/timeline conflicts
- unsupported attribution
- missing artifact evidence
- missing telemetry required for hunts
- exact next collection steps
