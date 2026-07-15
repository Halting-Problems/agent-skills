# Refresh dedupe and indexing notes

Session notes from the 2026-06-19 site refresh run.

## Canonical index source

Build the existing-site index from canonical Postgres incidents and candidate records. Include stable incident IDs, slugs, source URLs, package/repository identities, campaign relationships, publication state, and candidate dispositions.
Do not use rendered application output, D1 replica rows, temporary exports, or scratch JSON as the source of truth.

## URL comparison behavior

- Normalize URLs before comparing them.
- Strip tracking query parameters such as `utm_*`, `fbclid`, `gclid`, `mc_cid`, `mc_eid`, and `igshid`.
- Compare canonicalized URLs against source records linked to Postgres incidents and candidates.

## Dedupe rules that held up in this session

- Primary-feed items from CISA KEV, StepSecurity, and Sonatype often map directly to already-published posts.
- Treat campaign overviews and follow-up explainers as duplicates when they point to the same primary source or share stable dedupe keys such as `campaign:*`, `package:*`, `repo:*`, or `payload:*`.
- When a cleaned index collapses the candidate queue to zero, report that as already covered instead of trying to fabricate work orders.

## Work-order builder usage

`scripts/build_refresh_work_orders.py` is a compatibility wrapper around the sibling website's `tooling/orchestration/disposition-candidates.ts`. The typed command combines source-watcher output with canonical Postgres facts and emits one site-worker prompt per surviving candidate. A zero-survivor result remains auditable in the durable dossier run and candidate records.

## Practical note

During the June 19 refresh, CISA KEV additions, the JetBrains malicious plugin follow-up, Mastra/easy-day-js echoes, Atomic Arch echo coverage, and Miasma explainers were all deduped to existing posts by canonical URLs or incident-family keys.
