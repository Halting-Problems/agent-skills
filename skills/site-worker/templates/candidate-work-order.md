# Candidate site-worker work order

Work on exactly one candidate. Follow `skills/site-worker/SKILL.md` and the repository instructions.

## Hard boundaries

- Posts-info repository: `{{POSTS_INFO_DIR}}`
- Website repository: `{{WEBSITE_DIR}}`
- Required target slug: `{{TARGET_SLUG}}`
- Allowed website paths: `{{ALLOWED_WEBSITE_PATHS_JSON}}`
- For `update_existing` or `attach_to_campaign`, update only the required existing slug. Never create a folder named from the follow-up candidate ID.
- Never write outside the target slug directory or the explicitly allowed website paths.
- Return only the JSON object required by the supplied output schema.
- Report every changed path as an absolute path.

## Required source-version binding

When creating or updating `<slug>/event_profile.json`, preserve the candidate identity exactly:

- `source_item_key` = candidate `sourceItemKey`
- `source_version_hash` = candidate `sourceVersionHash`
- `source_version_at` = candidate `firstSeenAt`

Do not invent, recompute, or silently omit these values. Generate the modular site-worker plan from that bound event profile, and treat any mismatch as a publication blocker.

## Candidate

```json
{{CANDIDATE_JSON}}
```
