# Selected production import and research-repo push pattern

Use this when a refresh cron creates local `hp-posts-info/<slug>/` folders and the website code is already deployed with Postgres-backed dynamic routes.

## When this applies

- New or updated research folders already validate locally.
- `pnpm build` and `pnpm run build:cloudflare` pass.
- No website code/schema/importer changes are needed for the new rows.
- Local Postgres import is unavailable or points at a non-running local database.
- Production has the protected `/api/admin/migrate` importer and DB-backed routes.

## Import only the selected slugs

Avoid re-importing every research folder when the cron only changed a small set. Create a temporary script in the website checkout, parse exactly the selected `../hp-posts-info/<slug>` folders with `parsePostInfoFolder()`, POST each parsed post to `https://haltingproblems.com/api/admin/migrate` with `{ action: "import", post }`, then delete the temporary script and secret file.

Before import, set a short-lived `ADMIN_SECRET` with Wrangler and pin production data mode if needed:

```bash
SECRET=$(openssl rand -hex 32)
printf '%s' "$SECRET" | pnpm exec wrangler secret put ADMIN_SECRET
printf 'postgres' | pnpm exec wrangler secret put CANONICAL_DATA_SOURCE
```

Use a browser-like `User-Agent` for verification requests. Treat import success as incomplete until these pass for every slug:

- `/api/health/canonical` shows increased incident/source/script counts.
- `/threat/<slug>` returns `200` and includes the expected CVE/package terms.
- `/api/search?q=<known-term>` returns the slug.
- `/api/feed` contains the entry with affected-package rows and IOC entries.

## Push research folders from a clean worktree

If the active `hp-posts-info` checkout is on a dirty preview branch, use a clean worktree based on `origin/main`, copy only the intended slug folders into it, commit, and push `HEAD:main`. Then verify raw script URLs on `raw.githubusercontent.com/Halting-Problems/hp-posts-info/main/...` return `200` so production threat-page script links are not broken.

After removing the clean worktree, the original preview checkout may still show the same slug folders as untracked. Report that clearly instead of implying the pushed main branch is dirty or unpublished.

## No-deploy case

When only Postgres rows and research-repo content changed, and production dynamic DB-backed routes already serve the new rows, do not force a Cloudflare deploy. Report `website deploy: not run; no website code changes required` and include the production route/API verification evidence.