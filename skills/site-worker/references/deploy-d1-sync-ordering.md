# Deploy and D1 Sync Ordering Notes

When publishing Halting Problems posts from a clean worktree, the static article deploy and D1 script publication are separate success paths.

## Durable pattern

1. Run `pnpm check` and `pnpm build` in the clean publish worktree before committing.
2. Commit and push only the intended post markdown changes.
3. Apply remote D1 migrations with `pnpm run data:migrate:remote`.
4. Deploy the static site with `pnpm deploy`.
5. Run `pnpm run data:sync:remote` after confirming the sibling `../hp-posts-info` checkout is present.
6. Verify both article URLs and `/api/scripts?slug=<slug>` for every changed post before calling the run fully publish-ready.

## Important distinction

A successful Cloudflare Pages deploy proves the static article is live; it does not prove the reviewed `hp-posts-info` scripts were loaded into D1. If deploy succeeds before D1 sync, finish the remote sync and API verification immediately. If sync or API verification fails, report a partial/static publish rather than `publish_ready`.

## Reporting nuance

`pnpm run validate:content` can exit non-zero for unrelated repo-wide stale posts or unrelated research-repo pytest failures. Do not bury that failure, but separate it from candidate-specific evidence. Record whether each candidate slug was explicitly reported as valid/in-sync and whether its focused script tests, build, D1 sync, and API verification passed.