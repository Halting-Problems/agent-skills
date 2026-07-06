#!/usr/bin/env python3
"""Build site-worker work orders from source-watcher candidate output.

The script filters candidates that are already covered by an existing Halting
Problems post index and emits one deep-analysis site-worker work order per new
unreported candidate.

Input formats:
  - JSON source-watcher output with a top-level candidate_incidents list.
  - YAML source-watcher output if PyYAML is installed.
  - JSON existing index with any of these optional keys:
      reported_source_urls, slugs, dedupe_keys, event_ids, posts

Example:
  python build_refresh_work_orders.py candidates.json --existing-index site-index.json --out work-orders.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


TRACKING_PREFIXES = ("utm_",)
TRACKING_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid", "igshid"}


def load_data(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise SystemExit(f"{path}: not JSON, and PyYAML is not installed for YAML input") from exc
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise SystemExit(f"{path}: expected object at top level")
    return data


def canonical_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = re.sub(r"/+$", "", parsed.path or "/")
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key not in TRACKING_KEYS and not key.startswith(TRACKING_PREFIXES)
    ]
    query = urlencode(sorted(query_pairs), doseq=True)
    return urlunparse((scheme, netloc, path, "", query, ""))


def candidate_sources(candidate: dict[str, Any]) -> list[str]:
    sources = candidate.get("starting_sources") or candidate.get("source_urls") or []
    urls: list[str] = []
    for source in sources:
        if isinstance(source, str):
            urls.append(source)
        elif isinstance(source, dict) and source.get("url"):
            urls.append(str(source["url"]))
    if candidate.get("url"):
        urls.append(str(candidate["url"]))
    return sorted({u for u in urls if u})


def normalize_values(values: Any) -> set[str]:
    if not values:
        return set()
    if isinstance(values, str):
        values = [values]
    normalized: set[str] = set()
    for value in values:
        if value is None:
            continue
        normalized.add(str(value).strip().lower())
    return {v for v in normalized if v}


def slug_for(candidate: dict[str, Any]) -> str:
    candidate_id = str(candidate.get("candidate_id") or "").strip().lower()
    if candidate_id:
        return candidate_id
    title = str(candidate.get("title") or "candidate").lower()
    return re.sub(r"[^a-z0-9]+", "-", title).strip("-") or "candidate"


def canonical_sources(values: list[str]) -> set[str]:
    return {canonical_url(url) for url in values if url}


def has_followup_signal(candidate: dict[str, Any]) -> bool:
    threat_classes = normalize_values(candidate.get("candidate_threat_classes"))
    if "follow-up-analysis" in threat_classes:
        return True
    candidate_id = str(candidate.get("candidate_id") or "").lower()
    title = str(candidate.get("title") or "").lower()
    reason = str(candidate.get("reason") or "").lower()
    return "followup" in candidate_id or "follow-up" in title or "follow-up" in reason


def post_sort_key(post: dict[str, Any]) -> tuple[str, str]:
    return (str(post.get("date") or "9999-99-99"), str(post.get("slug") or "~"))


def normalize_post(post: dict[str, Any]) -> dict[str, Any]:
    return {
        "slug": str(post.get("slug") or "").strip().lower(),
        "title": str(post.get("title") or ""),
        "date": str(post.get("date") or ""),
        "urls": canonical_sources(list(post.get("source_urls") or [])),
        "dedupe_keys": normalize_values(post.get("dedupe_keys")),
    }


def make_existing_index(data: dict[str, Any]) -> dict[str, Any]:
    urls = normalize_values(data.get("reported_source_urls") or data.get("source_urls"))
    raw_posts = data.get("posts") or []
    posts = [normalize_post(post) for post in raw_posts if isinstance(post, dict)]
    return {
        "urls": {canonical_url(url) for url in urls},
        "slugs": normalize_values(data.get("slugs")),
        "dedupe_keys": normalize_values(data.get("dedupe_keys")),
        "event_ids": normalize_values(data.get("event_ids")),
        "posts": sorted(posts, key=post_sort_key),
    }


def classify_candidate(candidate: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
    slug = slug_for(candidate)
    candidate_keys = normalize_values(candidate.get("dedupe_keys"))
    candidate_urls = canonical_sources(candidate_sources(candidate))
    followup = has_followup_signal(candidate)

    best_match: dict[str, Any] | None = None
    for post in existing.get("posts", []):
        matched_keys = sorted(candidate_keys & post["dedupe_keys"])
        matched_urls = sorted(candidate_urls & post["urls"])
        exact_slug = slug == post["slug"] or slug in existing["event_ids"] and post["slug"] == slug
        score = 0
        if exact_slug:
            score += 100
        score += len(matched_urls) * 20
        score += len(matched_keys) * 10
        if score <= 0:
            continue
        candidate_match = {
            "post": post,
            "matched_keys": matched_keys,
            "matched_urls": matched_urls,
            "exact_slug": exact_slug,
            "score": score,
        }
        if best_match is None:
            best_match = candidate_match
            continue
        if candidate_match["score"] > best_match["score"]:
            best_match = candidate_match
            continue
        if candidate_match["score"] == best_match["score"] and post_sort_key(post) < post_sort_key(best_match["post"]):
            best_match = candidate_match

    if best_match is None:
        return {
            "disposition": "new",
            "canonical_slug": "",
            "reasons": [],
            "matched_keys": [],
            "matched_urls": [],
        }

    post = best_match["post"]
    reasons: list[str] = []
    if best_match["exact_slug"]:
        reasons.append(f"known slug/event_id: {post['slug']}")
    if best_match["matched_keys"]:
        reasons.append("known dedupe_keys: " + ", ".join(best_match["matched_keys"]))
    if best_match["matched_urls"]:
        reasons.append("known source_urls: " + ", ".join(best_match["matched_urls"]))

    has_new_sources = bool(candidate_urls - post["urls"])
    exact_same_candidate = best_match["exact_slug"] and not has_new_sources and not followup
    if exact_same_candidate:
        return {
            "disposition": "already_reported",
            "canonical_slug": post["slug"],
            "reasons": reasons,
            "matched_keys": best_match["matched_keys"],
            "matched_urls": best_match["matched_urls"],
        }

    return {
        "disposition": "update_existing",
        "canonical_slug": post["slug"],
        "reasons": reasons,
        "matched_keys": best_match["matched_keys"],
        "matched_urls": best_match["matched_urls"],
    }


def worker_prompt(candidate: dict[str, Any], mode: str = "new_incident_post", canonical_slug: str = "") -> str:
    sources = candidate_sources(candidate)
    if mode == "existing_post_upgrade":
        objective = f"""Perform a detailed, in-depth Halting Problems update for the canonical existing post `{canonical_slug}` using this candidate as new evidence.
