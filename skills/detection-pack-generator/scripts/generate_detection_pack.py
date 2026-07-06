#!/usr/bin/env python3
"""Generate starter detection pack from a Halting Problems event profile.

Usage:
  python generate_detection_pack.py event_profile.json > detection_pack.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def arr(obj: dict, path: list[str]) -> list:
    cur = obj
    for key in path:
        if not isinstance(cur, dict):
            return []
        cur = cur.get(key, [])
    return cur if isinstance(cur, list) else []


def detection(name, type_, telemetry, query, fields, signal, fps, severity, iocs=None, behaviors=None):
    return {
        "name": name,
        "type": type_,
        "telemetry": telemetry,
        "query": query,
        "output_fields": fields,
        "positive_signal": signal,
        "false_positives": fps,
        "severity": severity,
        "maps_to_iocs": iocs or [],
        "maps_to_behaviors": behaviors or [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event_profile")
    args = parser.parse_args()
    profile = json.loads(Path(args.event_profile).read_text(encoding="utf-8"))

    event_id = profile.get("event_id", "unknown")
    iocs = profile.get("iocs", {})
    detections = []

    domains = iocs.get("domains", [])
    if domains:
        domain_filter = ", ".join([f'"{d}"' for d in domains])
        detections.append(detection(
            "Outbound connection to event IOC domain",
            "kql",
            "EDR network telemetry",
            f"""DeviceNetworkEvents
| where RemoteUrl in~ ({domain_filter}) or RemoteUrl has_any ({domain_filter})
| project Timestamp, DeviceName, InitiatingProcessFileName, InitiatingProcessCommandLine, RemoteUrl, RemoteIP, RemotePort""",
            ["Timestamp", "DeviceName", "InitiatingProcessFileName", "InitiatingProcessCommandLine", "RemoteUrl", "RemoteIP", "RemotePort"],
            "Endpoint or runner initiated network activity to an IOC domain.",
            "Security testing, research sandboxes, or malware analysis VMs may intentionally contact IOC infrastructure.",
            "high",
            domains,
            ["network_exfiltration"],
        ))
        detections.append(detection(
            "DNS lookup for event IOC domain",
            "spl",
            "DNS logs",
            f"""index=dns ({' OR '.join([f'query="{d}"' for d in domains])})
| table _time src query record_type answer""",
            ["_time", "src", "query", "record_type", "answer"],
            "Host queried a known event domain.",
            "Analyst lookup, sandbox detonation, passive security tooling.",
            "medium",
            domains,
            ["dns_resolution"],
        ))

    process_patterns = iocs.get("process_patterns", [])
    if process_patterns:
        detections.append(detection(
            "Suspicious package or CI runner process behavior",
            "kql",
            "EDR process creation telemetry",
            """DeviceProcessEvents
| where ProcessCommandLine has_any ("/proc/", "/mem", "Runner.Worker", "gh auth token", "isSecret", "curl", "wget", "bun", "postinstall", "preinstall")
| project Timestamp, DeviceName, FileName, ProcessCommandLine, InitiatingProcessFileName, InitiatingProcessCommandLine""",
            ["Timestamp", "DeviceName", "FileName", "ProcessCommandLine", "InitiatingProcessFileName", "InitiatingProcessCommandLine"],
            "Process command line matches event behavior or package install credential access.",
            "Build jobs that legitimately use Bun or package lifecycle scripts.",
            "high",
            process_patterns,
            ["credential_access", "execution"],
        ))

    files = iocs.get("files", [])
    if files:
        osquery_conditions = " OR ".join([f"path LIKE '%{f.replace('%','%%')}%'" for f in files])
        detections.append(detection(
            "Event IOC files on endpoint",
            "osquery",
            "Endpoint filesystem inventory",
            f"SELECT path, filename, size, mtime FROM file WHERE {osquery_conditions};",
            ["path", "filename", "size", "mtime"],
            "Known event file path exists on developer endpoint or runner.",
            "Source checkout or benign test fixture containing IOC filename.",
            "medium",
            files,
            ["file_indicator"],
        ))

    packages = profile.get("affected_assets", {}).get("packages", [])
    versions = profile.get("affected_assets", {}).get("versions", [])
    if packages:
        detections.append(detection(
            "GitHub code search for affected dependency",
            "github-cli",
            "GitHub source code and lockfiles",
            "\\n".join([f"gh search code '\"{pkg}\" path:package-lock.json OR path:pnpm-lock.yaml OR path:requirements.txt OR path:poetry.lock OR path:go.sum OR path:composer.lock' --limit 1000" for pkg in packages]),
            ["repository", "path", "matching_line"],
            "Repository contains affected package reference.",
            "Reference may be in documentation, tests, or unreachable dependency groups.",
            "medium",
            packages + versions,
            ["dependency_inventory"],
        ))

    print(json.dumps({"event_id": event_id, "detections": detections}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
