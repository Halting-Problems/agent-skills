---
name: detection-pack-generator
description: Use when turning event profiles, IOCs, and behaviors into portable KQL, SPL, Sigma, YARA, osquery, GitHub, and cloud detection packs.
---

# Detection Pack Generator

## Mission

Produce detection content tied to exact IOCs and behaviors.
Generated detections must be ready to run. Do not emit a schema-only detection pack when the requested output is a post handling section.

## Inputs

- machine-readable event profile
- enrichment hunt recipes
- artifact diff output
- telemetry requirements

## Required Output

```yaml
event_id: ""
detections:
  - name: ""
    type: "kql|spl|sigma|yara|osquery|bash|github-cli|aws-cli|gcloud|azure-kql"
    telemetry: ""
    query: ""
    output_fields: []
    positive_signal: ""
    false_positives: ""
    severity: "low|medium|high|critical"
    maps_to_iocs: []
    maps_to_behaviors: []
```

For post handling sections, convert each detection into a fenced `bash`, `python`, `kql`, `spl`, or `powershell` block. The block must include exact indicator values and exact time windows when time scoping is part of the detection.

## Detection Rules

- Do not generate a detection for an indicator with no telemetry source.
- Do not overclaim Sigma/YARA coverage.
- Prefer behavior detections over domain-only detections where possible.
- Include false positives and escalation for every detection.
- Do not generate placeholder variables for incident values. `PACKAGE`, `RUN_ID`, `OWNER/REPO`, `START_DATE`, `EVENT_IOC_REGEX`, and `REPLACE_WITH_*` are invalid in publishable detections.
- If only reader-specific scope is unknown, require it explicitly and keep event values literal.
