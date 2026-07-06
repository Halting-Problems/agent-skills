# Agent skills for Halting Problems

This repo packages the skills and plugin code used to run the Halting Problems threat-intel site workflow.

The site itself lives in `~/haltingproblems.com`. The post/source material lives in `~/hp-posts-info`. This repo is the portable agent layer: it explains how the work is split across specialist skills, what each skill owns, and how the pieces move from raw source discovery to a live Postgres-backed Next.js threat page and JSON feed.

## Repository layout

```text
skills/   Agent skills used by the Halting Problems workflow
plugins/  Hermes/agent plugins used by the site-growth workflow
```

Current plugin:

| Path | Purpose |
|---|---|
| `plugins/halting-problems-growth-engine/` | Growth/content helper for Halting Problems planning, briefs, and site/feed work. |

## The short version

Halting Problems uses a staged pipeline:

```text
source discovery
  -> scope and dedupe decision
  -> evidence and artifact research
  -> package / IOC normalization
  -> hunting scripts and detection packs
  -> remediation guidance
  -> post/schema normalization
  -> agency review
  -> import into Postgres
  -> Next.js pages and APIs
  -> production verification
```

The main rule is simple: **do not publish decorative summaries when defenders need operational details.** Packages, versions, IOCs, scripts, source links, and remediation steps should survive the whole flow.

## Main orchestration flow

### 1. Discover candidate incidents

Skill: `source-watcher`

Finds possible supply-chain incidents from feeds, blogs, advisories, registries, and research sources. Output should be a small candidate record with source URLs, summary, suspected ecosystem, and why it may be in scope.

### 2. Decide whether it belongs on the site

Skill: `site-feed-curator-and-dedupe-skill`

Decides whether a candidate is:

- a new post
- an update to an existing post
- part of a campaign
- a duplicate
- out of scope

This avoids creating multiple posts for the same event and keeps the site focused on real supply-chain compromise rather than generic vulnerability news.

### 3. Build the evidence packet

Skills:

- `supply-chain-artifact-diff-lab`
- `provenance-and-publishing-integrity-auditor`
- `campaign-clustering-and-event-graph-builder`

These skills check what changed, whether package/release/signing/provenance claims hold up, and whether related incidents should be grouped or kept separate.

The expected output is a claim ledger: what is confirmed, what is likely, what is unknown, and what each source supports.

### 4. Turn research into defender action

Skills:

- `soc-ir-enrichment-engineer`
- `cloud-oidc-and-ci-cd-abuse-hunter`
- `browser-side-supply-chain-exposure-analyst`
- `developer-endpoint-forensics-runbooker`
- `remediation-and-credential-rotation-planner`

These skills convert the incident into practical response work:

- repository and package-lock audits
- CI/CD and GitHub Actions checks
- cloud/OIDC abuse checks
- endpoint and developer workstation triage
- browser/CDN exposure review when relevant
- credential rotation and recovery steps

### 5. Normalize IOCs and detections

Skills:

- `ioc-normalizer-and-sharing-exporter`
- `detection-pack-generator`

These produce machine-readable observables and detection logic. Output can include CSV/STIX/MISP-lite-style IOC exports, Sigma/YARA/osquery/KQL/SPL-style detections, and script inputs for the post folder.

### 6. Prepare the post folder

Skills:

- `post-schema-normalizer-and-migrator`
- `site-worker`

Each publishable incident should have a folder in `~/hp-posts-info/<slug>/` with:

```text
analysis.md or analysis.mdx
manifest.yaml
iocs.json
scripts/
tests/
fixtures/
```

The important part: hunting scripts live with the post source material, not as loose snippets in the website repo. They need tests and fixtures before import.

### 7. Import into the website database

Website repo: `~/haltingproblems.com`

Typical validation/import path:

```bash
cd ~/haltingproblems.com
pnpm exec tsx scripts/import-posts-info-to-postgres.ts --posts-info-dir ../hp-posts-info --dry-run
```

After dry-run passes, import to production Postgres using the approved site workflow. Then verify that the live site/API reads the new rows.

