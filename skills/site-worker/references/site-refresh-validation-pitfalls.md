# Site refresh validation pitfalls

Captured from the June 2026 Cisco/LiteSpeed refresh workflow.

## What the validators enforced

- `pnpm run validate:content` rejected posts whose **Technical Analysis** paragraphs had citations only in nearby prose or link text. The safe pattern is to end each claim-heavy analytical paragraph with an explicit citation marker like `[1]` in addition to inline links.
- The research-repo IOC test expects `affected_assets.packages` to contain **canonical package names**, while `iocs.package_versions` carries the versioned constraints. If `affected_assets.packages` includes versioned strings such as `Foo < 1.2.3`, the prefix-matching test fails.
- `sourceCount` must match the numbered source entries in the post frontmatter/body contract.
- Network IOCs should be defanged in prose, but machine-readable blocks may preserve raw values when required by the schema.

## Practical sequence

1. Edit the markdown or JSON profile.
2. Run `pnpm run validate:content` in the website repo.
3. If validation fails, patch the exact failing paragraph or schema field instead of rerunning unchanged.
4. Re-run the validator until it passes, then commit and push.
