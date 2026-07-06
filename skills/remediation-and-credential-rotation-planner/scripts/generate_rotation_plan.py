#!/usr/bin/env python3
"""Generate a credential rotation plan from event profile credentials_at_risk.

Usage:
  python generate_rotation_plan.py event_profile.json > rotation_plan.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

TEMPLATES = {
    "GitHub tokens": {
        "audit": ["GitHub audit log actor/token events", "commits/releases/workflow changes after exposure", "new deploy keys and GitHub Apps"],
        "rotate": ["revoke exposed PATs/OAuth tokens", "rotate gh CLI tokens", "review fine-grained token scopes"],
        "hunt": ["github_downstream_audit.sh"],
    },
    "GITHUB_TOKEN": {
        "audit": ["workflow run permissions", "repo writes during run window", "package/release creation"],
        "rotate": ["cannot rotate historical GITHUB_TOKEN, reduce default permissions and rerun clean workflows"],
        "hunt": ["github_downstream_audit.sh"],
    },
    "AWS OIDC": {
        "audit": ["AssumeRoleWithWebIdentity", "AccessKeyId follow-on CloudTrail activity"],
        "rotate": ["tighten trust policy subject claims", "rotate secrets read by assumed role if accessed", "review IAM policies"],
        "hunt": ["aws_github_oidc_audit.sh"],
    },
    "Azure OIDC": {
        "audit": ["service principal sign-ins", "AzureActivity writes"],
        "rotate": ["review federated credentials", "rotate secrets touched by service principal", "tighten subjects"],
        "hunt": ["azure_github_oidc_audit.sh"],
    },
    "GCP OIDC": {
        "audit": ["STS token exchanges", "GenerateAccessToken", "service account follow-on activity"],
        "rotate": ["review workload identity provider conditions", "disable or narrow service account impersonation"],
        "hunt": ["gcp_github_oidc_audit.sh"],
    },
    "package registry credentials": {
        "audit": ["versions published after exposure", "dist-tags and package maintainers", "provenance state"],
        "rotate": ["revoke registry tokens", "move to trusted publishing or OIDC", "rotate package automation tokens"],
        "hunt": ["registry_publish_audit.sh"],
    },
    "deployment credentials": {
        "audit": ["Kubernetes audit writes", "Terraform runs/applies", "CDN and cloud deploy activity"],
        "rotate": ["rotate deploy keys", "rotate kubeconfigs", "rotate Terraform tokens", "review environment approvals"],
        "hunt": ["k8s_deploy_audit.sh", "tfc_audit.sh", "cloudflare_audit.sh"],
    },
}


def match_template(cred: str) -> dict:
    lc = cred.lower()
    for key, template in TEMPLATES.items():
        if key.lower() in lc or any(part in lc for part in key.lower().split()):
            return template
    return {
        "audit": ["identify usage logs for this credential type"],
        "rotate": ["revoke or rotate from a clean environment"],
        "hunt": ["custom audit required"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event_profile")
    args = parser.parse_args()
    profile = json.loads(Path(args.event_profile).read_text(encoding="utf-8"))
    creds = profile.get("affected_assets", {}).get("credentials_at_risk", [])
    plan = []
    for cred in creds:
        t = match_template(cred)
        plan.append({
            "credential_type": cred,
            "why_at_risk": "Listed as credentials_at_risk in event profile.",
            "audit_before_rotation": t["audit"],
            "revoke_or_rotate_steps": t["rotate"],
            "downstream_abuse_hunts": t["hunt"],
            "validation_steps": ["confirm new credential works", "confirm old credential fails", "attach audit results"],
            "priority": "immediate" if any(x in cred.lower() for x in ["cloud", "registry", "deployment", "token", "secret", "oidc"]) else "high",
        })
    print(json.dumps({
        "event_id": profile.get("event_id", "unknown"),
        "rotation_scope": plan,
        "remediation_gates": {
            "containment_complete": ["malicious artifact blocked", "affected workflows disabled or fixed", "high-risk tokens revoked"],
            "eradication_complete": ["runners rebuilt if execution confirmed", "package caches purged", "malicious artifacts removed or blocked"],
            "recovery_complete": ["clean builds deployed", "new credentials verified", "downstream audit complete"],
            "closure_required": ["exposure classification per affected asset", "evidence preserved", "unknowns documented"],
        }
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
