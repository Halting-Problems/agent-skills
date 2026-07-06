---
name: supply-chain-artifact-diff-lab
description: Use when verifying artifact-level claims by comparing malicious and known-good package, container, extension, GitHub Action, or release artifacts.
---

# Supply Chain Artifact Diff Lab

## Mission

Reproduce and verify artifact-level claims. This skill answers what changed, how execution triggers, what durable indicators exist, and whether the published artifact matches the expected source.

## When To Use

Use for npm, PyPI, Composer, Go, Rust, VSIX, container images, GitHub Actions, release archives, and suspicious binary or script artifacts.

## Required Output

```yaml
artifact_diff:
  artifact_identity:
    ecosystem: ""
    registry: ""
    name: ""
    suspicious_version_or_ref: ""
    known_good_version_or_ref: ""
  collection_commands: []
  hashes: []
  size_delta: ""
  changed_manifest_fields: []
  new_files: []
  removed_files: []
  modified_files: []
  execution_trigger: "unknown"
  payload_behavior: []
  provenance:
    present: null
    verified: null
    issuer: "unknown"
    identity: "unknown"
    workflow_ref: "unknown"
  source_match:
    expected_source_ref: "unknown"
    registry_artifact_matches_source: null
    notes: ""
  confidence: "low|medium|high"
  analyst_notes: []
```

## Rules

- Never claim malicious behavior from package name alone.
- Treat artifact hash, file path, manifest field, version, digest, tag, and commit SHA as durable evidence.
- Preserve commands that let another analyst reproduce the collection.
- Separate artifact facts from behavioral inference.
