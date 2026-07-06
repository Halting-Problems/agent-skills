# Refresh dedupe and indexing notes

Session notes from the 2026-06-19 site refresh run.

## Canonical index source

Build the existing-site index from `src/content/threat-posts/*.md` only.
Do not use `dist/`, temporary exports, or scratch JSON as the source of truth.

## URL comparison behavior

- Normalize URLs before comparing them.
- Strip tracking query parameters such as `utm_*`, `fbclid`, `gclid`, `mc_cid`, `mc_eid`, and `igshid`.
- Compare canonicalized URLs against the source URLs cited by the site posts.

## Dedupe rules that held up in this session

- Primary-feed items from CISA KEV, StepSecurity, and Sonatype often map directly to already-published posts.
- Treat campaign overviews and follow-up explainers as duplicates when they point to the same primary source or share stable dedupe keys such as `campaign:*`, `package:*`, `repo:*`, or `payload:*`.
- When a cleaned index collapses the candidate queue to zero, report that as already covered instead of trying to fabricate work orders.

## Work-order builder usage

`scripts/build_refresh_work_orders.py` can take source-watcher output plus an existing index and emit one site-worker prompt per surviving candidate. This is useful even when the final answer is zero new candidates, because it makes the dedupe result auditable.

## Practical note

During the June 19 refresh, CISA KEV additions, the JetBrains malicious plugin follow-up, Mastra/easy-day-js echoes, Atomic Arch echo coverage, and Miasma explainers were all deduped to existing posts by canonical URLs or incident-family keys.
