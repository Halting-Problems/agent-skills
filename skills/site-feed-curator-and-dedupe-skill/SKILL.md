---
name: site-feed-curator-and-dedupe-skill
description: Use when deciding whether a candidate finding should become a new post, update an existing post, attach to a campaign, or be rejected.
---

# Site Feed Curator And Dedupe Skill

## Mission

Protect the feed from duplicates, weak incidents, and accidental campaign over-merging.

## Required Output

```yaml
feed_decision:
  action: "new_post|update_existing|attach_to_campaign|reject|needs_review"
  matched_existing_posts: []
  dedupe_keys: []
  parent_campaign_id: "none"
  child_event_id: ""
  reason: ""
  required_updates: []
  canonical_slug: ""
```

## Decision Rules

- `new_post`: new package/artifact/campaign with enough direct or primary evidence.
- `update_existing`: same event has new timeline, IOCs, remediation, or source status.
- `attach_to_campaign`: child event has hard correlation to existing campaign.
- `reject`: no supply-chain compromise angle (unless it has massive, large-scale impact on major libraries with millions of downloads) or no direct/primary evidence.
- `needs_review`: source conflict, missing version, or unclear blast radius.
