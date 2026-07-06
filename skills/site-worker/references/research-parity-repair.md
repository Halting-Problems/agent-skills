# Research parity repair workflow

Use this when `pnpm run validate:content` fails because `haltingproblems.com` and the sibling `hp-posts-info` repository disagree after scope pruning, post compilation, or research artifact changes.

## Durable pattern

1. **Use paired clean worktrees.** Create a temporary parent directory containing sibling worktrees named exactly `haltingproblems.com` and `hp-posts-info`. The compiler and D1 sync resolve the research repo as `../hp-posts-info`; a differently named worktree can produce false validation failures or skipped script sync.
2. **Reproduce before changing.** Run `pnpm run validate:content` in the site worktree and summarize failure classes: missing frontend markdown, stale compiled posts, editorial validation, semantic IOC failures, and script-representation failures.
3. **Prune scope at the source.** If generic CVE/KEV posts were removed from the frontend, remove their corresponding directories from `hp-posts-info` too. Otherwise validation keeps expecting frontend Markdown for pruned research slugs.
4. **Compile after research changes.** Run `pnpm run compile:posts` from the site worktree after pruning or editing `hp-posts-info`; this updates frontend Markdown from canonical manifests/scripts.
5. **Validate the whole contract.** Run `pnpm run validate:content`, `pnpm test`, `pnpm check`, and `pnpm build` from the site worktree. `validate:content` should report `Content & Database Validation PASSED`.
6. **Commit both repos deliberately.** Commit and push `hp-posts-info` first for canonical research/artifact changes, then commit and push the regenerated site Markdown.
7. **Deploy and sync D1.** Run `pnpm deploy`, then `pnpm run data:migrate:remote` and `pnpm run data:sync:remote` so `post_scripts` reflects the pruned research repo.
8. **Verify production.** Fetch the homepage, a kept article, the IOC feed, and `/api/scripts?slug=<kept-slug>` plus `/api/scripts?slug=<removed-slug>`. A kept slug should return hunts when applicable; a removed slug should return `hunts: []` and be absent from feeds.

## Pitfalls

- Do not repair parity in dirty primary checkouts; existing local work can be extensive and unrelated.
- Do not call a static Pages deploy enough when script manifests changed. D1 sync is part of parity repair.
- Do not re-add removed CVE/KEV frontend posts just to satisfy validation. If the editorial scope says they are out, prune the research directories instead.
- A Cloudflare Pages fallback may return HTTP 200 for a removed article path; verify the removed slug is absent from the rendered body/feed/API rather than relying only on status code.