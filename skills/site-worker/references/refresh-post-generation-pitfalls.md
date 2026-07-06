# Refresh post-generation pitfalls

Captured from the June 2026 site refresh pass.

## Lessons learned

- `pnpm run compile:posts` rebuilds the site from all available `hp-posts-info` manifests. If a candidate is briefly represented by an extra markdown draft or campaign-only article that should not ship, remove the stray file before the final validation pass and re-run the compiler so the site and generated research packets stay aligned.
- Prefer one canonical article slug per incident. Only introduce a separate campaign-level post when the source-watcher or direct evidence establishes a real parent/child relationship.
- For June 2026 refreshes, the working pattern that validated cleanly was: create the research packet, compile the post, remove any accidental duplicate draft, then run `pnpm run validate:content`, `pnpm build`, and `pnpm deploy`.
- `validate:content` also checks whether each slug's manifest scripts actually reference the IOC values declared in `iocs.json`. For refresh work, make sure domains, URLs, package versions, and file-path patterns appear in the script constants and are used by the scan logic, not just listed in JSON.
- If the refresh workflow needs a session note or research memo, place it under `references/` and avoid leaving a `research.md` at the slug root. The validator treats that as an unexpected top-level file.

## Why this matters

Duplicate or provisional markdown files can create confusing slug collisions and leave the website in a state that is technically buildable but semantically inconsistent with the research repository.
