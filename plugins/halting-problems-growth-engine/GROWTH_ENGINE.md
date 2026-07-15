# Halting Problems Growth Engine

## Mission

The Halting Problems Growth Engine is a tailored Agency Agents pack for growing, scaling, and marketing `/home/sam/halting-problems/repos/haltingproblems.com` without weakening the site's threat-intelligence quality bar.

It turns each canonical Halting Problems incident, campaign, or capability update into a repeatable growth loop:

1. Publish or update the canonical source of truth.
2. Verify the site, feed, search, and canonical database outputs.
3. Extract SEO opportunities and internal links.
4. Repurpose the article into channel-native social, Reddit, newsletter, and partner/community assets.
5. Queue safe experiments with explicit metrics and approval gates.
6. Review results weekly and update the backlog.

## Site Context

- Primary repo: `/home/sam/halting-problems/repos/haltingproblems.com`.
- Canonical post authoring repo: `/home/sam/halting-problems/repos/hp-posts-info`.
- Canonical serving path: `hp-posts-info/<slug>/` → Postgres importer → Next.js/Postgres pages and APIs.
- Legacy Astro/D1/static paths are migration references unless a task explicitly targets them.
- Subscriber storage: Cloudflare D1 table `subscribers` exists, but marketing email requires consent, sender authentication, and explicit approval before sending.
- Known channel preference: Sam wants new Halting Problems posts syndicated to security subreddits; r/cybersecurity is a confirmed target from prior workflow history.

## Selected Agency Agents

| Slug | Agency Agent | Source | Job in this pack |
|---|---|---|---|
| `growth-hacker` | Growth Hacker | `/home/sam/agency-agents/marketing/marketing-growth-hacker.md` | Owns experiment backlog, funnel hypotheses, acquisition loops, and weekly learning reviews. |
| `seo-specialist` | SEO Specialist | `/home/sam/agency-agents/marketing/marketing-seo-specialist.md` | Owns technical SEO, topic clusters, structured data, search intent, and cannibalization checks. |
| `content-creator` | Content Creator | `/home/sam/agency-agents/marketing/marketing-content-creator.md` | Owns repurposing articles into platform-specific narratives and editorial calendars. |
| `social-media-strategist` | Social Media Strategist | `/home/sam/agency-agents/marketing/marketing-social-media-strategist.md` | Owns LinkedIn/X/professional campaign strategy and channel-native distribution. |
| `email-marketing-strategist` | Email Marketing Strategist | `/home/sam/agency-agents/marketing/marketing-email-strategist.md` | Owns subscriber segmentation, lifecycle flows, deliverability, and compliance gates. |
| `analytics-reporter` | Analytics Reporter | `/home/sam/agency-agents/support/support-analytics-reporter.md` | Owns metrics snapshots, dashboards, deltas, and growth reporting. |
| `engineering-devops-automator` | DevOps Automator | `/home/sam/agency-agents/engineering/engineering-devops-automator.md` | Owns cron, deploy, workflow reliability, and automation guardrails. |
| `agentic-search-optimizer` | Agentic Search Optimizer | `/home/sam/agency-agents/marketing/marketing-agentic-search-optimizer.md` | Owns LLM/browser-agent discoverability and machine-readable site affordances. |

When using Hermes, prefer the existing `agency-agents-router` plugin for lazy routing. Search first, then load/delegate only the specialists needed for the current work order.

## Operating Modes

### `publish_amplification`

Use immediately after a new post or canonical update is verified live.

Output:

```yaml
growth_work_order:
  mode: publish_amplification
  article_slug: ""
  canonical_url: ""
  required_agents:
    - content-creator
    - social-media-strategist
    - seo-specialist
    - growth-hacker
  channel_assets:
    reddit:
      subreddits: []
      title_options: []
      body: ""
      approval_required: true
    linkedin:
      post: ""
      approval_required: true
    x:
      thread: []
      approval_required: true
    newsletter:
      subject_options: []
      segment: "subscribers with relevant consent"
      approval_required: true
  validation:
    - verify canonical article URL
    - verify /api/feed includes article
    - verify /api/search?q=<known-term> finds article
  gates:
    - explicit_human_approval
    - no automatic posting
```

