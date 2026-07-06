---
name: ioc-normalizer-and-sharing-exporter
description: Use when converting post IOCs and observables into normalized JSON, CSV, STIX-like bundles, MISP-like drafts, or OpenCTI-friendly objects.
---

# IOC Normalizer And Sharing Exporter

## Mission

Turn human-readable indicators into clean downstream sharing formats.

## Indicator Classes

Durable:

- package name and version
- purl
- file path
- file hash
- commit SHA
- tag
- image digest
- registry metadata
- workflow path
- signing identity

Volatile:

- domain
- URL
- IP
- GitHub exfil repo
- CDN/script URL
- DNS pattern

## Required Output

```yaml
ioc_export:
  event_id: ""
  durable_indicators: []
  volatile_indicators: []
  defanged_markdown: ""
  csv_paths: []
  stix_bundle_path: ""
  misp_event_path: ""
```
