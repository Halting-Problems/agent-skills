# Static publish when D1 script sync is not ready

Use this note when a new Halting Problems post has a publishable static article and tested `~/hp-posts-info/<slug>/` hunt content, but `/api/scripts?slug=<slug>` still returns `hunts: []` after deploy.

## Durable workflow lessons

1. **Do not call the result fully `publish_ready`.** Treat it as a partial/static publish and set the site-worker decision to `needs_review` until D1 `post_scripts` contains the tested hunts.
2. **Still verify the static article.** Fetch both the Pages preview URL and the custom-domain article URL with a browser-like `User-Agent`; record HTTP status.
3. **Verify the API separately.** Fetch `/api/scripts?slug=<slug>` on preview and custom domain. If the response is HTTP 200 with `hunts: []`, state that dynamic script loading is not ready.
4. **Avoid destructive D1 sync.** Only run `data:sync` or `data:sync:remote` from a checkout where `../hp-posts-info` is present and contains the intended slug manifests/scripts. Syncing without the sibling research repo can empty or omit `post_scripts`.
5. **Final report wording:** say “static article published; dynamic script/API loading still needs review,” include the exact API response summary, and recommend remote D1 migrate/sync followed by another `/api/scripts?slug=<slug>` check.

## Validation evidence to keep

- focused slug pytest output from `~/hp-posts-info/<slug>/tests/`
- `pnpm run compile:posts` proof that the candidate slug was compiled from the manifest
- `pnpm run validate:content` result; distinguish candidate failures from unrelated repo-wide validation debt
- `pnpm check` and `pnpm build` from the final publish worktree
- deploy URL and commit SHA
- Reddit JSON only if a new article was published; zero exit is insufficient unless submitted arrays are non-empty
