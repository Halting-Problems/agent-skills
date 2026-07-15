# KEV Cron Selected Import Session Notes

Use these notes when a scheduled Halting Problems refresh must add newly reported KEV/exploited-vulnerability coverage and publish through the existing Postgres-backed site without a website code deploy.

## Durable workflow refinements

- A zero-result site-feed watcher is not enough to return `[SILENT]` when the cron prompt also asks for exploited-vulnerability coverage. Continue to CISA KEV delta discovery and NVD/vendor enrichment.
- Keep DAG artifacts out of the slug root. Put `event_profile.json`, `site-worker-plan.json`, review YAMLs, run ledgers, and task artifacts under `references/`; keep the root limited to `analysis.md|analysis.mdx`, `iocs.json`, `manifest.yaml`, and expected directories.
- Focused slug pytest runs can create `fixtures/out-*` directories when hunt scripts write reports. Delete generated `fixtures/out-*` before committing and pushing research folders.
- The protected production importer can import selected slugs through `/api/admin/migrate` with `action: "import"` and a parsed `ParsedPostInfo` payload when local Postgres is unavailable. Load `ADMIN_SECRET` from the live environment or `.env.local`, but do not persist helper scripts unless they are intentionally supported tooling.
- For feed verification, locate rows by `entries[].id == "HP-<slug>"`. Package data may be in OSV-style `affected[]` rather than a top-level `packages` field. Verify content depth by checking `affected[].package.name` and `iocs[]`, not just HTTP 200.
- Do not treat CISA/NVD/vendor/GHSA/MSRC/advisory URLs as attacker IOCs. Put source URLs in sources or detection selectors. Keep `iocs.domains`, `iocs.urls`, `iocs.hashes`, and `iocs.ips` empty when public sources publish no attacker-controlled observables.
- After pushing selected research folders to `hp-posts-info` main, verify each raw script URL under `https://raw.githubusercontent.com/Halting-Problems/hp-posts-info/main/<slug>/scripts/<script>.py` returns 200 before reporting production links as healthy.

## Minimal production verification set

1. `/api/health/canonical` returns 200 with `canonicalDataSource` primary/cloud and increased incident/script counts.
2. Every `/threat/<slug>` returns 200 and includes hunt/script content.
3. `/api/search?q=<CVE>` returns the matching CVE.
4. `/api/feed` contains `HP-<slug>` rows, `affected[]` package entries, and no source/advisory domains in incident IOC fields.
5. Raw GitHub script URLs return 200 from `hp-posts-info` main.
