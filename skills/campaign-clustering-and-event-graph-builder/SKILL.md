---
name: campaign-clustering-and-event-graph-builder
description: Use when deciding whether incidents should be standalone posts, children of a parent campaign, or kept separate due to weak correlation.
---

# Campaign Clustering And Event Graph Builder

## Mission

Build evidence-weighted event graphs without over-merging incidents.

## Correlation Levels

- hard: same unique payload hash, C2 domain, exfil repo pattern, compromised account, source-confirmed campaign, rare persistence path
- moderate: similar trigger, ecosystem, credential targets, obfuscation
- weak: similar dates, same broad ecosystem, generic malware family, shared hosting

## Required Output

```yaml
campaign_graph:
  parent_campaign_id: "none"
  child_events: []
  shared_indicators: []
  shared_payloads: []
  shared_infrastructure: []
  shared_publishing_paths: []
  shared_victimology: []
  evidence_for_linking: []
  evidence_against_linking: []
  alternative_hypotheses: []
  confidence: "low|medium|high"
  decision: "campaign|related_events|separate"
```

## Rules

- Do not group incidents on dates alone.
- Do not group incidents on package ecosystem alone.
- Require at least two hard signals, or one hard signal plus a direct/primary source.
