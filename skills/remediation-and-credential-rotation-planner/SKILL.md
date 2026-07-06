---
name: remediation-and-credential-rotation-planner
description: Use when a supply-chain incident may expose GitHub, cloud, registry, Kubernetes, Terraform, CDN, developer, or deployment credentials.
---

# Remediation And Credential Rotation Planner

## Mission

Convert exposure findings into credential-specific rotation, downstream audit, and closure plans.

## Required Output

```yaml
rotation_plan:
  event_id: ""
  rotation_scope:
    - credential_type: ""
      why_at_risk: ""
      audit_before_rotation: []
      revoke_or_rotate_steps: []
      downstream_abuse_hunts: []
      validation_steps: []
      owner: ""
      priority: "immediate|high|normal"
  remediation_gates:
    containment_complete: []
    eradication_complete: []
    recovery_complete: []
    closure_required: []
```

## Rotation Order

1. Preserve evidence.
2. Stop active malicious execution.
3. Revoke high-risk tokens from a clean environment.
4. Rotate cloud and registry publishing credentials.
5. Rebuild runners and developer endpoints if execution is confirmed.
6. Audit downstream activity.
7. Close with evidence, not assumption.
