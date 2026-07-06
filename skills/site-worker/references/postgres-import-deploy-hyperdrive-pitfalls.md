# Postgres import, Cloudflare deploy, and Hyperdrive pitfalls

Use this when importing `hp-posts-info` posts into production Postgres and deploying the Next.js/OpenNext Halting Problems site.

## Remote import path when local `.env.local` is absent

If `pnpm run import:posts:postgres` fails because local `.env.local` or `DATABASE_URL` is unavailable, use the production admin importer instead of falling back to D1/static paths.

1. Ensure production `/api/admin/migrate` exists and is protected by `ADMIN_SECRET`.
2. Rotate or set a temporary strong `ADMIN_SECRET` through Wrangler:
   ```bash
   SECRET=$(openssl rand -hex 32)
   printf '%s' "$SECRET" | pnpm exec wrangler secret put ADMIN_SECRET
   ```
3. Parse `hp-posts-info` folders locally using `parsePostInfoFolder()` and POST each parsed post to:
   ```text
   https://haltingproblems.com/api/admin/migrate
   ```
   with:
   ```http
   X-Admin-Secret: $SECRET
   Content-Type: application/json
   ```
   body:
   ```json
   {"action":"import","post":{}}
   ```
4. Verify `/api/health/canonical` reports the expected `incidentCount`, `sourceDocumentCount`, and `scriptCount`.

## Production must be pinned to Postgres mode

After the Postgres import, verify production has:

```bash
printf 'postgres' | pnpm exec wrangler secret put CANONICAL_DATA_SOURCE
```

Without this, `/api/search` and `/api/feed` can continue serving the legacy/static/D1 path even while `/api/health/canonical` shows Postgres is populated.

## Worker 1101 hung-request triage after Postgres import

If production intermittently returns Cloudflare `error code: 1101` for DB-backed pages or APIs after deploy/import:

1. Run `wrangler tail haltingproblems --format=json` while reproducing the route.
2. If the exception says the Worker was canceled because code hung and there is no application stack trace, suspect stale module-level DB client reuse in the Worker isolate.
3. For the current `src/db/index.ts` pattern, avoid reusing a cached module-level Drizzle/postgres.js client across requests. Create a lightweight client per `getDb()` call and let Hyperdrive pool behind the binding.
4. Re-run `pnpm check`, `pnpm test -- --run`, `pnpm build`, `pnpm run build:cloudflare`, and `pnpm run deploy`.
5. Verify every newly imported `/threat/<slug>`, `/api/search?q=<known-term>`, `/api/feed`, and `/api/health/canonical` using a browser-like `User-Agent`.

## Script-size/rendering guardrail

DB-backed threat pages render the stored script source. Large incident scripts can make Cloudflare Worker responses more fragile and harder to render. If newly imported pages intermittently 1101 or are unusually large:

- Keep hunt scripts complete and incident-specific, but compact nonessential formatting.
- Prefer concise constants and scanner logic over verbose comments or large inline prose.
- Keep deep research notes in `analysis.md` or `references/`, not inside the script body.

## Git/source-link verification

The threat page links scripts to `https://github.com/Halting-Problems/hp-posts-info/blob/main/...`. After importing posts, push the corresponding `hp-posts-info` folders to `main` and verify the raw/main script URLs return `200`; otherwise production pages can show links to scripts that only exist in a local or preview branch.
