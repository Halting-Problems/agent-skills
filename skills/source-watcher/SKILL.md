---
name: haltingproblems-source-watcher
description: Use when finding candidate supply-chain incidents from public feeds, advisories, registries, GitHub, security research blogs, and watch pages.
---

# Halting Problems Source Watcher

## Mission

Find candidate incidents that may deserve a research packet or an update to an existing post.

This skill does not write final posts. It produces a candidate queue with source URLs, preliminary classification, dedupe keys, and collection gaps.

## Inputs

- seed sources
- website URL or current feed
- source taxonomy
- date window
- topic scope

## Required Output

```yaml
candidate_incidents:
  - candidate_id: ""
    title: ""
    first_seen: ""
    candidate_threat_classes: []
    ecosystem: []
    affected_assets: []
    starting_sources:
      - name: ""
        url: ""
        source_role: "DIRECT_SOURCE|PRIMARY_RESEARCH|SECONDARY_ANALYSIS|SYNDICATION_NEWS|ENRICHMENT_DATA"
    dedupe_keys: []
    suggested_next_skill: "supply-chain-compromise-researcher"
    confidence: "low|medium|high"
    reason: ""
    collection_gaps: []
```

## Supply-chain scope gate

Discovery is scoped to supply-chain attacks or supply-chain-adjacent security events. Promote candidates only when the event plausibly involves repository compromise, package compromise, CI/CD abuse, developer tooling compromise, signed artifact compromise, registry abuse, provenance abuse, dependency confusion, malicious package distribution, maintainer/account takeover, browser/CDN supply-chain exposure, or content supply-chain compromise.

Do not promote generic CVE/KEV vulnerability items, generic KEV roundups, ransomware/vulnerability news, or vendor advisories unless the direct evidence ties the event to a software supply-chain or software-delivery compromise angle. If the supply-chain angle is unclear, put the item in `needs_review` or `rejected` with the missing evidence instead of promoting it as a survivor.

## Rules

- Prefer direct sources and primary research.
- Do not create new incidents from syndicated news alone.
- Do not merge incidents into campaigns unless hard indicators support it.
- Record exact URLs.
- Give every candidate a stable dedupe key.
- Every promoted candidate must explain its supply-chain or supply-chain-adjacent angle in `reason`.

## Discovery pitfalls and feed handling

- Parse RSS `pubDate` fields with a robust RFC 2822 parser such as Python `email.utils.parsedate_to_datetime()`; do not assume every blog feed fits a small `strptime()` format list.
- Canonicalize feed URLs before dedupe, including removal of tracking query parameters such as `utm_*`, because some feeds append marketing params to otherwise-canonical article URLs.
- Do not assume every source exposes `/rss.xml` or `/feed/`. If a source lacks a clean feed endpoint, fall back to homepage/sitemap discovery and fetch candidate pages to recover publication dates.
- A short discovery window, such as 4 hours, can legitimately yield zero candidates even when sources are healthy. Return an empty candidate queue rather than stretching the window or promoting older items.

See `references/public-feed-quirks.md` for confirmed feed endpoints and fallback patterns from the 2026-06-20 refresh session.
