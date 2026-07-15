# Supply-chain scope gate for Halting Problems refreshes

Use this when refreshing Halting Problems from public sources or running scheduled discovery/publisher cron jobs.

## In scope

Promote candidates only when the event is a supply-chain attack, supply-chain-adjacent security event, or is a noteworthy exploited vulnerability (CVE/KEV) or zero-day with active exploitation in the wild, with a clear relationship to at least one of:

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
- noteworthy exploited vulnerabilities (CVEs/KEVs) and zero-days with active exploitation in the wild

Every survivor candidate should state the specific supply-chain or active exploitation angle in `reason` so the publisher job can enforce the gate without reinterpreting vague discovery output.

## Out of scope

Reject or mark `needs_review` instead of promoting:

- generic, unexploited vulnerabilities (i.e. those without active exploitation in the wild)
- ordinary network appliance, OS, browser, VPN, web-app, or product CVEs that are not subject to active exploitation or zero-day abuse
- standard patch advisories without active exploitation or supply-chain context
- broad ransomware or exploitation news without active exploitation or supply-chain angle

If direct evidence is missing, record the missing evidence in `collection_gaps`. Do not stretch a vulnerability story into coverage based on loose mentions of credentials, build hosts, or enterprise impact if it lacks active exploitation or a software delivery angle.

## Cron split pattern

Discovery job prompt should:

- discover supply-chain attacks, supply-chain-adjacent security events, or noteworthy exploited vulnerabilities (CVEs/KEVs) and zero-days with active exploitation in the wild
- reject generic, unexploited CVE/KEV-only items unless there is active exploitation or they tie to software delivery compromise
- require every survivor reason to name the supply-chain or active exploitation angle
- return strict YAML with empty `survivors: []` when nothing qualifies

Publisher job prompt should:

- treat discovery output as an input queue, not a mandate to publish
- reapply the same scope gate before creating or updating content
- reject any generic, unexploited CVE/KEV survivor that slipped through discovery
- return `[SILENT]` when there are no survivors

## Test guard

For Halting Problems, keep a small repository-policy test that asserts the source-watcher skill, site-refresh-orchestrator skill, and cron prompts all contain the scope gate language. This prevents future prompt edits from quietly broadening the site back into general, unexploited vulnerability coverage.
