# Supply-chain scope gate for Halting Problems refreshes

Use this when refreshing Halting Problems from public sources or running scheduled discovery/publisher cron jobs.

## In scope

Promote candidates only when the event is a supply-chain attack or supply-chain-adjacent security event with a clear relationship to at least one of:

- repository compromise
- package compromise
- CI/CD abuse
- developer tooling compromise
- signed artifact compromise
- registry abuse
- provenance abuse
- dependency confusion
- malicious package distribution
- maintainer or account takeover
- browser/CDN supply-chain exposure
- content supply-chain compromise

Every survivor candidate should state the specific supply-chain angle in `reason` so the publisher job can enforce the gate without reinterpreting vague discovery output.

## Out of scope unless explicitly tied to software delivery

Reject or mark `needs_review` instead of promoting:

- generic CVE/KEV vulnerability items
- generic KEV roundups
- broad ransomware or exploitation news
- vendor advisories with no artifact, registry, repository, CI/CD, developer-tooling, signed-binary, provenance, or content-distribution compromise angle

If direct evidence is missing, record the missing evidence in `collection_gaps`. Do not stretch a vulnerability story into supply-chain coverage based on loose mentions of credentials, build hosts, or enterprise impact.

## Cron split pattern

Discovery job prompt should:

- discover only supply-chain attacks or supply-chain-adjacent security events
- reject CVE/KEV-only items unless the direct evidence ties them to software delivery compromise
- require every survivor reason to name the supply-chain angle
- return strict YAML with empty `survivors: []` when nothing qualifies

Publisher job prompt should:

- treat discovery output as an input queue, not a mandate to publish
- reapply the same scope gate before creating or updating content
- reject any generic CVE/KEV survivor that slipped through discovery
- return `[SILENT]` when there are no survivors

## Test guard

For Halting Problems, keep a small repository-policy test that asserts the source-watcher skill, site-refresh-orchestrator skill, and cron prompts all contain the supply-chain scope gate language. This prevents future prompt edits from quietly broadening the site back into general vulnerability coverage.
