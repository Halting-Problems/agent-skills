# Reddit syndication via `reddit_user_crossposter`

Use this when a Halting Problems publishing workflow should automatically post newly published site articles to Reddit as the user's account after deploy.

## Working pattern

- Trigger the Reddit poster only after a new site post is successfully published and deployed.
- Current runner path:
  `/home/sam/halting-problems/repos/haltingproblems.com/integrations/reddit/user-crossposter/run_sync.sh --max-items 1`
- Current feed source:
  `https://haltingproblems.com/feed.xml`
- Current target automation is narrowed to:
  `r/cybersecurity`

## Important config details

- For direct posting into the destination subreddit instead of posting to the user profile first and then crossposting, set:
  `REDDIT_SOURCE_SUBREDDIT=cybersecurity`
- For required flair on `r/cybersecurity`, configure:
  `REDDIT_TARGET_FLAIR_IDS=cybersecurity=dee83b36-c726-11eb-84d2-0e25ae66cff3`
- If the Reddit user-agent contains spaces, quote it in `.env` so `run_sync.sh` can safely `source` the file:
  `REDDIT_USER_AGENT='haltingproblems-reddit-crossposter/0.1 by u/halting_problems'`

## Posting behavior implemented in the runner

- When the source subreddit and only target subreddit are the same normalized subreddit, the runner should submit directly into that subreddit instead of creating a source-profile post and crossposting.
- PRAW `Submission.crosspost(...)` accepts `flair_id`, so flair can also be supplied on crossposts when needed.

## Rollout pitfall

When enabling automation after one or more manual Reddit posts already exist, seed the dedupe state file before turning the cron job loose, or the next run may repost the latest already-published article.

Current state file path:
- `~/.local/state/haltingproblems-reddit-crossposter.json`

Seed at minimum:
- `posted_keys` entries like `cybersecurity::<article-guid>`
- `source_posts` mapping of article guid to the existing Reddit submission id when known

## Temporarily disabling syndication

When Sam asks to pause or disable Reddit syndication, update the publisher cron prompt rather than pausing the whole site refresh pipeline. Keep discovery and publishing enabled, but add explicit negative instructions to the publisher job:

- Do not run the Reddit user crossposter.
- Do not call `integrations/reddit/user-crossposter/run_sync.sh`.
- Do not post, crosspost, or syndicate new Halting Problems articles to Reddit.
- If a new article is published, report that Reddit syndication is intentionally disabled.

Verify the cron prompt no longer contains the old automatic `run_sync.sh --max-items 1` instruction and does contain the disabled notice.

## Verification pattern

1. Run unit tests for `integrations/reddit/user-crossposter`.
2. Run `./run_sync.sh --dry-run --max-items 1` with the real state file to confirm no duplicate post is planned.
3. Run a second dry-run against a temporary empty `{}` state file to confirm the newest feed item would be selected for Reddit posting.
4. Only then enable or update the publisher cron workflow that invokes the runner after deploy.
