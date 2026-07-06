# Dev preview pattern for unmerged Halting Problems refreshes

Use this when Sam asks for a dev/preview page but explicitly says not to publish `haltingproblems.com` production.

## Pattern used successfully

1. Keep production untouched: work on a preview branch in both repos, e.g. `preview/last-two-weeks-supply-chain-refresh`.
2. Verify locally before exposing a preview:
   - `pnpm check`
   - `pnpm test`
   - `pnpm exec tsx scripts/import-posts-info-to-postgres.ts --posts-info-dir ../hp-posts-info --dry-run`
   - `pnpm build`
3. Check whether a built Next app is already serving port 3000 before starting another one:
   - `ss -ltnp 'sport = :3000' || true`
   - If `pnpm start` fails with `EADDRINUSE`, do not treat that as preview failure; verify the existing listener with `curl -I http://127.0.0.1:3000/` and reuse it if it serves the current checkout.
4. Start the built Next app locally when no listener exists:
   - `pnpm start`
5. Expose it with a temporary tunnel rather than a production deploy:
   - `npx --yes localtunnel --port 3000 --subdomain <descriptive-preview-name>`
   - If the requested subdomain exits immediately or begins returning 408s/503s, check for old tunnel processes with `ps -ef | grep -E 'localtunnel|next-server|next start' | grep -v grep` before starting yet another tunnel.
   - Localtunnel may keep running outside the current Hermes process registry; trust `ss`/`ps`/HTTP verification over `process list` alone.
6. Verify the preview with real HTTP checks:
   - `curl -I <url>/` should return `200 OK`.
   - `curl <url>/api/search?q=<known-term>` should return expected JSON.
   - `curl <url>/threat/<known-slug>` should contain the expected article title.
7. Report the preview URL as temporary and dev-only.

## Cloudflare Pages caveat

`wrangler.jsonc` may point Pages at `dist`, but this Next app builds to `.next` unless a compatible Pages adapter is used. `@cloudflare/next-on-pages` may require every non-static route to export `runtime = 'edge'`; adding that can break this app if shared data modules import Node/Postgres dependencies such as `postgres`, `net`, `tls`, `stream`, or `perf_hooks`. Do not keep Edge-runtime patches solely to satisfy Pages if they break `pnpm build`.

When the goal is only a dev review page, a verified localtunnel preview is safer than forcing a production-style Cloudflare Pages deployment through unrelated runtime migration work.

## Content/data preview note

Branch previews need a preview Postgres database loaded from the intended `hp-posts-info` checkout. Do not add or refresh Next app mock incident fallback data; otherwise preview/search/detail pages can mask missing imports and drift from the production data flow.
