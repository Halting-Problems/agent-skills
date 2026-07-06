# Agency frontend UX review implementation pattern

Use this when Sam asks to use Agency Agents to review the Halting Problems frontend, design, UX, accessibility, or conversion flow.

## Agency routing

Use Agency Agents as specialists, then implement the findings rather than only summarizing them. Good review lanes:

- `ui-designer`: visual hierarchy, typography, spacing, component polish, responsive layout.
- `ux-architect`: information architecture, defender/researcher user journeys, action paths, table ergonomics, CTAs.
- `accessibility-auditor`: WCAG 2.2 AA, keyboard/focus, contrast, screen-reader status messages, table semantics, reduced motion.
- `frontend-developer`: component boundaries, performance, maintainability, testability.

Dispatch independent lanes in parallel when possible, then merge findings into a prioritized implementation backlog.

## Halting Problems UX defaults

For threat detail pages, prioritize defender action over raw dossier completeness:

1. Above-the-fold defender action panel: affected?, immediate action, hunting availability, top IOCs, and quick links.
2. In-page TOC for Summary, Analysis, Timeline, Affected Software, IOCs, Hunting Scripts, Sources.
3. Progressive disclosure for internal research metadata, provenance-heavy blocks, and large scripts.
4. Keep IOC clipboard and tested scripts prominent, copyable, and keyboard-accessible.
5. Do not expose internal pipeline details like source-watcher/dedupe queues as first-class public content unless collapsed as research metadata.

For homepage/dashboard UX:

- Show result count and active filters.
- Normalize ecosystem labels (`npm`, `GitHub Actions`, `Open VSX`, `JetBrains Marketplace`, `Multi-ecosystem`).
- Add severity filters and clear-filter affordance.
- Include operational metadata on cards: signals, last updated, hunting/script availability.
- Add docs/IA routes for `Feed/API` and `Methodology` when the nav points to those values.

## Accessibility fixes that came up

- Use a darker readable link token on light backgrounds; cyan `#06b6d4` on white fails contrast.
- Make scrollable `<pre>` blocks focusable with `tabIndex={0}` and an accessible label.
- Add strong visible focus styles with at least 3:1 contrast.
- Add `role="group"` to export button groups or use semantic grouping.
- Add table captions/`aria-labelledby`, `scope="col"`, and row headers where the first column identifies rows.
- Add `role="status" aria-live="polite"` to subscription/status messages and `aria-invalid` on form errors.
- Add `prefers-reduced-motion: reduce` overrides for smooth scrolling/transitions.
- Add screen-reader text for `target="_blank"` links: “opens in a new tab”.
- Add mobile wrapping rules (`overflow-wrap: anywhere`, `min-width: 0`) for markdown, inline code, long package names, hashes, and table cells while keeping tables/code horizontally scrollable.

## Verification contract

Before claiming this class of UX work is complete:

```bash
pnpm check
pnpm test -- --run
pnpm build
pnpm run build:cloudflare
pnpm run deploy
npx --yes @axe-core/cli https://haltingproblems.com --tags wcag2a,wcag2aa,wcag22aa
npx --yes @axe-core/cli https://haltingproblems.com/threat/<representative-slug> --tags wcag2a,wcag2aa,wcag22aa
```

Also verify live routes with browser-like `User-Agent`:

- `/`
- `/feed/` if touched
- `/methodology/` if touched
- `/threat/<representative-slug>`
- `/api/health/canonical`
- `/api/feed`

For production threat-page UX changes, explicitly confirm the rendered page contains the new action panel/TOC/disclosure affordances and that axe returns `0 violations` for homepage and representative threat page.
