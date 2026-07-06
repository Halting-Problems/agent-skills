---
name: cloud-oidc-and-ci-cd-abuse-hunter
description: Use when GitHub Actions, OIDC, cloud credentials, CI/CD tokens, or deployment credentials may have been exposed or abused.
---

# Cloud OIDC And CI/CD Abuse Hunter

## Mission

Map CI/CD exposure to downstream cloud, registry, and source-control activity.

This skill must pivot from token issuance to follow-on API activity.
Output must be runnable audit scripts with exact event windows, exact workflow/action/package selectors, exact cloud audit event names, and dynamic enumeration of run IDs, session IDs, access keys, package versions, and releases.

## Required Audit Flow

1. Identify affected workflow runs.
2. Extract repository, ref, actor, workflow, job, environment, permissions, and `id-token` scope.
3. Identify cloud trust relationships.
4. Query token/federation issuance.
5. Extract session identity or temporary key.
6. Pivot to follow-on API calls.
7. Flag write, deploy, IAM, secret, registry, and release activity.
8. Define remediation and closure.

## Script Requirements

- Use exact exposure windows from the incident profile; do not require `START_DATE`, `SINCE`, or `UNTIL` as reader input.
- Require only reader-specific scope values such as `ORG`, `REPOS_FILE`, `AWS_PROFILE`, `AZURE_SUBSCRIPTION_ID`, and `GCP_PROJECT_ID`.
- Query GitHub runs with `gh api` or `gh run view` and loop over returned run IDs; never emit `RUN_ID`.
- Query token exchange events first, then pivot to returned access key, session, principal, or subject IDs for follow-on API activity.
- Write JSONL outputs for token issuance, follow-on API calls, release/package writes, secret changes, workflow changes, and deployment changes.
- Include positive-signal and remediation-trigger comments in each script.
- Return `needs_review` instead of a script when exact incident values are missing.

## Platforms

- GitHub
- AWS
- Azure
- GCP
- GitHub Packages and GHCR
- Kubernetes
- Terraform or HCP Terraform
- CDN or edge providers
