# Refresh validation debt notes

Session takeaway for Halting Problems refresh runs:

- `pnpm run compile:posts` can succeed even when `pnpm run validate:content` later reports unrelated legacy debt in other posts or shared test fixtures.
- Treat validate failures as blocking only when they are attributable to the new/updated slug, its manifest, its tests/fixtures, or other files created in the current refresh.
- If the candidate post and its research package pass targeted validation, plus `pnpm build` and deploy succeed, record repo-wide validate debt separately rather than discarding the publishable incident.
- Keep stray refresh notes or drafts under `references/` or remove them before the final validation pass so the checker does not trip on root-level leftovers.
