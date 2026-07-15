#!/usr/bin/env python3
"""Create an adaptive, executable Halting Problems site-worker task graph."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
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

RUNNERS = {"halting_skill", "agency_review", "command", "gate"}
TASK_ARTIFACT_SCHEMA = "skills/site-worker/references/site-worker-task-artifact.schema.json"
DECISION_ARTIFACT_SCHEMA = "skills/site-worker/references/site-worker-decision-artifact.schema.json"
COMMAND_ARTIFACT_SCHEMA = "skills/site-worker/references/site-worker-command-artifact.schema.json"


def load_profile(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def slug_for(profile: dict[str, Any]) -> str:
    value = str(profile.get("existing_slug") or profile.get("event_id") or profile.get("candidate_id") or "unknown-event").strip()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValueError("event_id/existing_slug must be lowercase kebab-case")
    return value


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def applicability(profile: dict[str, Any]) -> dict[str, bool]:
    assets_value = profile.get("affected_assets")
    assets: dict[str, Any] = assets_value if isinstance(assets_value, dict) else {}
    fields = [
        *_strings(profile.get("attack_types")),
        *_strings(profile.get("tags")),
        *_strings(profile.get("exploitation_evidence")),
        *_strings(profile.get("attacker_iocs")),
        *_strings(assets.get("ecosystems")),
        *_strings(assets.get("credentials_at_risk")),
        *_strings(assets.get("developer_tools")),
        *_strings(assets.get("platforms")),
    ]
    text = " ".join(fields).lower()
    ecosystems = {item.lower() for item in _strings(assets.get("ecosystems"))}
    package_terms = {"npm", "pypi", "rubygems", "nuget", "maven", "cargo", "crates", "package", "registry"}
    package = bool(ecosystems & package_terms) or any(term in text for term in package_terms)
    artifact = package and any(term in text for term in ["compromise", "malicious", "tamper", "backdoor", "dependency confusion"])
    artifact = artifact or any(term in text for term in ["artifact tamper", "container compromise", "signed artifact", "action compromise", "extension compromise"])
    cloud = any(term in text for term in ["oidc", "cloud", "github actions", "ci/cd", "ci_cd", "aws", "azure", "gcp"])
    browser = any(term in text for term in ["browser", "frontend", "front-end", "cdn", "magecart", "web skimmer", "javascript supply chain"])
    endpoint = bool(_strings(assets.get("developer_tools"))) or any(
        term in text for term in ["developer tool", "ide", "vscode", "open vsx", "endpoint", "workstation"]
    )
    endpoint = endpoint or (package and any(term in text for term in ["compromise", "malicious", "credential theft", "token theft"]))
    credential = bool(_strings(assets.get("credentials_at_risk"))) or any(
        term in text for term in ["credential", "token theft", "secret theft", "api key", "session theft"]
    )
    campaign = bool(profile.get("is_campaign_level")) or profile.get("parent_campaign_id") not in [None, "", "none"]
    detection = bool(_strings(profile.get("attacker_iocs"))) or any(
        term in text for term in ["compromise", "malicious", "malware", "backdoor", "active exploitation", "known exploited", "credential theft"]
    )
    # A generic KEV record alone does not justify a bespoke detection pack.
    if text.strip() == "known exploited vulnerability":
        detection = False
    return {
        "registry": package,
        "artifact_diff": artifact,
        "provenance": artifact,
        "cloud": cloud,
        "browser": browser,
        "endpoint": endpoint,
        "campaign": campaign,
        "credential_impact": credential,
        "detection": detection,
    }


def infer_optional_halting_skills(profile: dict[str, Any]) -> list[str]:
    rules = applicability(profile)
    mapping = [
        ("cloud", "cloud-oidc-and-ci-cd-abuse-hunter"),
        ("browser", "browser-side-supply-chain-exposure-analyst"),
        ("endpoint", "developer-endpoint-forensics-runbooker"),
        ("campaign", "campaign-clustering-and-event-graph-builder"),
        ("artifact_diff", "supply-chain-artifact-diff-lab"),
        ("provenance", "provenance-and-publishing-integrity-auditor"),
        ("detection", "detection-pack-generator"),
    ]
    return [skill for rule, skill in mapping if rules[rule]]


def make_tasks(
    profile_path: Path,
    profile: dict[str, Any],
    *,
    artifact_root: Path | None = None,
) -> dict[str, Any]:
    slug = slug_for(profile)
    event_name = str(profile.get("event_name") or profile.get("title") or slug)
    profile_path = profile_path.resolve()
    profile_content_hash = hashlib.sha256(profile_path.read_bytes()).hexdigest()
    artifact_root = (artifact_root or Path(f"/home/sam/hp-posts-info/{slug}")).expanduser().resolve()
    rules = applicability(profile)
    tasks: list[dict[str, Any]] = []
    by_name: dict[str, dict[str, Any]] = {}

    def add(
        name: str,
        *,
        runner: str,
        specialist: str,
        objective: str,
        artifact: str,
        depends: list[str] | None = None,
        acceptance: list[str],
        blocks_publish: bool = True,
        artifact_schema: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if runner not in RUNNERS:
            raise ValueError(f"unknown runner: {runner}")
        dependencies = [by_name[item] for item in (depends or [])]
        if artifact_schema is not None:
            expected_schema = artifact_schema
        elif runner == "command":
            expected_schema = COMMAND_ARTIFACT_SCHEMA
        elif runner == "gate":
            expected_schema = DECISION_ARTIFACT_SCHEMA
        elif artifact.endswith(".json"):
            expected_schema = TASK_ARTIFACT_SCHEMA
        else:
            expected_schema = ""
        task = {
            "task_id": f"{slug}-{len(tasks) + 1:02d}-{name}",
            "runner": runner,
            "task_type": runner,
            "specialist": specialist,
            "objective": objective,
            "inputs": [str(profile_path)] if not dependencies else [item["artifact_path"] for item in dependencies],
            "artifact_path": str(artifact_root / artifact),
            "artifact_schema": expected_schema,
            "depends_on": [item["task_id"] for item in dependencies],
            "blocks_publish": blocks_publish,
            "status": "pending",
            "acceptance_criteria": acceptance,
            "constraints": [
                "Do not invent versions, timestamps, hashes, IOCs, victim counts, or attribution.",
                "Preserve unknown, not_observed, disputed, and inferred labels.",
                "Use Next.js/Postgres as publication authority; D1 may only be an explicitly versioned read replica.",
            ],
        }
        if extra:
            task.update(extra)
        tasks.append(task)
        by_name[name] = task
        return task

    add(
        "scope-gate", runner="gate", specialist="site-refresh-orchestrator",
        objective=f"Decide whether {event_name} is in Halting Problems scope.", artifact="01-scope-gate.json",
        acceptance=["Decision is in_scope, out_of_scope, or needs_primary_source.", "Syndicated-only evidence is blocked."],
    )
    add(
        "dedupe-and-disposition", runner="gate", specialist="site-feed-curator-and-dedupe-skill",
        objective=f"Select new, update, campaign, duplicate, review, or reject disposition for {event_name}.",
        artifact="02-dedupe-disposition.json", depends=["scope-gate"],
        acceptance=["Matched slugs and dedupe keys are recorded.", "Update decisions name the existing slug."],
    )
    add(
        "evidence-plan", runner="halting_skill", specialist="site-worker",
        objective=f"Create a bounded evidence collection plan for {event_name}.", artifact="03-evidence-plan.json",
        depends=["dedupe-and-disposition"], acceptance=["Every collection item names the claim it can prove.", "Unsafe execution is forbidden."],
    )
    add(
        "research-packet", runner="halting_skill", specialist="supply-chain-compromise-researcher",
        objective=f"Build a sourced claim ledger for {event_name}.", artifact="04-research-packet.json",
        depends=["evidence-plan"], acceptance=["Claims have sources and confidence.", "Facts, inference, and unknowns are separated."],
    )

    optional_outputs: list[str] = []
    if rules["registry"]:
        add(
            "registry-analysis", runner="halting_skill", specialist="soc-ir-enrichment-engineer",
            objective=f"Verify registry package coordinates and version history for {event_name}.", artifact="registry-analysis.json",
            depends=["research-packet"], acceptance=["Registry coordinates and version evidence are explicit."],
        )
        optional_outputs.append("registry-analysis")
    if rules["artifact_diff"]:
        dependencies = ["research-packet"] + (["registry-analysis"] if rules["registry"] else [])
        add(
            "artifact-diff", runner="halting_skill", specialist="supply-chain-artifact-diff-lab",
            objective=f"Compare trusted and suspect artifacts for {event_name}.", artifact="artifact-diff.json",
            depends=dependencies, acceptance=["Artifact identities and reproducible differences are recorded."],
        )
        optional_outputs.append("artifact-diff")
    if rules["provenance"]:
        add(
            "provenance-audit", runner="halting_skill", specialist="provenance-and-publishing-integrity-auditor",
            objective=f"Audit source-to-artifact provenance for {event_name}.", artifact="provenance-audit.json",
            depends=["artifact-diff"], acceptance=["Tags, signatures, builders, and registry timestamps are verified or unknown."],
        )
        optional_outputs.append("provenance-audit")
    for rule, name, specialist, artifact, objective in [
        ("cloud", "cloud-oidc-audit", "cloud-oidc-and-ci-cd-abuse-hunter", "cloud-oidc-audit.json", "Audit CI/CD, cloud, and OIDC downstream abuse."),
        ("browser", "browser-exposure", "browser-side-supply-chain-exposure-analyst", "browser-exposure.json", "Assess browser and CDN exposure."),
        ("endpoint", "endpoint-forensics", "developer-endpoint-forensics-runbooker", "endpoint-forensics.json", "Build developer endpoint triage guidance."),
        ("campaign", "campaign-graph", "campaign-clustering-and-event-graph-builder", "campaign-graph.json", "Build and validate campaign relationships."),
        ("credential_impact", "credential-impact", "remediation-and-credential-rotation-planner", "credential-impact.json", "Map exposed credentials to rotation and closure gates."),
    ]:
        if rules[rule]:
            add(
                name, runner="halting_skill", specialist=specialist,
                objective=f"{objective} Event: {event_name}.", artifact=artifact,
                depends=["research-packet"], acceptance=["Applicability and evidence are explicit.", "Unknowns remain blocking when required."],
            )
            optional_outputs.append(name)

    normalization_dependencies = ["research-packet"] + [name for name in ["registry-analysis", "artifact-diff"] if name in by_name]
    add(
        "ioc-package-normalization", runner="halting_skill", specialist="ioc-normalizer-and-sharing-exporter",
        objective=f"Normalize IOCs, package coordinates, hashes, and repositories for {event_name}.", artifact="iocs-and-packages.json",
        depends=normalization_dependencies, acceptance=["Raw machine-readable IOCs are typed and deduplicated.", "Package coordinates separate names from versions."],
    )
    soc_dependencies = ["research-packet"] + optional_outputs
    add(
        "soc-actionability", runner="halting_skill", specialist="soc-ir-enrichment-engineer",
        objective=f"Create testable SOC/AppSec audit recipes for {event_name}.", artifact="soc-actionability.json",
        depends=soc_dependencies, acceptance=["Hunts name telemetry, fields, windows, and interpretation.", "Positive, negative, and inconclusive outcomes are defined."],
    )
    if rules["detection"]:
        add(
            "detection-pack", runner="halting_skill", specialist="detection-pack-generator",
            objective=f"Generate applicable detection content for {event_name}.", artifact="detection-pack.json",
            depends=["ioc-package-normalization", "soc-actionability"], acceptance=["Every detection names telemetry and false positives."],
        )
        add(
            "script-pack", runner="command", specialist="soc-ir-enrichment-engineer",
            objective=f"Materialize and test hunt scripts for {event_name}.", artifact="script-pack-results.json",
            depends=["detection-pack", "soc-actionability"], acceptance=["Scripts, manifests, fixtures, and focused tests pass."],
            extra={"command": ["python", "-m", "pytest", str(artifact_root / "tests"), "-q"]},
        )

    draft_dependencies = ["research-packet", "ioc-package-normalization", "soc-actionability"] + optional_outputs
    if rules["detection"]:
        draft_dependencies += ["detection-pack", "script-pack"]
    add(
        "post-draft", runner="halting_skill", specialist="supply-chain-compromise-technical-writer",
        objective=f"Draft the source-backed Halting Problems analysis for {event_name}.", artifact="post-draft.md",
        depends=list(dict.fromkeys(draft_dependencies)), acceptance=["Operational details are preserved.", "Claim-heavy prose has nearby citations."],
    )
    add(
        "schema-normalization", runner="halting_skill", specialist="post-schema-normalizer-and-migrator",
        objective=f"Normalize the final event profile for {event_name}.", artifact="normalized-event-profile.json",
        depends=["post-draft"], acceptance=["Normalized data is ready for selected-slug Postgres import."],
    )

    review_names: list[str] = []
    for lane in REQUIRED_AGENCY_REVIEW_LANES:
        name = lane["review_lane"].replace("_", "-")
        add(
            name, runner="agency_review", specialist="agency-agent-reviewer", objective=lane["objective"],
            artifact=f"reviews/{lane['review_lane']}.json", depends=["schema-normalization"],
            acceptance=["Decision is pass, pass_with_warnings, or block.", "Blocking findings identify task IDs and artifact paths."],
            blocks_publish=lane["blocks_publish"],
            extra={"review_lane": lane["review_lane"], "agent_profile_path": lane["agent_profile_path"]},
        )
        review_names.append(name)

    add(
        "synthesis-conflict-resolution", runner="gate", specialist="site-worker",
        objective=f"Resolve specialist and reviewer conflicts for {event_name}.", artifact="synthesis-conflicts.json",
        artifact_schema=DECISION_ARTIFACT_SCHEMA,
        depends=review_names, acceptance=["Blocking findings are fixed or remain explicit blockers.", "Warnings are preserved."],
    )
    add(
        "postgres-import-dry-run", runner="command", specialist="site-worker",
        objective=f"Dry-run the selected-slug Postgres import for {event_name}.", artifact="postgres-import-dry-run.json",
        depends=["schema-normalization", "synthesis-conflict-resolution"], acceptance=["Dry-run succeeds without mutating Postgres."],
        extra={
            "command": [
                "pnpm",
                "exec",
                "tsx",
                "tooling/content/import-posts-info-to-postgres.ts",
                "--posts-info-dir",
                str(artifact_root.parent),
                "--slug",
                slug,
                "--dry-run",
            ]
        },
    )
    add(
        "postgres-import", runner="command", specialist="site-worker",
        objective=f"Execute the selected-slug Postgres import for {event_name}.", artifact="postgres-import-result.json",
        depends=["postgres-import-dry-run"], acceptance=["Selected slug imports exactly once from tested artifacts."],
        extra={
            "command": [
                "pnpm",
                "exec",
                "tsx",
                "tooling/content/import-posts-info-to-postgres.ts",
                "--posts-info-dir",
                str(artifact_root.parent),
                "--slug",
                slug,
            ]
        },
    )
    add(
        "production-verification", runner="gate", specialist="site-worker",
        objective=f"Verify the production threat page, feed, and search results for {event_name}.", artifact="production-verification.json",
        depends=["postgres-import"], acceptance=["Threat page, feed, and search expose the imported source version."],
    )
    add(
        "publishability-gate", runner="gate", specialist="site-worker",
        objective=f"Decide whether {event_name} can be published.", artifact="publishability-gate.json",
        artifact_schema=DECISION_ARTIFACT_SCHEMA,
        depends=["synthesis-conflict-resolution", "postgres-import", "production-verification"],
        acceptance=["No required review is blocked.", "Postgres import and production verification completed for this source version."],
    )

    return {
        "site_worker_plan_version": "3.0",
        "event_id": slug,
        "event_name": event_name,
        "profile_path": str(profile_path),
        "profile_content_hash": profile_content_hash,
        "artifact_root": str(artifact_root),
        "source_item_key": str(profile.get("source_item_key") or profile.get("sourceItemKey") or "unknown"),
        "source_version_hash": str(profile.get("source_version_hash") or profile.get("sourceVersionHash") or "unknown"),
        "source_version_at": str(
            profile.get("source_version_at")
            or profile.get("sourceVersionAt")
            or profile.get("updated_at")
            or profile.get("firstSeenAt")
            or ""
        ),
        "canonical_publication_target": "nextjs-postgres",
        "legacy_paths_disallowed": ["d1-primary", "static-primary"],
        "run_ledger_schema": "skills/site-worker/references/site-worker-run-ledger-schema.json",
        "applicability": rules,
        "optional_halting_skills": infer_optional_halting_skills(profile),
        "tasks": tasks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event_profile", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--artifact-root", type=Path, help="Trusted output root override")
    args = parser.parse_args()
    plan = make_tasks(
        args.event_profile,
        load_profile(args.event_profile),
        artifact_root=args.artifact_root,
    )
    data = json.dumps(plan, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data + "\n", encoding="utf-8")
    else:
        print(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
