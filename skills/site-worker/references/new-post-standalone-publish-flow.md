# Standalone new-post publish flow for Halting Problems

Use this when a queued candidate should become a net-new canonical post rather than an update to an existing slug.

## Decision signals
- Work-order/orchestration state indicates a new incident post or no canonical existing slug.
- The candidate exists only in temp tracking state and does not yet have both:
  - `hp-posts-info/<slug>/`
  - `haltingproblems.com/src/content/threat-posts/<slug>.md`
- Technique overlap with an existing campaign post is suggestive but not strong enough to merge identities.

## Recommended execution order
1. Create the research slug in `hp-posts-info/<slug>/`.
2. Add at minimum:
   - `manifest.yaml`
   - `iocs.json`
   - a hunt script under `scripts/`
   - a targeted pytest under `tests/`
   - minimal clean/dirty fixtures if the hunt test needs them
3. Draft the canonical site post at `src/content/threat-posts/<slug>.md`.
4. Run the narrow test first for the new slug.
5. Run site compilation and full validation:
   - compile research posts
   - validate content parity
   - build the site
6. Deploy only after validation passes.
7. Verify both the article URL and `/api/scripts?slug=<slug>` after deploy.

## Pitfalls learned
- A newly added hunt test can fail because the fixture content does not actually contain the exact selector asserted by the test. Fix the test to match real fixture evidence or add the missing selector to the fixture before rerunning.
- `validate:content` can fail on script lint issues even when the content itself is in sync. Clean small linter problems (for example unused imports) before treating the post as publish-ready.
- Pages preview article routes may return `200` while the preview `/api/scripts` endpoint returns `404`. Treat the production article URL plus the production `/api/scripts` response as the publish verification gate.

## Verification gate
A standalone new post is ready only when all are true:
- targeted slug test passes
- full content validation passes
- full site build passes
- deploy succeeds
- production article URL returns `200`
- production `/api/scripts?slug=<slug>` returns `200` JSON

## Example shape
The `shai-hulululud-ai-scanner-disruption-package` incident followed this pattern successfully: new research slug, new hunt script/tests, compiled canonical post, validated parity, deployed, then verified the production article and script API separately.
