#!/usr/bin/env python3
"""Discover analysis URLs from a Halting Problems style site.

Usage:
  python discover_site_posts.py https://haltingproblems.com/
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.links.append(value)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "haltingproblems-source-watcher/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    args = parser.parse_args()

    html = fetch(args.base_url)
    parser_obj = LinkParser()
    parser_obj.feed(html)

    base_host = urlparse(args.base_url).netloc
    urls = sorted({
        urljoin(args.base_url, href)
        for href in parser_obj.links
        if "/analysis/" in href
    })
    urls = [u for u in urls if urlparse(u).netloc == base_host]

    candidates = []
    for url in urls:
        slug = url.rstrip("/").split("/")[-1]
        candidates.append({
            "candidate_id": slug,
            "title": slug.replace("-", " "),
            "url": url,
            "dedupe_keys": [f"slug:{slug}"],
            "suggested_next_skill": "supply-chain-compromise-researcher",
        })

    print(json.dumps({"candidate_incidents": candidates}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
