# Postgres subscriber migration and Next.js signup

Use when moving Halting Problems newsletter/subscriber capture from legacy Cloudflare D1/Functions into the Next.js/OpenNext + Hyperdrive/Postgres path.

## Durable pattern

1. Add a Postgres `subscribers` table matching the legacy D1 fields before switching the signup endpoint:
   - `email text primary key`
   - `created_at timestamptz default now()`
   - `updated_at timestamptz default now()`
   - `source text default 'site'`
   - `status text default 'subscribed' check(status in ('subscribed','unsubscribed'))`
   - `ip_hash text default ''`
   - `user_agent text default ''`
   - index: `(status, created_at desc)`
2. Add the Drizzle schema export and a migration file under `migrations-postgres/`.
3. Implement a Next.js App Router endpoint at `/api/subscribe` that:
   - accepts only JSON `POST`
   - validates and lowercases email
   - hashes `cf-connecting-ip` / `x-forwarded-for` when present
   - truncates user-agent to the legacy limit
   - upserts `status='subscribed'` on email conflict
   - returns `405` for unsupported methods and `400` for invalid email
4. Add a client subscribe component to the Next.js homepage. Verify the homepage HTML contains the form marker after deploy.
5. If local direct Postgres access is unavailable, extend the protected `/api/admin/migrate` route with a narrow subscriber migration action, deploy it, then POST the D1 rows to production through the same temporary `ADMIN_SECRET` pattern used for post imports.
6. After migration, verify through production, not just local tests:
   - homepage returns `200` and contains `data-subscriber-form`
   - `/api/subscribe` rejects invalid email with `400`
   - posting an existing known test subscriber returns `200` without increasing row count
   - protected admin/count path reports expected total/subscribed rows
   - `/api/health/canonical` still reports Postgres as canonical for CTI data

## D1 export command

```bash
pnpm exec wrangler d1 execute haltingproblems-data --remote \
  --command "SELECT email, created_at, updated_at, source, status, ip_hash, user_agent FROM subscribers ORDER BY created_at" \
  --json
```

Parse the JSON result and send only those fields to the production admin migration action. Do not print or share subscriber email lists in final user-facing summaries unless explicitly requested.

## Pitfalls

- The legacy `/functions/api/subscribe.ts` can exist in the repo while the deployed OpenNext app returns `404`; implement the App Router endpoint instead of assuming Functions routes are active.
- A broad `wrangler tail` watch on the literal JSON key `exceptions` is noisy because it matches `"exceptions": []`; watch for specific non-empty error text or inspect tail logs manually.
- Deploy success is not enough: subscriber migration needs a row-count verification from production Postgres.
