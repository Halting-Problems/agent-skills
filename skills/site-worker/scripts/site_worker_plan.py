#!/usr/bin/env python3
"""Create a modular Halting Problems site-worker task graph from an event profile."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_AGENCY_REVIEW_LANES = [
    {
        "review_lane": "architecture_review",
        "agent_profile_path": "/home/sam/agency-agents/engineering/engineering-multi-agent-systems-architect.md",
        "objective": "Critique topology, dependency graph, context boundaries, failure handling, and observability.",
        "blocks_publish": True,
    },
    {
        "review_lane": "data_quality_review",
        "agent_profile_path": "/home/sam/agency-agents/engineering/engineering-ai-data-remediation-engineer.md",
        "objective": "Critique data quality, normalization, quarantine paths, auditability, and zero-data-loss assumptions.",
        "blocks_publish": True,
    },
    {
        "review_lane": "incident_response_review",
        "agent_profile_path": "/home/sam/agency-agents/security/security-incident-responder.md",
        "objective": "Critique SOC/IR usability, hunt clarity, containment guidance, and closure gates.",
        "blocks_publish": True,
    },
    {
        "review_lane": "workflow_qa_review",
        "agent_profile_path": "/home/sam/agency-agents/testing/testing-workflow-optimizer.md",
        "objective": "Critique whether the chained workflow is modular, testable, and free of handoff ambiguity.",
        "blocks_publish": True,
    },
    {
        "review_lane": "technical_writing_review",
        "agent_profile_path": "/home/sam/agency-agents/engineering/engineering-technical-writer.md",
        "objective": "Critique clarity, source-backed writing, and preservation of operational detail.",
        "blocks_publish": False,
    },
]


def load_profile(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def slug_for(profile: dict[str, Any]) -> str:
    value = str(profile.get("event_id") or profile.get("candidate_id") or "unknown-event").strip()
    return value or "unknown-event"


def profile_text(profile: dict[str, Any]) -> str:
    assets = profile.get("affected_assets") or {}
    parts = [
        " ".join(profile.get("attack_types") or []),
        " ".join(assets.get("ecosystems") or []),
        " ".join(assets.get("credentials_at_risk") or []),
        " ".join(assets.get("developer_tools") or []),
    ]
    return " ".join(parts).lower()


def infer_optional_halting_skills(profile: dict[str, Any]) -> list[str]:
    text = profile_text(profile)
    skills: list[str] = []
    if any(term in text for term in ["oidc", "cloud", "github actions", "ci/cd", "ci_cd", "aws", "azure", "gcp"]):
        skills.append("cloud-oidc-and-ci-cd-abuse-hunter")
    if any(term in text for term in ["browser", "frontend", "cdn", "javascript", "npm"]):
        skills.append("browser-side-supply-chain-exposure-analyst")
    if any(term in text for term in ["vscode", "open vsx", "extension", "developer tool", "ide"]):
        skills.append("developer-endpoint-forensics-runbooker")
    if profile.get("is_campaign_level") or profile.get("parent_campaign_id") not in [None, "", "none"]:
        skills.append("campaign-clustering-and-event-graph-builder")
    return skills


def hp_path(slug: str, filename: str) -> str:
    return f"~/hp-posts-info/{slug}/{filename}"


def base_task(
    *,
    slug: str,
    number: int,
    short_id: str,
    specialist: str,
    objective: str,
    artifact: str,
    acceptance_criteria: list[str],
    depends_on: list[str] | None = None,
    task_type: str = "halting_skill",
    blocks_publish: bool = True,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task = {
        "task_id": f"{slug}-{number:02d}-{short_id}",
        "task_type": task_type,
        "specialist": specialist,
        "objective": objective,
        "depends_on": depends_on or [],
        "artifact_path": hp_path(slug, artifact),
        "blocks_publish": blocks_publish,
        "acceptance_criteria": acceptance_criteria,
        "constraints": [
            "Do not invent package versions, timestamps, hashes, IOCs, victim counts, or attribution.",
            "Preserve unknown, not_observed, disputed, and inferred labels.",
            "Return structured JSON or YAML when the task contract defines a schema.",
            "Use canonical Next.js/Postgres publication assumptions; do not rely on Astro or D1 as the primary publication path.",
        ],
    }
    if extra:
        task.update(extra)
    return task


def make_tasks(profile_path: Path, profile: dict[str, Any]) -> dict[str, Any]:
    slug = slug_for(profile)
    event_name = profile.get("event_name") or profile.get("title") or slug

    tasks: list[dict[str, Any]] = [
        base_task(
            slug=slug,
            number=1,
            short_id="scope-gate",
            specialist="site-refresh-orchestrator",
            objective=f"Decide whether {event_name} is in Halting Problems supply-chain scope.",
            artifact="01-scope-gate.yaml",
            acceptance_criteria=[
                "Decision is one of in_scope, out_of_scope, or needs_primary_source.",
                "Supply-chain angle is stated using package, registry, CI/CD, provenance, developer tooling, cloud, browser, extension, or artifact criteria.",
                "Syndicated-only evidence is blocked unless a primary source is identified.",
            ],
        ),
        base_task(
            slug=slug,
            number=2,
            short_id="dedupe-and-disposition",
            specialist="site-feed-curator-and-dedupe-skill",
            objective=f"Decide whether {event_name} is new, duplicate, update_existing, campaign_child, or reject.",
            depends_on=[f"{slug}-01-scope-gate"],
            artifact="02-dedupe-disposition.yaml",
            acceptance_criteria=[
                "Disposition includes matched URLs, dedupe keys, event IDs, slugs, packages, advisories, and campaign IDs.",
                "Update decisions name the canonical existing slug.",
                "Campaign decisions cite hard correlation evidence, not date or ecosystem similarity alone.",
            ],
        ),
        base_task(
            slug=slug,
            number=3,
            short_id="evidence-plan",
            specialist="site-worker",
            objective=f"Create a source and artifact collection plan for {event_name}.",
            depends_on=[f"{slug}-02-dedupe-and-disposition"],
            artifact="03-evidence-plan.yaml",
            acceptance_criteria=[
                "Plan lists required primary sources, registry metadata, artifact downloads, advisories, commits, releases, tags, and telemetry assumptions.",
                "Each planned collection item includes why it is needed and what claim it can prove or disprove.",
                "Unsafe execution of untrusted code is explicitly forbidden.",
            ],
        ),
        base_task(
            slug=slug,
            number=4,
            short_id="research-packet",
            specialist="supply-chain-compromise-researcher",
            objective=f"Build the evidence-backed research packet and claim ledger for {event_name}.",
            depends_on=[f"{slug}-03-evidence-plan"],
            artifact="04-research-packet.md",
            acceptance_criteria=[
                "Every behavioral claim has source references and confidence.",
                "Observed facts, inference, and unknowns are separated.",
                "The packet includes a claim ledger with stable claim IDs.",
            ],
        ),
        base_task(
            slug=slug,
            number=5,
            short_id="artifact-provenance",
            specialist="supply-chain-artifact-diff-lab + provenance-and-publishing-integrity-auditor",
            objective=f"Verify artifact differences and publishing provenance for {event_name}.",
            depends_on=[f"{slug}-04-research-packet"],
            artifact="05-artifact-provenance.yaml",
            acceptance_criteria=[
                "Package, release, container, extension, action, or artifact identities are verified or marked unknown with a reason.",
                "Source-to-artifact, tag, signature, builder, registry, and timestamp evidence is captured when applicable.",
                "Conflicting artifact evidence is represented as a conflict block.",
            ],
        ),
        base_task(
            slug=slug,
            number=6,
            short_id="soc-actionability",
            specialist="soc-ir-enrichment-engineer",
            objective=f"Turn {event_name} into SOC and appsec audit recipes.",
            depends_on=[f"{slug}-04-research-packet", f"{slug}-05-artifact-provenance"],
            artifact="06-soc-actionability.yaml",
            acceptance_criteria=[
                "Hunts list telemetry source, fields, time windows, query text, and interpretation.",
                "Each audit recipe has positive, negative, and inconclusive result handling.",
                "Output answers whether a SOC analyst must clean any data before use.",
            ],
        ),
        base_task(
            slug=slug,
            number=7,
            short_id="ioc-package-normalization",
            specialist="ioc-normalizer-and-sharing-exporter",
            objective=f"Normalize IOCs, packages, versions, hashes, and repositories for {event_name}.",
            depends_on=[f"{slug}-04-research-packet"],
            artifact="07-iocs-and-packages.json",
            acceptance_criteria=[
                "Machine-readable IOCs are raw and parseable.",
                "Package coordinates include ecosystem, namespace, name, version/range, fixed version, and registry URL when known.",
                "Low-confidence observables are labeled and not mixed with confirmed IOCs.",
            ],
        ),
        base_task(
            slug=slug,
            number=8,
            short_id="script-pack",
            specialist="soc-ir-enrichment-engineer",
            objective=f"Create runnable scripts, fixtures, manifests, and tests for {event_name}.",
            depends_on=[f"{slug}-06-soc-actionability", f"{slug}-07-ioc-package-normalization"],
            artifact="scripts/",
            acceptance_criteria=[
                "Scripts live in the research repo under the event slug.",
                "Each script has a manifest, clean fixture, dirty fixture, and unit test.",
                "Scripts contain known incident constants and no forbidden placeholders.",
            ],
        ),
        base_task(
            slug=slug,
            number=9,
            short_id="downstream-impact",
            specialist="remediation-and-credential-rotation-planner",
            objective=f"Assess credential, CI/CD, cloud, registry, browser, and endpoint downstream impact for {event_name}.",
            depends_on=[f"{slug}-05-artifact-provenance", f"{slug}-06-soc-actionability"],
            artifact="09-downstream-impact.yaml",
            acceptance_criteria=[
                "Applicability decisions exist for registry, GitHub, cloud, endpoint, browser/CDN, and deployment modules.",
                "Credential rotation advice maps to specific token types or providers.",
                "Closure gates are testable and incident-specific.",
            ],
        ),
        base_task(
            slug=slug,
            number=10,
            short_id="detection-pack",
            specialist="detection-pack-generator",
            objective=f"Generate portable detection content for {event_name}.",
            depends_on=[f"{slug}-06-soc-actionability", f"{slug}-07-ioc-package-normalization"],
            artifact="10-detection-pack/",
            acceptance_criteria=[
                "Detections include KQL, SPL, Sigma, YARA, osquery, shell, or cloud queries only when applicable.",
                "Each detection lists required telemetry fields and false-positive guidance.",
                "Detection pack validator passes.",
            ],
        ),
        base_task(
            slug=slug,
            number=11,
            short_id="post-draft",
            specialist="supply-chain-compromise-technical-writer",
            objective=f"Draft the Halting Problems post for {event_name} from validated structured inputs.",
            depends_on=[
                f"{slug}-04-research-packet",
                f"{slug}-05-artifact-provenance",
                f"{slug}-06-soc-actionability",
                f"{slug}-07-ioc-package-normalization",
                f"{slug}-08-script-pack",
                f"{slug}-09-downstream-impact",
                f"{slug}-10-detection-pack",
            ],
            artifact="11-post-draft.md",
            acceptance_criteria=[
                "Narrative preserves operational details from specialist outputs.",
                "Every claim-heavy paragraph has nearby citations.",
                "Machine-readable blocks and prose defanging rules are followed.",
            ],
        ),
        base_task(
            slug=slug,
            number=12,
            short_id="schema-normalization",
            specialist="post-schema-normalizer-and-migrator",
            objective=f"Normalize final post schema and event profile for {event_name}.",
            depends_on=[f"{slug}-11-post-draft"],
            artifact="12-normalized-event-profile.json",
            acceptance_criteria=[
                "Event profile JSON is valid.",
                "Source count matches numbered sources.",
                "Normalized facts are ready for Postgres import.",
            ],
        ),
    ]

    for index, lane in enumerate(REQUIRED_AGENCY_REVIEW_LANES, start=13):
        tasks.append(
            base_task(
                slug=slug,
                number=index,
                short_id=lane["review_lane"].replace("_", "-"),
                specialist="agency-agent-reviewer",
                objective=lane["objective"],
                depends_on=[f"{slug}-12-schema-normalization"],
                artifact=f"{index:02d}-{lane['review_lane']}.yaml",
                task_type="agency_review",
                blocks_publish=lane["blocks_publish"],
                acceptance_criteria=[
                    "Review output follows agency_review_result schema.",
                    "Reviewer directly answers assigned critique questions.",
                    "Blocking findings include exact upstream task IDs and artifact paths.",
                ],
                extra={
                    "review_lane": lane["review_lane"],
                    "agent_profile_path": lane["agent_profile_path"],
                },
            )
        )

    review_ids = [item["task_id"] for item in tasks if item["task_type"] == "agency_review"]
    tasks.append(
        base_task(
            slug=slug,
            number=18,
            short_id="synthesis-conflict-resolution",
            specialist="site-worker",
            objective=f"Merge specialist and agency-agent outputs for {event_name}; resolve conflicts explicitly.",
            depends_on=review_ids,
            artifact="18-synthesis-conflicts.yaml",
            acceptance_criteria=[
                "All blocking reviewer findings are fixed or carried as blocking gaps.",
                "Conflicting claims are not averaged; they are resolved or marked disputed.",
                "Final result preserves reviewer warnings.",
            ],
        )
    )
    tasks.append(
        base_task(
            slug=slug,
            number=19,
            short_id="publishability-gate",
            specialist="site-worker",
            objective=f"Decide whether {event_name} is publish_ready, needs_review, reject, update_existing, attach_to_campaign, or duplicate.",
            depends_on=[f"{slug}-18-synthesis-conflict-resolution"],
            artifact="19-publishability-gate.yaml",
            acceptance_criteria=[
                "No required agency-agent review lane has decision block.",
                "Postgres import readiness is confirmed for sources, claims, evidence, package facts, IOCs, scripts, detections, and remediation gates.",
                "Next.js/API/feed compatibility is confirmed; Astro and D1 are not treated as canonical publication targets.",
                "If blocked, exact collection or fix steps are listed.",
            ],
        )
    )

    return {
        "site_worker_plan_version": "2.0",
        "event_id": slug,
        "event_name": event_name,
        "profile_path": str(profile_path),
        "canonical_publication_target": "nextjs-postgres",
        "legacy_paths_disallowed": ["astro", "d1-primary", "static-primary"],
        "critique_question_bank": "skills/site-worker/references/agent-pipeline-critique-questions.md",
        "agency_review_lanes": "skills/site-worker/references/agency-agent-review-lanes.md",
        "run_ledger_schema": "skills/site-worker/references/site-worker-run-ledger-schema.json",
        "optional_halting_skills": infer_optional_halting_skills(profile),
        "tasks": tasks,
        "final_validation": [
            "validate modular task dependencies",
            "validate agency-agent review results",
            "validate raw machine-readable IOCs",
            "validate package coordinates",
            "validate claim evidence coverage",
            "validate script fixtures and tests",
            "validate Postgres import readiness",
            "validate Next.js feed/API output",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event_profile", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    profile = load_profile(args.event_profile)
    plan = make_tasks(args.event_profile, profile)
    data = json.dumps(plan, indent=2, sort_keys=False)
    if args.output:
        args.output.write_text(data + "\n", encoding="utf-8")
    else:
        print(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
