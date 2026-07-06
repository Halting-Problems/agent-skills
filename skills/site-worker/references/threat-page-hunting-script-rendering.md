# Threat page hunting-script rendering pitfalls

Use this when importing `hp-posts-info` scripts into Postgres and rendering DB-backed threat detail pages.

## Duplicate script-section failure mode

`hp-posts-info` analysis prose can include a section whose heading starts with `Hunt Manifest:` while the importer also stores canonical tested scripts in `threat_scripts`. If the Next threat page renders both unfiltered analysis sections and `threat_scripts`, the public page shows two hunting-script areas:

1. a manifest-like hunting section inside `Analysis`, and
2. the canonical `Tested Hunting Scripts` section.

This makes the page look duplicated and pushes users through internal pipeline material before the tested script workflow.

## Rendering rule

For public threat pages, keep `threat_scripts` as the canonical tested-script surface and filter imported analysis sections whose heading matches `^Hunt Manifest:` from the default Analysis flow. If the metadata is useful, expose it inside the tested-script component or a collapsed research-metadata panel, not as a second article section.

## Formatting rule

Tested script source should use the same styled script-card classes as the threat page design system, not an unstyled/shiki-only wrapper. Code blocks that can horizontally scroll must be keyboard focusable and have a visible focus state.

Recommended checks:

- Representative page has no `analysis-section` with `Hunt Manifest:` heading.
- Page still has exactly one visible `Tested Hunting Scripts` section.
- Script code uses styled classes such as `.td-script-card` and `.td-script-card__pre`.
- Axe does not report `scrollable-region-focusable` for script `<pre>` elements.
