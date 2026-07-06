#!/usr/bin/env python3
"""Merge specialist output file paths into a site-worker result manifest."""
from __future__ import annotations
import argparse, json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--event-id', required=True)
    p.add_argument('--mode', default='new_incident_post')
    p.add_argument('--decision', default='needs_review')
    p.add_argument('--artifact', action='append', default=[], help='Path to completed artifact')
    p.add_argument('--blocking-gap', action='append', default=[])
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = {
        'site_worker_result_version': '1.0',
        'mode': args.mode,
        'decision': args.decision,
        'event_id': args.event_id,
        'slug': '',
        'parent_campaign_id': 'none',
        'spawned_tasks': [],
        'completed_artifacts': args.artifact,
        'validation_results': [],
        'blocking_gaps': args.blocking_gap,
        'recommended_next_action': 'Review blocking gaps' if args.blocking_gap else 'Run final post validation',
    }
    args.output.write_text(json.dumps(result, indent=2) + '
', encoding='utf-8')
    print(args.output)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
