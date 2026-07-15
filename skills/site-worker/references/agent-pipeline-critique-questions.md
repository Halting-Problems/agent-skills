# Agent Pipeline Critique Questions

Use these questions before a candidate can be marked publish-ready. Every final `site_worker_result` must include reviewer answers or a documented reason the question is not applicable.

## Defender Usability

- Can an everyday appsec engineer or SOC analyst understand what to check in under five minutes?
- Does the output provide a short "Should I care?" decision path?
- Does the output list affected assets in machine-readable form before long narrative prose?
- Would the user need to manually clean package names, versions, IOCs, or queries before scripting?
- Are unknowns explicit enough that a user will not mistake missing evidence for absence of risk?

## Package And Artifact Fidelity

- Are package coordinates exact: ecosystem, namespace/scope, name, version, range, fixed version, registry URL?
- Are version ranges valid for the ecosystem named by the post?
- Are hashes labeled with algorithm and artifact identity?
- Are GitHub Actions, containers, browser extensions, IDE extensions, and release artifacts represented with their correct native identifiers?
- Are malicious, suspicious, clean, and fixed artifacts clearly separated?

## IOC Fidelity

- Are raw machine-readable IOCs valid for direct use in scripts?
- Are prose IOCs defanged where required?
- Are domains, URLs, IPs, hashes, emails, wallet addresses, package names, and repository names typed separately?
- Are IOCs tied to evidence and first/last observed timestamps when known?
- Are noisy or low-confidence observables labeled as such?

## Provenance And Evidence

- Does every behavioral claim have linked evidence?
- Does each evidence item include source URL, source type, retrieval timestamp, and confidence?
- Are observed facts separated from inference, hypothesis, and attribution?
- Are artifact/provenance claims backed by registry metadata, release metadata, signing data, builder identity, or source-to-artifact comparison?
- Are primary sources preferred over syndicated summaries?

## SOC And IR Actionability

- Do hunts specify telemetry source, query language, required fields, and time window?
- Do hunts explain what positive, negative, and inconclusive results mean?
- Do detection queries include false-positive guidance?
- Are escalation and closure conditions explicit?
- Are audit commands safe to run and scoped to reader-owned environments?

## Scripts And Fixtures

- Does each script live in `~/hp-posts-info/<slug>/scripts/`?
- Does each script have a matching manifest, fixture, and unit test?
- Does each script embed known incident constants and accept only reader-owned scope inputs?
- Are placeholders such as `OWNER/REPO`, `RUN_ID`, `PACKAGE`, `START_DATE`, and `REPLACE_WITH_*` absent?
- Can the script run in clean and dirty fixture states?

## Remediation

- Are recommendations incident-specific rather than generic rotation advice?
- Are credential rotation steps mapped to actual token types, providers, workflows, registries, or cloud roles?
- Are containment, eradication, recovery, and closure gates present?
- Is the blast radius stated without inventing victim counts or unsupported exposure?
- Are follow-up monitoring windows and recheck commands included?

## Feed, API, And Site Publication

- Does the output write canonical facts to Postgres through the approved import path?
- Does the Next.js API/feed read from canonical Postgres facts while any D1 output remains an explicitly versioned read replica with no fallback authority?
- Does `/api/feed` include valid affected package data and omit malformed entries?
- Does the publication path preserve claim evidence and source mappings?
- Can a downstream user reconstruct why the post was published, rejected, updated, or blocked?
