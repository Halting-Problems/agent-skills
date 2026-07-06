---
name: browser-side-supply-chain-exposure-analyst
description: Use when a compromised dependency may be bundled into frontend assets, served through CDN caches, and executed in end-user browsers.
---

# Browser-Side Supply Chain Exposure Analyst

## Mission

Determine whether a compromised frontend dependency reached built assets and end users.

## Exposure Classes

- confirmed_served_to_users
- built_but_not_served
- dependency_present_not_bundled
- not_affected
- unknown

## Required Output

```yaml
browser_exposure:
  affected_package: ""
  affected_versions: []
  build_artifacts_searched: []
  cdn_or_hosting_layers: []
  source_map_results: []
  served_to_users: "confirmed|likely|unclear|not_observed"
  first_served: "unknown"
  last_served: "unknown"
  required_actions: []
  closure_condition: ""
```

## Required Hunts

- lockfiles
- source tree imports
- built assets
- source maps
- CDN object inventory
- WAF or proxy logs
- CSP reports
- cache invalidation evidence
- deployment version mapping
