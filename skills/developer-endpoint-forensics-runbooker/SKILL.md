---
name: developer-endpoint-forensics-runbooker
description: Use when malicious packages, IDE extensions, RATs, or developer tools may have executed on developer workstations.
---

# Developer Endpoint Forensics Runbooker

## Mission

Generate endpoint triage runbooks for developer workstation compromise from supply-chain malware.

## Scope

- Windows
- macOS
- Linux
- VS Code and Open VSX extensions
- CLI tokens
- package manager caches
- shell profiles
- SSH and cloud credentials

## Required Output

```yaml
endpoint_runbook:
  platforms: []
  collection_order: []
  triage_commands: []
  credential_files_to_review: []
  persistence_locations: []
  process_and_network_hunts: []
  reimage_criteria: []
  rotation_order: []
  evidence_to_preserve: []
```

## Rules

- Preserve evidence before deleting.
- Rotate credentials from a clean environment.
- Give platform-specific commands.
- Mark commands that may expose sensitive local paths or tokens.
