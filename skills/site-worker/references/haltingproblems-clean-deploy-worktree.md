# Halting Problems clean deploy pattern

Use this when Sam asks to deploy one logical change while the main checkout contains unrelated dirty work.

## Pattern

1. Inspect the main checkout enough to identify the intended logical change.
2. Create a temporary worktree from `origin/main`, e.g. `/home/sam/haltingproblems-<topic>-deploy`.
3. Apply or recreate only the intended files in that worktree.
4. Run the normal validation path in the worktree:
   - focused test(s) for the change
   - `pnpm openspec:validate` when specs changed
   - `pnpm test`
   - `pnpm check`
   - `pnpm build`
5. Commit from the clean worktree and push `HEAD:main`.
6. Run `pnpm build:cloudflare` before deploying. `pnpm deploy` can reuse a stale `.open-next` bundle and ship the previous route set even after a successful push.
7. Run `pnpm deploy` from the clean worktree.
8. Verify production URLs, not just the Pages preview URL. If a newly-added route still returns the old result (for example `404`), rebuild with `pnpm build:cloudflare` and redeploy before debugging application code.
9. Remove the temporary worktree when done.

## Why

This avoids accidentally shipping unrelated local changes from `/home/sam/halting-problems/repos/haltingproblems.com` while still letting the user move quickly.

## Verification examples

- For analytics changes: fetch production HTML and check `GTM-W2NH68H2` is present while `googletagmanager.com/gtag/js` is absent.
- For content removals: verify removed slugs do not appear in rendered body or `/feed/iocs.json`.
- For post edits: fetch the affected `/analysis/<slug>/` production page and check the edited section is present.