Treat the existing article as the single source of truth. Do not create a follow-up post or a sibling post unless the evidence proves this is a separate incident. Extract the current post content, merge the new facts, run the schema normalizer, run the actionability review, add any missing hunt recipes, downstream audits, or remediation gates, and validate the post contract."""
    else:
        objective = "Perform a detailed, in-depth Halting Problems analysis for this candidate and decide whether it should become a new post, update an existing post, attach to a campaign, or be rejected. If it is publishable, create or update the site content and all supporting artifacts needed for a defensible article."

    canonical_line = f"- canonical_existing_slug: {canonical_slug}\n" if canonical_slug else ""
    return f"""Use the Halting Problems site-worker skill for one candidate source only.

Candidate:
- candidate_id: {candidate.get("candidate_id", "")}
- title: {candidate.get("title", "")}
- first_seen: {candidate.get("first_seen", "")}
- source_urls: {json.dumps(sources, ensure_ascii=False)}
- dedupe_keys: {json.dumps(candidate.get("dedupe_keys", []), ensure_ascii=False)}
- ecosystem: {json.dumps(candidate.get("ecosystem", []), ensure_ascii=False)}
- affected_assets: {json.dumps(candidate.get("affected_assets", []), ensure_ascii=False)}
- reason: {candidate.get("reason", "")}
- collection_gaps: {json.dumps(candidate.get("collection_gaps", []), ensure_ascii=False)}
{canonical_line}
Objective:
{objective}

