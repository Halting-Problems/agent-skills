---
name: provenance-and-publishing-integrity-auditor
description: Use when verifying whether a package, container, GitHub Action tag, release, or artifact was produced by the expected source, workflow, builder, and signing identity.
---

# Provenance And Publishing Integrity Auditor

## Mission

Answer whether the artifact should be trusted based on tag, source, builder, provenance, signature, and registry evidence.

## Required Output

```yaml
publishing_integrity:
  artifact:
    ecosystem: ""
    name: ""
    version_or_ref: ""
  source_repository: ""
  tag:
    expected: ""
    current_sha: ""
    known_good_sha: ""
    moved: null
    reachable_from_default_branch: null
    signed: null
  provenance:
    present: null
    verified: null
    type: "npm|pypi|sigstore|slsa|in-toto|gpg|unknown"
    issuer: "unknown"
    identity: "unknown"
    workflow_ref: "unknown"
    builder: "unknown"
  registry:
    publish_time: "unknown"
    publisher: "unknown"
    dist_tag_changed: null
  suspicious_reasons: []
  verification_commands: []
```

## Rules

- Distinguish missing provenance from failed provenance.
- Check if tag target is reachable from default branch.
- Check whether the package artifact matches source release when possible.
- Treat mutable tags as high-risk in CI/CD trust chains.
