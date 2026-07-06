# Feed package and IOC export pitfall

When changing `/api/feed`, verify it exports operational detail, not just incident summaries.

## Durable lesson

The feed can look healthy while silently dropping useful rows:

- affected packages with no exact version/range were previously skipped
- IOC/observable facts were not included in the feed at all

For defender/SIEM use, the feed should include every affected package row and every observable row available from Postgres.

## Expected feed shape

Each entry should include:

- `affected[]`: all affected package facts
  - include package rows even when version data is unknown
  - use an explicit unknown-version event instead of dropping the package
- `iocs[]`: all observable facts
  - `type`
  - `value`
  - `defanged`
  - `role`
  - `confidence`

## Regression test pattern

Add or update a CTI data test where one incident has:

1. at least two package rows
2. one package row with exact version data
3. one package row with no exact/range version data
4. at least two observable rows

The test should fail if:

- a package without version data is dropped
- `iocs` is absent or empty
- the feed uses the incident slug as a fake package name

## Production verification pattern

After deploy, fetch `/api/feed` with a browser-like user agent and spot-check known rich incidents:

```text
leo-platform-npm-miasma-compromise: affected package count should include the full package set and IOCs should be non-empty
hades-pypi-graph-ml-memory-scraper: affected package count and IOC count should be non-empty and large enough to reflect the post detail page
actions-cool-github-actions-tag-hijack: affected packages and IOCs should both be present
```

Do not treat a `200` response or the correct entry count as enough. Check package and IOC counts plus representative values.