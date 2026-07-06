# Astro roundup to Next.js/Postgres incident migration

Use this when an older Astro blog roundup names supply-chain attacks that are not yet represented as standalone `~/hp-posts-info/<slug>/` folders for the Next.js/Postgres pipeline.

## Durable pattern

1. Treat the old Astro/blog post as a coverage index, not as the canonical source of truth.
2. Dedupe against both surfaces:
   - `~/haltingproblems.com/src/content/threat-posts/*.md`
   - `~/hp-posts-info/<slug>/`
3. For each uncovered incident, scaffold a standalone `~/hp-posts-info/<slug>/` folder containing:
   - `analysis.md`
   - `iocs.json`
   - `manifest.yaml`
   - at least one tested script under `scripts/`
4. Keep publication state conservative unless fresh artifact work was performed:
   - use `publication_state: "needs_review"`
   - explain that indicators are source-backed but fresh artifact diffing / cleanup verification was not performed
5. Preserve provenance in `iocs.json` and prose:
   - primary source URLs in `sources.primary_research`
   - old Halting Problems blog URL in `sources.correlated` when relevant
   - an explicit `artifact_analysis.provenance.migration_source` note
6. Build hunt scripts around durable selectors from the cited primary research:
   - packages / action names / repository names
   - malicious versions or tag selectors
   - file names and persistence paths
   - domains, URLs, hashes, process strings, network markers
   - campaign-specific dead-drop strings or repository naming patterns
7. Do **not** execute untrusted package artifacts. Static text extraction from public research pages is OK; package contents still follow the untrusted-artifact static-inspection rule.

## Validation sequence

Run the research-repo checks first, then website importer and app checks:

```bash
cd ~/hp-posts-info
.venv/bin/pytest tests -q

cd ~/haltingproblems.com
pnpm exec tsx scripts/import-posts-info-to-postgres.ts --posts-info-dir ../hp-posts-info --dry-run --slug <slug>
pnpm exec tsx scripts/import-posts-info-to-postgres.ts --posts-info-dir ../hp-posts-info --dry-run
pnpm test -- --run
pnpm check
pnpm build
```

A local `pnpm build` warning that Postgres is not configured and the build fell back to static summaries is not, by itself, a migration failure. Do not call the post fully publish-ready until a real configured Postgres import and DB-backed route/API verification have also passed.

## Plan-validator pitfall

`skills/site-worker/scripts/site_worker_plan.py` expects the event-profile shape it was written for. Passing a full `iocs.json` document directly may produce a plan that `validate_site_worker_plan.py` rejects with missing required task suffixes. Do not treat that as evidence that the newly scaffolded incident folders are invalid; rely on `hp-posts-info` pytest and importer dry-runs for the folder/import contract, and only use the plan tool with an event profile that matches its expected input.

## Reporting

When summarizing this migration, distinguish:

- **coverage added**: new `hp-posts-info` folders and scripts exist
- **validated**: pytest/importer/check/test/build results
- **not yet done**: live Postgres import, deploy, DB-backed `/threat/<slug>`, `/api/feed`, and `/api/search` verification