### 8. Review and verify

Skills/references:

- `site-worker/references/agency-agent-review-lanes.md`
- `site-worker/references/agency-frontend-ux-review-implementation.md`
- `site-worker/references/feed-packages-iocs-export.md`

Before calling work done, verify more than HTTP 200s:

- `/threat/<slug>` renders the expected prose, packages, IOCs, sources, timeline, and tested scripts.
- `/api/feed` includes all affected packages and exported IOCs.
- `/api/search?q=<known-term>` finds the incident.
- `pnpm check`, tests, and builds pass in the website repo.
- Production pages are checked after deploy.

## Skill map

| Skill | Role in the workflow |
|---|---|
| `site-worker` | Main orchestrator. Decides mode, coordinates specialists, validates import/deploy readiness. |
| `source-watcher` | Finds candidate incidents from public sources. |
| `site-refresh-orchestrator` | Builds broader refresh work orders for ongoing monitoring. |
| `site-feed-curator-and-dedupe-skill` | Scope gate and duplicate/update/campaign decision. |
| `supply-chain-artifact-diff-lab` | Compares malicious/benign packages, containers, actions, extensions, or artifacts. |
| `provenance-and-publishing-integrity-auditor` | Checks tags, releases, signing, publishing provenance, and builder integrity. |
| `campaign-clustering-and-event-graph-builder` | Links incidents only when there is strong evidence. |
| `soc-ir-enrichment-engineer` | Converts research into SOC/IR audit steps and telemetry checks. |
| `cloud-oidc-and-ci-cd-abuse-hunter` | Handles GitHub Actions, cloud trust, OIDC, and CI/CD abuse paths. |
| `browser-side-supply-chain-exposure-analyst` | Handles frontend/CDN/browser supply-chain exposure. |
| `developer-endpoint-forensics-runbooker` | Handles workstation, IDE extension, and endpoint triage. |
| `detection-pack-generator` | Produces detection packs and validates query/actionability quality. |
| `ioc-normalizer-and-sharing-exporter` | Normalizes and exports observables. |
| `remediation-and-credential-rotation-planner` | Produces containment, rotation, recovery, and closure plans. |
| `post-schema-normalizer-and-migrator` | Normalizes old and new post data into the expected schema. |
| `find-skills` | Helps discover/install skills when expanding the toolkit. |

## Data contracts

### Event profile

The pipeline starts from an event profile with fields like:

```json
{
  "slug": "example-incident",
  "title": "Example supply-chain incident",
  "source_urls": [],
  "ecosystems": ["npm"],
  "affected_packages": [],
  "observables": [],
  "status": "needs_review"
}
```

### Post source folder

The post folder in `hp-posts-info` is the handoff format between research and the website importer.

```text
hp-posts-info/<slug>/
  analysis.md
  iocs.json
  manifest.yaml
  scripts/<tested_hunt_script>
  tests/<script_tests>
  fixtures/<mock_inputs>
```

### Website serving path

The website serves from Postgres through the Next.js app:

```text
hp-posts-info folder
  -> importer
  -> Postgres CTI tables
  -> Next.js threat page
  -> /api/feed and /api/search
```

## Running helper tests

Some skills include scripts/tests. From this repo you can run quick validation like:

```bash
python -m pytest skills/site-worker/tests
python plugins/halting-problems-growth-engine/tests/validate_growth_engine_pack.py
```

The website itself still needs its own checks from `~/haltingproblems.com`:

```bash
pnpm check
pnpm test -- --run
pnpm build
pnpm run build:cloudflare
```

## Adding or changing skills

When a new workflow becomes repeatable, add it as a skill or a reference under the nearest existing skill.

Good places to add details:

- reusable pipeline rule: `skills/site-worker/SKILL.md`
- one-off pitfall or deploy recipe: `skills/site-worker/references/*.md`
- reusable audit script: the relevant skill's `scripts/` directory
- sample output: the relevant skill's `examples/` directory

Keep skill text direct and practical. Avoid filler. Each instruction should change what an agent does or how it verifies the work.
