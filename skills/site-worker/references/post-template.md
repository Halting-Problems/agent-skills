# [Threat Post Title]

---
layout: ../../layouts/ThreatPostLayout.astro
title: "[Threat Post Title]"
date: YYYY-MM-DD
slug: [slug]
description: "Brief, high-impact summary of the threat post."
ecosystem: [ecosystem-name]
---

## Executive Summary

Provide two or three sourced paragraphs covering the affected artifact, malicious version or reference, execution trigger, primary impact, exposure window, and the immediate responder decision.

## Key Facts

| Fact | Value |
| --- | --- |
| **Affected Artifact** | [e.g. package-name] |
| **Ecosystem** | [e.g. npm, pypi, github-actions] |
| **Malicious Versions** | [e.g. 1.2.3, 1.2.4] |
| **Exposure Window** | [e.g. YYYY-MM-DD to YYYY-MM-DD] |
| **Immediate Action** | [e.g. Contain compromised instances, rotate credentials] |

## Evidence Assessment

Prose or a claims table distinguishing confirmed, likely, unclear, not observed, and disputed behaviors.
Each entry must identify what the cited source proves. Do not repeat long IOC or affected-package lists that appear later.

## Impact Determination

| Exposure Classification | Criteria | Required Evidence | Required Action | Closure Gate |
| --- | --- | --- | --- | --- |
| **Confirmed Compromise** | [e.g. Script ran with root privileges] | [e.g. Presence of files in /sys/fs/bpf] | [e.g. Revoke and rotate all AWS and NPM credentials] | [e.g. Negative scan on all endpoints, IAM logs audit] |

## Minimum Evidence To Collect

Use prose bullets. Each bullet must explain:
- **What to collect**: (e.g. NPM caches, specific log files)
- **Where it normally comes from**: (e.g. `~/.npm/_cacache`)
- **Why it is relevant**: (e.g. contains the exact SHA-1 of the fetched payload)
- **Which exposure classification or response decision it resolves**

## Timeline

A sourced chronological list. Mark unknown or approximate timestamps explicitly.
- **YYYY-MM-DD HH:MM:SS UTC**: Observed activity / package published.
- **YYYY-MM-DD HH:MM:SS UTC**: Public advisory or vendor alert.

## What Happened

Give a short end-to-end narrative of the compromise.

## Technical Analysis

Provide explanatory prose under applicable subsections. Small artifact/IOC blocks are allowed only when meant to be parsed.
*Important: Recommendations, rationale, impact, exfiltration explanation, and remediation must not be encoded as JSON or YAML.*

### Initial Access
Explain how the compromised package was introduced or hosted.

### Execution Trigger
Explain how the malicious payload gets triggered.

### Payload Behavior
Detail what the payload does upon execution.

### Credential or Data Collection
Detail which credentials or data the malware collected.

### Defense Evasion
Detail how the malware attempted to bypass security detections.

### Exfiltration and Command and Control
Explain the exfiltration channel and C2 infrastructure.

## Affected Assets and Blast Radius

Explain the exposure path in prose, then use a concise table for affected artifacts, environments, identities, and downstream systems. Do not publish an internal `affected_assets` schema as the analysis.

## Indicators of Compromise

A table or machine-readable block containing only observed, sourced selectors (hashes, domain/IPs, file paths, etc.). Do not emit empty categories.

## Detection and Hunting

Publish incident-specific, single-responsibility hunts. Omit scripts if evidence cannot support a useful collector.
Include a link to the corresponding tested script in `hp-posts-info` and explain:
- The specific question the script answers
- Required telemetry sources
- Positive signal on compromise
- Expected false positives
- Escalation path on match

## Downstream Abuse Audits

Include only platforms demonstrably exposed by the incident. Explain why the identity/service is at risk before presenting a collector.

## Remediation and Closure

Use an ordered, human-readable response sequence. All remediations must be prose-driven and threat-specific, explaining the rationale for each step:
1. **Preserve evidence**: (e.g. clone target volume, save caches)
2. **Stop active execution**: (e.g. terminate target processes)
3. **Contain affected assets and identities**: (e.g. isolate nodes, disable IAM users)
4. **Revoke and rotate credentials**: (e.g. rotate compromised tokens)
5. **Eradicate malicious artifacts and persistence**: (e.g. remove cron/systemd entries)
6. **Rebuild untrusted systems**: (e.g. redeploy clean container images)
7. **Audit downstream activity**
8. **Recover using verified artifacts**
9. **Close**: Close only when evidence-backed gates are satisfied.

## Sources

1. **Source Name**: Role/description, claims supported, and limitations.
