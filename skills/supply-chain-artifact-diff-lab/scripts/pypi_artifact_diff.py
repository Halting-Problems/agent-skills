#!/usr/bin/env python3
"""Download and diff PyPI package files.

Usage:
  python pypi_artifact_diff.py PACKAGE KNOWN_GOOD_VERSION SUSPICIOUS_VERSION --out out/pypi-diff
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
import urllib.request
import zipfile
from pathlib import Path


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as resp:
        target.write_bytes(resp.read())
    return target


def choose_file(meta: dict, version: str) -> dict:
    files = meta["releases"].get(version, [])
    if not files:
        raise RuntimeError(f"No files found for version {version}")
    wheels = [f for f in files if f.get("packagetype") == "bdist_wheel"]
    return wheels[0] if wheels else files[0]


def extract(archive: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z:
            z.extractall(target)
    elif tarfile.is_tarfile(archive):
        with tarfile.open(archive) as t:
            t.extractall(target)
    else:
        raise RuntimeError(f"Unsupported archive type: {archive}")


def list_files(base: Path) -> dict[str, str]:
    result = {}
    for path in sorted(base.rglob("*")):
        if path.is_file():
            result[str(path.relative_to(base))] = sha256(path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package")
    parser.add_argument("known_good")
    parser.add_argument("suspicious")
    parser.add_argument("--out", default="out/pypi-artifact-diff")
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    meta = fetch_json(f"https://pypi.org/pypi/{args.package}/json")
    kg = choose_file(meta, args.known_good)
    sus = choose_file(meta, args.suspicious)

    kg_archive = download(kg["url"], out / "archives" / kg["filename"])
    sus_archive = download(sus["url"], out / "archives" / sus["filename"])

    kg_dir = out / "known-good"
    sus_dir = out / "suspicious"
    extract(kg_archive, kg_dir)
    extract(sus_archive, sus_dir)

    kg_files = list_files(kg_dir)
    sus_files = list_files(sus_dir)
    added = sorted(set(sus_files) - set(kg_files))
    removed = sorted(set(kg_files) - set(sus_files))
    modified = sorted(k for k in set(kg_files) & set(sus_files) if kg_files[k] != sus_files[k])

    suspicious_paths = [
        p for p in added + modified
        if p.endswith(".pth") or p.endswith("setup.py") or p.endswith("pyproject.toml")
        or "__init__.py" in p or "_runtime" in p or p.endswith(".pyz")
    ]

    report = {
        "package": args.package,
        "known_good": args.known_good,
        "suspicious": args.suspicious,
        "known_good_file": kg,
        "suspicious_file": sus,
        "known_good_sha256": sha256(kg_archive),
        "suspicious_sha256": sha256(sus_archive),
        "added_files": added,
        "removed_files": removed,
        "modified_files": modified,
        "suspicious_paths_to_review": suspicious_paths,
        "execution_triggers_to_review": [
            ".pth interpreter startup hooks",
            "setup.py or build backend execution",
            "import-time code in __init__.py",
            "entry_points scripts",
            "hidden runtime directories or zipapps"
        ],
    }
    (out / "artifact-diff.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
