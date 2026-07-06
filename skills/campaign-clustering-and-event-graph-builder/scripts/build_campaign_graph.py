#!/usr/bin/env python3
"""Build a simple correlation graph from event profile JSON files.

Usage:
  python build_campaign_graph.py profiles/*.json > campaign_graph.json
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


def norm_list(v):
    return v if isinstance(v, list) else []


def indicators(profile):
    iocs = profile.get("iocs", {})
    assets = profile.get("affected_assets", {})
    result = {
        "domains": set(norm_list(iocs.get("domains"))),
        "urls": set(norm_list(iocs.get("urls"))),
        "hashes": set(norm_list(iocs.get("hashes"))),
        "files": set(norm_list(iocs.get("files"))),
        "process_patterns": set(norm_list(iocs.get("process_patterns"))),
        "network_patterns": set(norm_list(iocs.get("network_patterns"))),
        "packages": set(norm_list(assets.get("packages"))),
        "repositories": set(norm_list(assets.get("repositories"))),
        "attack_types": set(norm_list(profile.get("attack_types"))),
    }
    return result


def score(a, b):
    ia, ib = indicators(a), indicators(b)
    hard = []
    moderate = []
    for k in ["domains", "urls", "hashes", "files", "repositories"]:
        common = sorted(ia[k] & ib[k])
        if common:
            hard.append({"type": k, "values": common})
    for k in ["process_patterns", "network_patterns", "packages", "attack_types"]:
        common = sorted(ia[k] & ib[k])
        if common:
            moderate.append({"type": k, "values": common})
    if len(hard) >= 2:
        decision = "campaign_candidate"
    elif len(hard) == 1:
        decision = "related_candidate"
    elif len(moderate) >= 2:
        decision = "weak_related_candidate"
    else:
        decision = "separate"
    return {"hard": hard, "moderate": moderate, "decision": decision}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profiles", nargs="+")
    args = parser.parse_args()

    profiles = []
    for p in args.profiles:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        profiles.append(data)

    edges = []
    for a, b in itertools.combinations(profiles, 2):
        s = score(a, b)
        if s["decision"] != "separate":
            edges.append({
                "source": a.get("event_id"),
                "target": b.get("event_id"),
                **s
            })

    print(json.dumps({"events": [p.get("event_id") for p in profiles], "edges": edges}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
