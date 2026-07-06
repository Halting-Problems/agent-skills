#!/usr/bin/env python3
"""Normalize old or partial event profiles to the current object shape.

Usage:
  python normalize_event_profile.py input.json > normalized.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT = {
    "schema_version": "3.0",
    "event_id": "",
    "event_name": "",
    "parent_campaign_id": "none",
    "is_campaign_level": False,
    "publication_state": "needs_review",
    "confidence": "low",
    "confidence_reason": "",
    "attack_types": [],
    "sources": {"direct": [], "primary_research": [], "correlated": []},
    "affected_assets": {
        "ecosystems": [],
        "registries": [],
        "packages": [],
        "versions": [],
        "repositories": [],
        "vendors": [],
        "ci_cd_systems": [],
        "container_images": [],
        "developer_tools": [],
        "credentials_at_risk": [],
    },
    "timeline": {
        "first_seen": "unknown",
        "malicious_publish_time": "unknown",
        "discovery_time": "unknown",
        "removal_time": "unknown",
        "disclosure_time": "unknown",
        "patch_or_fix_time": "unknown",
    },
    "artifact_analysis": {
        "malicious_artifacts": [],
        "execution_trigger": "unknown",
        "payload_behavior": [],
        "provenance": {},
    },
    "iocs": {
        "package_versions": [],
        "files": [],
        "hashes": [],
        "domains": [],
        "urls": [],
        "ips": [],
        "process_patterns": [],
        "network_patterns": [],
    },
    "detection": {
        "lockfile_hunts": [],
        "filesystem_hunts": [],
        "process_hunts": [],
        "network_hunts": [],
        "ci_cd_hunts": [],
        "registry_hunts": [],
        "hunt_recipes": [],
    },
    "open_questions": [],
    "defender_takeaways": {
        "detection": "",
        "hunting": "",
        "remediation": "",
        "prevention": "",
    },
    "remediation_gates": {
        "containment_complete": [],
        "eradication_complete": [],
        "recovery_complete": [],
        "closure_required": [],
    },
}


def merge(default, src):
    if isinstance(default, dict):
        out = dict(default)
        if isinstance(src, dict):
            for k, v in src.items():
                if k in out:
                    out[k] = merge(out[k], v)
                else:
                    out[k] = v
        return out
    return src if src not in (None, "") else default


def normalize(data):
    if isinstance(data, list):
        # Old Format B or array profiles. Preserve as correlated sources if unable to map.
        first = data[0] if data and isinstance(data[0], dict) else {}
        base = merge(DEFAULT, {})
        base["event_id"] = first.get("event_id", first.get("id", "unknown-array-profile"))
        base["event_name"] = first.get("event_name", first.get("name", base["event_id"]))
        base["sources"]["correlated"] = [item.get("url") for item in data if isinstance(item, dict) and item.get("url")]
        base["open_questions"].append("Input used old array format. Manual review required.")
        return base

    # field aliases
    aliases = {
        "direct_sources": ("sources", "direct"),
        "primary_sources": ("sources", "primary_research"),
        "correlated_sources": ("sources", "correlated"),
        "ci_CD_systems": ("affected_assets", "ci_cd_systems"),
        "credentialsAtRisk": ("affected_assets", "credentials_at_risk"),
    }
    data = dict(data)
    for old, (parent, new) in aliases.items():
        if old in data:
            data.setdefault(parent, {})
            if isinstance(data[parent], dict):
                data[parent].setdefault(new, data.pop(old))

    return merge(DEFAULT, data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    args = parser.parse_args()
    data = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    print(json.dumps(normalize(data), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