### `seo_backlog`

Use weekly or after several posts ship.

Focus:
- Sitemap and robots health.
- Indexable canonical URLs.
- Article title/meta/open graph quality.
- Topic cluster gaps around supply-chain compromise, malicious packages, CI/CD abuse, developer tooling compromise, cloud credential exposure, and browser-side supply chain exposure.
- Internal links from related posts to canonical campaign/incident pages.
- Structured data opportunities for `Article`, `BreadcrumbList`, and security/threat-intel metadata where appropriate.

### `subscriber_lifecycle`

Use when improving subscriber capture or lifecycle email.

Rules:
- Lead with segment definitions and consent basis.
- Never send broadcast marketing email by default.
- Every sequence has exit conditions: unsubscribe, hard bounce, complaint, conversion, inactivity threshold.
- Open rates are directional only; optimize for CTR, CTOR, conversion, and retention.
- Do not use the D1 `subscribers` table for sending until sender authentication and compliance are verified.

### `weekly_growth_review`

Use on a recurring schedule to create a human-reviewable growth report.

Inputs:
- Recent published/updated posts.
- Feed/search/API health.
- Subscriber counts and growth if accessible.
- Social syndication actions actually performed.
- Search and referral metrics if analytics credentials are available.

Output:
- What shipped.
- What grew.
- What failed or was blocked.
- Next 3 experiments with owner agent, hypothesis, metric, and stop condition.

### `full_growth_audit`

Use monthly or when resetting strategy.

Covers:
- Site positioning and audience.
- SEO technical baseline.
- Content clusters and gaps.
- Social and community distribution.
- Subscriber capture and lifecycle.
- Automation reliability.
- Agentic discoverability.

## Safety Boundaries

- No automatic posting, crossposting, DMing, emailing, or ad spend without explicit human approval.
- No black-hat SEO: no link schemes, cloaking, keyword stuffing, doorway pages, hidden text, or fake engagement.
- Do not invent analytics, rankings, subscriber counts, or conversion metrics. If credentials/data are unavailable, mark metrics as `unknown` and list the collection step.
- Do not let growth workflows create duplicate incident posts. Halting Problems keeps each original post as the canonical source of truth; follow-up developments update the canonical existing post.
- Preserve technical specificity. Marketing outputs must not flatten IOCs, detection logic, or remediation guidance into generic copy.
- Social and Reddit drafts must be community-native, non-spammy, and transparent about affiliation when appropriate.
- Email work must include consent, unsubscribe, suppression, bounce, and complaint handling.

## Standard Agent Routing

### Hermes

1. Load this skill: `halting-problems-growth-engine`.
2. Use `hp_growth_engine_plan` to produce the work order when the plugin is loaded.
3. Use `agency-agents-router` lazily:
   - `agency_agents_search` for the role if uncertain.
   - `agency_agents_load` with `agent: <slug>` for one specialist prompt.
   - `agency_agents_delegate` for bounded specialist review tasks.

### Codex

Reference the custom agent:

```text
Use the Halting Problems Growth Engine agent to create a publish_amplification work order for <slug>.
```

For specialist review, reference Agency Agents by name:

```text
Use the SEO Specialist and Growth Hacker agents to review this growth backlog.
```

### Antigravity

Reference the skill:

```text
Use the halting-problems-growth-engine skill to run a weekly_growth_review for /home/sam/halting-problems/repos/haltingproblems.com.
```

## Verification Commands

From `/home/sam/halting-problems/repos/haltingproblems.com`, use these when relevant:

```bash
pnpm check
pnpm test
pnpm build
pnpm exec tsx tooling/content/import-posts-info-to-postgres.ts --posts-info-dir ../hp-posts-info --dry-run
curl -fsS http://localhost:3000/api/feed
curl -fsS 'http://localhost:3000/api/search?q=<known-term>'
```

Do not claim a growth automation, publish flow, or channel asset is ready until the relevant validation output has been inspected.