Ecosystem & Storage resolution:
- Create folder `~/hp-posts-info/{candidate.get("candidate_id", "")}/` for all script, mock, and test assets.
- Save the hunt manifest in `~/hp-posts-info/{candidate.get("candidate_id", "")}/manifest.yaml`.
- Save the machine-readable IOC profile in `~/hp-posts-info/{candidate.get("candidate_id", "")}/iocs.json`.

Depth requirements:
- Prefer direct sources, primary research, registry metadata, repository history, package artifacts, release artifacts, advisories, and original researcher posts.
- Build a claim ledger that ties every assertion to evidence. Require source attribution for every behavioral claim.
- Distinguish observed behavior from inference.
- Verify package, container, GitHub Action, extension, release, tag, provenance, and builder facts where applicable.
- Preserve uncertainty. Use unknown or not_observed instead of inventing versions, hashes, victims, timelines, or attribution.
- Include detailed downstream impact analysis for credentials, CI/CD, cloud, developer endpoints, browsers/CDNs, and registries when applicable.
- Require an applicability decision before adding endpoint, registry, GitHub, browser, CI/CD, or cloud modules.

Remediation & Advice requirements:
- Require rationale for every recommendation. Do not write generic "rotate everything" checklist templates. Remediations must be prose-driven and specifically reference the packages, registry hooks, or directories defined in the finding.

Python script requirements:
- Create useful, usable Python scripts inside `~/hp-posts-info/{candidate.get("candidate_id", "")}/scripts/` whenever the incident can be audited, hunted, or remediated.
- Scripts must be complete and runnable, not placeholders or pseudocode.
- Embed incident-specific constants that are known from evidence, such as package names, versions, domains, hashes, registry paths, repository names, action refs, advisory IDs, and relevant timestamps.
- Include unit tests in `~/hp-posts-info/{candidate.get("candidate_id", "")}/tests/` and mock telemetry fixtures under `~/hp-posts-info/{candidate.get("candidate_id", "")}/fixtures/` to verify scripts run successfully on clean/dirty states.
- Do not leave placeholders such as OWNER/REPO, RUN_ID, PACKAGE, START_DATE, REPLACE_WITH_*, or bracketed TODO values in final article scripts.

Safety & Sandbox constraints:
- Do NOT run, execute, or install downloaded untrusted code under any circumstances (never use npm install, node, bun, or python execution on untrusted packages). Inspect only via safe, static methods.
- To avoid triggering API safety filters, never print raw text containing potentially sensitive or safety-triggering content (such as exploit instructions or bioweapon words) in the terminal output. Use helper python scripts to inspect locally and print only redacted/defanged summaries or metadata.
- Always write, download, extract, or copy untrusted package tarballs, extensions, or files being analyzed directly to the corresponding post directory in the sibling research repository (`~/hp-posts-info/{candidate.get("candidate_id", "")}/`). Never download, write, or extract them to locations outside this repository (such as `/tmp/`, `/home/sam/`, or the website root).

Modular pipeline requirements:
- Before drafting or publishing, create an event profile and run `python skills/site-worker/scripts/site_worker_plan.py <event_profile.json> --output ~/hp-posts-info/{candidate.get("candidate_id", "")}/site-worker-plan.json`.
- Run `python skills/site-worker/scripts/validate_site_worker_plan.py ~/hp-posts-info/{candidate.get("candidate_id", "")}/site-worker-plan.json` and fix any validation errors before continuing.
- Use `skills/site-worker/references/agent-pipeline-critique-questions.md` as the critique question bank.
- Use `skills/site-worker/references/agency-agent-review-lanes.md` to dispatch review tasks based on profiles in `/home/sam/agency-agents`.
- Required agency-agent review lanes are architecture_review, data_quality_review, incident_response_review, workflow_qa_review, and technical_writing_review.
- Treat Next.js/Postgres as the canonical publishing target.
- Do not treat Astro content, D1, or static fallback files as the canonical publication path.

