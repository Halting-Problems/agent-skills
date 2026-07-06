#!/usr/bin/env python3
"""Defang network IOCs in prose/YAML text.

Usage:
  python defang_iocs.py input.md > defanged.md
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def defang(text: str) -> str:
    text = re.sub(r"https://", "hxxps://", text)
    text = re.sub(r"http://", "hxxp://", text)
    # Defang dots in domain-like strings but avoid file extensions and version numbers where possible.
    text = re.sub(r"\b([a-zA-Z0-9-]+)\.([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b", lambda m: m.group(0).replace(".", "[.]"), text)
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    args = parser.parse_args()
    print(defang(Path(args.input).read_text(encoding="utf-8")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
