# KEV cron import and verification pitfalls

Lessons from the 2026-07-09 automated exploited-vulnerability refresh.

## Protected admin importer

When selected `hp-posts-info/<slug>/` folders validate locally but production import returns `401 unauthorized`, treat it as an admin-secret propagation/configuration issue, not a content problem.

Pattern:
1. Confirm local parsing and dry-run import pass first.
2. Rotate `ADMIN_SECRET` with Wrangler if the local secret is stale.
3. Update the local `.env.local` value to the same generated secret.
4. Wait briefly for Worker secret propagation before retrying selected-slug imports.
5. Re-run production `/api/health/canonical` and per-slug checks after import.

Do not report the post publish-ready until the retry succeeds and production DB-backed routes verify.

## Research push / local checkout confusion

A local `hp-posts-info` branch may show newly created slug folders as untracked even when `origin/main` already contains those exact folders from an earlier clean publish worktree. Before creating another commit or pushing duplicate work, verify `origin/main` with `git ls-tree` or raw GitHub URLs. If raw script URLs return 200 and content is already on `main`, clean the local untracked copies instead of forcing a new commit.

## Feed contract details

`/api/feed` currently exposes entries under `entries[]` with IDs shaped like `HP-<slug>`, not a top-level `items[]` or direct `slug` field. Feed verification should:

- locate entries by `id == "HP-<slug>"`;
- verify `affected[]` is non-empty for each imported candidate;
- verify the expected CVE appears in the serialized entry;
- verify advisory/source infrastructure is not emitted in `iocs[]` unless it is a true attacker-controlled or exploitation-observed IOC.

## Threat page hunt-manifest rendering

A rendered `Hunt Manifest:` block on `/threat/<slug>` is expected for imported tested scripts. Do not fail verification merely because the page contains the phrase `Hunt Manifest:`. The regression to guard against is duplicate analysis-section leakage or missing tested-script rendering; a good check is HTTP 200 + expected CVE + rendered hunt/script block.

## Discovery outcome

A site source-watcher run can legitimately return zero recent candidates while KEV/manual exploited-vulnerability enrichment yields publishable candidates. Report these as separate discovery lanes instead of treating zero source-watcher survivors as a no-op when the cron prompt explicitly asks for KEV/newly exploited vulnerability enrichment.
