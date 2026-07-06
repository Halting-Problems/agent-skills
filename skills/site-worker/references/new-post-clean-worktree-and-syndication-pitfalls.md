# New-post clean worktree and syndication pitfalls

Lessons from the 2026-06-26 cdxgen Maven scanner publication run.

## Isolate dirty working copies before publishing

When the live `haltingproblems.com` or `hp-posts-info` checkouts contain unrelated changes or generated refresh debt, create a clean sibling workspace for publication instead of committing from the dirty tree:

1. Make a temporary parent directory outside either repo.
2. Add detached worktrees for both repos from `origin/main`, preserving the required sibling layout:
   - `<tmp>/haltingproblems.com`
   - `<tmp>/hp-posts-info`
3. Copy only the candidate slug folder into `<tmp>/hp-posts-info/<slug>/` and only the candidate Markdown into `<tmp>/haltingproblems.com/src/content/threat-posts/<slug>.md`.
4. Run focused slug tests from the research repo, then `pnpm run compile:posts`, `pnpm run validate:content`, `pnpm check`, `pnpm test`, and `pnpm build` from the website worktree.
5. If `compile:posts` rewrites many unrelated Markdown files, capture the successful `validate:content` proof while compiled output is present, then restore unrelated frontend churn and keep only the candidate Markdown staged.
6. Re-run `pnpm build` after restoring churn. A whole-repo `validate:content` failure after restore is expected stale-post debt if the candidate remains in-sync and the earlier clean compiled validation passed.

This pattern keeps the commit focused while still proving candidate/research parity.

## Full-fetch deploy verification

Do not decide article verification from a small HTML sample. Some pages place the title or key text after the first few kilobytes. Fetch the full article body and check the `<title>` or slug-specific identifiers before treating a custom-domain deploy as stale.

## Reddit `--max-items 1` with same-day posts

A zero-exit Reddit sync is not proof of syndication. Also, `--max-items 1` may inspect the first feed item only; when multiple posts share the same date, a newly deployed article can appear second and the sync may submit nothing.

Always inspect JSON arrays:
- `submitted_direct_posts`
- `submitted_crossposts`
- `submitted_source_posts`

If all are empty, report "no Reddit post was actually made" even when `errors: []`. If syndication of the specific new article is required, use a targeted/dedupe-aware path or increase selection only after confirming it will not repost older content.
