# D1 sync failure with otherwise successful static deploy

Use this when a new Halting Problems article builds and deploys, but Cloudflare D1 migration/sync fails before `post_scripts` is populated.

## Durable lesson

Static Pages deployment and dynamic script availability are separate gates. A post can return HTTP 200 while `/api/scripts?slug=<slug>` returns `{"hunts": []}` because `pnpm run data:migrate:remote` or `pnpm run data:sync:remote` failed.

## Handling pattern

1. Run the normal candidate-specific checks first: focused `hp-posts-info/<slug>/tests`, `pnpm run compile:posts`, `pnpm run validate:content`, `pnpm check`, `pnpm test`, and `pnpm build` as applicable.
2. Run remote D1 migration/sync from the website checkout with `../hp-posts-info` present.
3. If D1 migration/sync fails for authorization/account/configuration reasons but the static build and deploy succeed:
   - Do not call the article fully `publish_ready`.
   - Classify the final site-worker result as `needs_review` or equivalent partial-publish state.
   - Verify and report both article URL status and `/api/scripts?slug=<slug>` status.
   - Explicitly state that dynamic hunt loading is blocked and that `/api/scripts` returned empty hunts if observed.
4. If the user explicitly required syndication after any successful new-post deploy, still run the configured syndication step after the static deploy succeeds, then report that dynamic script loading remains blocked.

## Reporting language

Use wording like:

- `Static article deployed and verified HTTP 200.`
- `D1 sync failed, so /api/scripts?slug=<slug> currently returns hunts: [] and dynamic script loading is not publish-ready.`
- `Recommended next action: fix D1 credentials/account access, rerun data:migrate:remote and data:sync:remote, then re-verify /api/scripts.`

Do not bury the D1/API gap under a generic deploy success line.
