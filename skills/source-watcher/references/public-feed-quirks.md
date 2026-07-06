# Public feed quirks for supply-chain source discovery

Session note from 2026-06-20 discovery/dedupe cron.

## RSS/Atom date parsing

For RSS `pubDate` values like `Fri, 19 Jun 2026 20:44:48 GMT`, prefer Python's `email.utils.parsedate_to_datetime()` instead of hand-rolled `datetime.strptime()` format lists. It handles common RFC 2822 variants used by security blogs.

## Known feed endpoints confirmed in this session

- StepSecurity blog RSS: `https://www.stepsecurity.io/blog/rss.xml`
- Sonatype blog RSS: `https://www.sonatype.com/blog/rss.xml`
- Socket blog Atom: `https://socket.dev/api/blog/feed.atom`
  - Do not assume `https://socket.dev/blog/rss.xml`; it returned 404 in this session.
  - Canonicalize feed links before dedupe because Socket appends tracking parameters such as `?utm_medium=feed`.

## Feedless or irregular sources

- JFrog Research did not expose a straightforward `/feed/` endpoint in this session.
- Fallback approach: inspect the homepage and sitemap for `/post/` URLs, then fetch the candidate post pages and extract visible publication dates or structured metadata before classifying them as in-window candidates.
- Treat missing feed support as a reason to switch discovery method, not as a reason to drop the source.

## Windowing reminder

A 4-hour refresh window can legitimately produce zero candidates even when sources are healthy. Report a clean zero-result discovery summary instead of fabricating survivors from older posts.
