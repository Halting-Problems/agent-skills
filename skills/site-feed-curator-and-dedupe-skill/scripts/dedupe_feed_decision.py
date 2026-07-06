#!/usr/bin/env python3
"""Compare a candidate event profile to existing profiles and suggest a feed action.

Usage:
  python dedupe_feed_decision.py candidate.json existing/*.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "unknown-event"


def keys(profile: dict) -> set[str]:
    out = set()
    event_id = profile.get("event_id")
    if event_id:
        out.add(f"event_id:{event_id}")
    assets = profile.get("affected_assets", {})
    for pkg in assets.get("packages", []) or []:
        out.add(f"package:{pkg}")
    for repo in assets.get("repositories", []) or []:
        out.add(f"repo:{repo}")
    iocs = profile.get("iocs", {})
    for d in iocs.get("domains", []) or []:
        out.add(f"domain:{d}")
    for h in iocs.get("hashes", []) or []:
        out.add(f"hash:{h}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate")
    parser.add_argument("existing", nargs="*")
    args = parser.parse_args()

    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    ckeys = keys(candidate)
    matches = []

    for path in args.existing:
        profile = json.loads(Path(path).read_text(encoding="utf-8"))
        overlap = sorted(ckeys & keys(profile))
        if overlap:
            matches.append({
                "path": path,
                "event_id": profile.get("event_id"),
                "event_name": profile.get("event_name"),
                "overlap": overlap,
            })

    if not matches:
        action = "new_post"
        reason = "No dedupe key overlap with existing profiles."
    elif any(len(m["overlap"]) >= 2 for m in matches):
        action = "update_existing"
        reason = "Multiple dedupe keys overlap with an existing profile."
    else:
        action = "needs_review"
        reason = "Single dedupe key overlap. Review for campaign or related event."

    slug = slugify(candidate.get("event_name") or candidate.get("event_id") or "unknown-event")
    print(json.dumps({
        "action": action,
        "matched_existing_posts": matches,
        "dedupe_keys": sorted(ckeys),
        "parent_campaign_id": candidate.get("parent_campaign_id", "none"),
        "child_event_id": candidate.get("event_id", ""),
        "reason": reason,
        "required_updates": [],
        "canonical_slug": f"{slug}.md",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
