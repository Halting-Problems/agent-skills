# Halting Problems coverage scope policy

Use this when pruning or validating whether Halting Problems should publish a post.

## Editorial scope

Halting Problems focuses on software supply-chain security attacks and adjacent systems, as well as noteworthy exploited vulnerabilities (CVEs/KEVs) and zero-days with active exploitation in the wild. Generic or unexploited vulnerabilities are out of scope.

In-scope examples:
- package compromise, registry abuse, dependency confusion, typosquatting, malicious packages
- maintainer or publishing account compromise
- GitHub Actions, CI/CD, OIDC, build-system, release, or provenance compromise
- signed installer or artifact tampering
- IDE/plugin/extension compromise and developer-tooling malware
- content supply-chain compromise where the compromised system distributes malicious content to users
- noteworthy exploited vulnerabilities (CVEs/KEVs) and zero-days with active exploitation in the wild
- CVE/KEV posts carrying exception tags such as `cisa-kev`, `kev`, `vulnerability`, `exploited-vulnerability`, `cve`, `supply-chain`, `content-supply-chain`, `package-compromise`, `repository-compromise`, `github-actions`, `ci-cd`, `signed-malware`, `developer-workstations`, or `developer-endpoints`

Out-of-scope examples:
- generic, unexploited vulnerabilities (i.e. those without active exploitation in the wild)
- ordinary network appliance, OS, browser, VPN, web-app, or product CVEs that are not subject to active exploitation or zero-day abuse
- standard patch advisories without active exploitation in the wild or supply-chain context

## Recommended enforcement pattern

A repository-policy test should evaluate `../hp-posts-info/<slug>/` event profiles together with canonical Postgres incidents:
- parse event-profile titles, tags, affected assets, and exploitation evidence
- compare candidate identities with imported incident and campaign records
- flag CVE or KEV candidates that lack a qualifying supply-chain or exploited-vulnerability basis
- allow them only when the evidence and explicit scope tags satisfy this policy

This approach would catch authoring/import drift before the Next.js application serves an incident.

## Workflow

1. Start an OpenSpec change for scope/pruning work.
2. Write the failing coverage-scope test first.
3. Mark generic CVE/KEV event profiles as rejected and prevent their Postgres import.
4. Keep only event profiles with explicit supply-chain or exploited-vulnerability evidence and exception tags.
5. Run `pnpm test`, `pnpm check`, `pnpm build`, `pnpm run import:posts:postgres:dry-run`, and `pnpm openspec:validate`.
6. Archive the OpenSpec change so the coverage rule remains source-of-truth.

## Caveat

If a CVE/KEV post is borderline, do not keep it if it does not involve either a software supply chain angle or active exploitation in the wild (such as being on CISA's KEV catalog or documented in-the-wild zero-day activity). Explicit tags must be used to declare the scope exception.