Validation:
- Run the site-worker validation checklist.
- Confirm sourceCount matches numbered sources.
- Confirm final post prose defangs network IOCs outside machine-readable blocks.
- Confirm machine-readable event profile JSON is valid.
- Validate Postgres import readiness for sources, claims, evidence, package facts, IOCs, scripts, detections, and remediation gates.
- Validate Next.js API/feed compatibility from canonical Postgres-backed facts.
- Treat Astro content, D1, and static fallback files as legacy compatibility paths only, not as canonical publication evidence.

Return:
- site_worker_result YAML
- created or updated files across both repositories
- script paths and how each script helps defenders
- validation results
- blocking gaps and exact next collection steps if not publish-ready
"""


def make_work_orders(candidates: list[dict[str, Any]], existing: dict[str, Any], update_slug: str = "") -> dict[str, Any]:
    already_reported: list[dict[str, Any]] = []
    new_candidates: list[dict[str, Any]] = []
    spawned: list[dict[str, Any]] = []

    for candidate in candidates:
        classification = classify_candidate(candidate, existing)
        slug = slug_for(candidate)
        candidate_id = str(candidate.get("candidate_id") or slug)

        if classification["disposition"] == "already_reported" and slug != update_slug:
            already_reported.append({
                "candidate_id": candidate_id,
                "title": candidate.get("title", ""),
                "reasons": classification["reasons"],
            })
            continue

        new_candidates.append(candidate)
        canonical_slug = update_slug.strip().lower() if update_slug else classification["canonical_slug"]
        mode = "existing_post_upgrade" if canonical_slug else "new_incident_post"
        spawned.append({
            "task_id": f"site-worker-{candidate_id}",
            "candidate_id": candidate_id,
            "title": candidate.get("title", ""),
            "source_urls": candidate_sources(candidate),
            "dedupe_keys": candidate.get("dedupe_keys", []),
            "status": "queued",
            "specialist": "site-worker",
            "recommended_mode": mode,
            "canonical_existing_slug": canonical_slug,
            "match_reasons": classification["reasons"],
            "prompt": worker_prompt(candidate, mode=mode, canonical_slug=canonical_slug),
        })

    return {
        "site_refresh_result": {
            "total_candidates": len(candidates),
            "already_reported": already_reported,
            "rejected_candidates": [],
            "new_unreported_candidates": [
                {
                    "candidate_id": c.get("candidate_id", slug_for(c)),
                    "title": c.get("title", ""),
                    "source_urls": candidate_sources(c),
                    "dedupe_keys": c.get("dedupe_keys", []),
                }
                for c in new_candidates
            ],
            "spawned_site_workers": spawned,
            "completed_artifacts": [],
            "validation_results": [],
            "blocking_gaps": [],
            "recommended_next_action": "Run site-worker tasks in update mode for canonical matches; only create a new post when no canonical post match exists.",
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates", type=Path, help="source-watcher JSON/YAML output")
    parser.add_argument("--existing-index", type=Path, help="JSON/YAML index of already reported posts/sources")
    parser.add_argument("--update-slug", type=str, help="slug of post to run in update mode")
    parser.add_argument("--out", type=Path, help="write JSON output to this path")
    args = parser.parse_args()

    data = load_data(args.candidates)
    candidates = data.get("candidate_incidents", [])
    if not isinstance(candidates, list):
        raise SystemExit("candidate_incidents must be a list")
    typed_candidates = [c for c in candidates if isinstance(c, dict)]

    existing: dict[str, Any] = {"urls": set(), "slugs": set(), "dedupe_keys": set(), "event_ids": set(), "posts": []}
    if args.existing_index:
        existing = make_existing_index(load_data(args.existing_index))

    update_slug = args.update_slug.strip().lower() if args.update_slug else ""
    result = make_work_orders(typed_candidates, existing, update_slug)
    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
