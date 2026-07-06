#!/usr/bin/env python3
"""Export IOCs from an event profile to JSON, CSV, STIX-like, and MISP-like formats.

Usage:
  python export_iocs.py event_profile.json --out out/iocs
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def indicator(type_, value, durability, event_id):
    return {
        "type": type_,
        "value": value,
        "durability": durability,
        "event_id": event_id,
    }


def stix_id(kind: str, value: str) -> str:
    digest = hashlib.sha256(value.encode()).hexdigest()[:32]
    return f"{kind}--{digest[:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event_profile")
    parser.add_argument("--out", default="out/ioc-export")
    args = parser.parse_args()

    profile = json.loads(Path(args.event_profile).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    event_id = profile.get("event_id", "unknown")
    iocs = profile.get("iocs", {})
    assets = profile.get("affected_assets", {})

    durable = []
    volatile = []

    for pkg in assets.get("packages", []):
        durable.append(indicator("package", pkg, "durable", event_id))
    for version in assets.get("versions", []):
        durable.append(indicator("package_version", version, "durable", event_id))
    for f in iocs.get("files", []):
        durable.append(indicator("file_path", f, "durable", event_id))
    for h in iocs.get("hashes", []):
        durable.append(indicator("hash", h, "durable", event_id))
    for item in iocs.get("package_versions", []):
        durable.append(indicator("package_version", item, "durable", event_id))

    for d in iocs.get("domains", []):
        volatile.append(indicator("domain", d, "volatile", event_id))
    for u in iocs.get("urls", []):
        volatile.append(indicator("url", u, "volatile", event_id))
    for ip in iocs.get("ips", []):
        volatile.append(indicator("ip", ip, "volatile", event_id))

    all_indicators = durable + volatile
    (out / "iocs.normalized.json").write_text(json.dumps({
        "event_id": event_id,
        "durable_indicators": durable,
        "volatile_indicators": volatile,
    }, indent=2), encoding="utf-8")

    with (out / "iocs.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["event_id", "type", "value", "durability"])
        writer.writeheader()
        writer.writerows(all_indicators)

    now = datetime.now(timezone.utc).isoformat()
    stix_objects = []
    for ind in all_indicators:
        pattern_type = {
            "domain": "domain-name:value",
            "url": "url:value",
            "ip": "ipv4-addr:value",
            "hash": "file:hashes.'SHA-256'",
        }.get(ind["type"], "x-haltingproblems:value")
        stix_objects.append({
            "type": "indicator",
            "spec_version": "2.1",
            "id": stix_id("indicator", ind["type"] + ":" + ind["value"]),
            "created": now,
            "modified": now,
            "name": f"{event_id} {ind['type']}",
            "pattern_type": "stix",
            "pattern": f"[{pattern_type} = '{ind['value']}']",
            "valid_from": now,
            "labels": ["supply-chain", ind["durability"]],
        })
    (out / "stix-lite-bundle.json").write_text(json.dumps({
        "type": "bundle",
        "id": stix_id("bundle", event_id),
        "objects": stix_objects,
    }, indent=2), encoding="utf-8")

    misp_attrs = [{"type": i["type"], "value": i["value"], "category": "Payload delivery" if i["durability"] == "volatile" else "Artifacts dropped"} for i in all_indicators]
    (out / "misp-lite-event.json").write_text(json.dumps({
        "Event": {
            "info": profile.get("event_name", event_id),
            "date": now[:10],
            "threat_level_id": "2",
            "analysis": "1",
            "Attribute": misp_attrs,
        }
    }, indent=2), encoding="utf-8")

    print(json.dumps({"event_id": event_id, "out": str(out), "count": len(all_indicators)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
