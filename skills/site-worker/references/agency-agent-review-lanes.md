# Agency-Agent Review Lanes

These lanes use role definitions from `/home/sam/agency-agents`. The site-worker planner should emit review tasks that quote the `agent_profile_path` so the orchestrator can load the correct agent profile before review.

## Required Lanes

| Lane ID | Agency Agent Profile | Purpose | Blocks Publish |
| --- | --- | --- | --- |
| `architecture_review` | `/home/sam/agency-agents/engineering/engineering-multi-agent-systems-architect.md` | Review topology, dependency graph, failure handling, context boundaries, partial-result handling, and observability. | yes |
| `data_quality_review` | `/home/sam/agency-agents/engineering/engineering-ai-data-remediation-engineer.md` | Review malformed facts, normalization gaps, zero-data-loss assumptions, quarantine paths, and auditability of data corrections. | yes |
| `incident_response_review` | `/home/sam/agency-agents/security/security-incident-responder.md` | Review whether hunts, containment, evidence handling, and remediation gates are usable by incident responders. | yes |
| `workflow_qa_review` | `/home/sam/agency-agents/testing/testing-workflow-optimizer.md` | Review whether the chained workflow is testable, modular, and free of avoidable handoff ambiguity. | yes |
| `technical_writing_review` | `/home/sam/agency-agents/engineering/engineering-technical-writer.md` | Review whether final output is clear, source-backed, non-decorative, and operationally useful. | no |

## Optional Lanes

| Lane ID | Agency Agent Profile | Trigger |
| --- | --- | --- |
| `api_contract_review` | `/home/sam/agency-agents/testing/testing-api-tester.md` | Use when feed/API output changes or Postgres import/export behavior changes. |
| `evidence_collection_review` | `/home/sam/agency-agents/testing/testing-evidence-collector.md` | Use when source evidence, snapshots, hashes, or source retrieval are weak. |
| `reality_check_review` | `/home/sam/agency-agents/testing/testing-reality-checker.md` | Use when claims sound plausible but lack direct proof or contradict source material. |
| `devops_review` | `/home/sam/agency-agents/engineering/engineering-devops-automator.md` | Use when cron, deployment, Cloudflare, or scheduled refresh behavior changes. |

## Review Output Contract

Each agency-agent review task must return:

```yaml
agency_review_result:
  lane_id: ""
  agent_profile_path: ""
  decision: "pass|pass_with_warnings|block"
  confidence: "high|medium|low"
  blocking_findings: []
  warnings: []
  required_fixes: []
  evidence_references: []
  reviewer_summary: ""
```

## Merge Rule

Publishing is blocked when any required lane returns `block`. Warnings must be preserved in the final `site_worker_result` and attached to the run ledger.
