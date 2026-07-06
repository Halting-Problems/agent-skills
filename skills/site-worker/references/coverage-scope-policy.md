# Halting Problems coverage scope policy

Use this when pruning or validating whether Halting Problems should publish a post.

## Editorial scope

Halting Problems should stay focused on software supply-chain security attacks. Generic CVE/KEV vulnerability posts are out of scope unless the writeup is specifically about a supply-chain compromise or an adjacent system that materially affects software delivery.

In-scope examples:
- package compromise, registry abuse, dependency confusion, typosquatting, malicious packages
- maintainer or publishing account compromise
- GitHub Actions, CI/CD, OIDC, build-system, release, or provenance compromise
- signed installer or artifact tampering
- IDE/plugin/extension compromise and developer-tooling malware
- content supply-chain compromise where the compromised system distributes malicious content to users
- CVE/KEV only when explicitly framed by supply-chain tags such as `supply-chain`, `content-supply-chain`, `package-compromise`, `repository-compromise`, `github-actions`, `ci-cd`, `signed-malware`, `developer-workstations`, or `developer-endpoints`

Out-of-scope examples:
- ordinary network appliance, OS, browser, VPN, web-app, or product CVEs
- broad KEV roundup posts
- generic exploited-vulnerability coverage without package, build, artifact, registry, CI/CD, developer-tooling, or content-supply-chain impact

## Tested enforcement pattern

A useful repository-policy test is `tests/unit/coverage-scope.test.ts`:
- recursively scan `src/content/**/*.md`
- parse frontmatter title and tags
- flag posts whose slug/title/tags indicate CVE or KEV
- allow them only when they carry explicit supply-chain exception tags

This catches both `src/content/threat-posts/` and generic `src/content/blog/` KEV drift.

## Workflow

1. Start an OpenSpec change for scope/pruning work.
2. Write the failing coverage-scope test first.
3. Remove generic CVE/KEV Markdown entries from `src/content/`.
4. Keep only CVE/KEV posts with explicit supply-chain exception tags.
5. Run `pnpm test`, `pnpm check`, `pnpm build`, and `pnpm openspec:validate`.
6. Archive the OpenSpec change so the coverage rule remains source-of-truth.

## Caveat

If a CVE/KEV post is borderline, do not keep it because the body vaguely mentions build hosts or credentials. Require explicit supply-chain metadata and a clear supply-chain analysis angle.