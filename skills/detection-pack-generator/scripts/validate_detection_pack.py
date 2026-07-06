#!/usr/bin/env python3
"""Validate detection pack actionability."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = ["name", "type", "telemetry", "query", "positive_signal", "false_positives", "severity"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("detection_pack")
    args = parser.parse_args()
    data = json.loads(Path(args.detection_pack).read_text(encoding="utf-8"))
    errors = []

    if not data.get("event_id"):
        errors.append("missing event_id")
    detections = data.get("detections", [])
    if not detections:
        errors.append("no detections")
    for idx, det in enumerate(detections):
        for key in REQUIRED:
            if not det.get(key):
                errors.append(f"detections[{idx}] missing {key}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1
    print(f"Detection pack OK: {args.detection_pack}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
