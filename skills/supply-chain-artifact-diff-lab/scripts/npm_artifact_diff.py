#!/usr/bin/env python3
"""Download and diff npm package tarballs.

Requires:
  npm, tar, diff, jq optional

Usage:
  python npm_artifact_diff.py @scope/pkg 1.0.0 1.0.1 --out out/npm-diff
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True, stderr=subprocess.STDOUT)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def npm_pack(pkg: str, version: str, out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    before = set(out.iterdir())
    run(["npm", "pack", f"{pkg}@{version}", "--pack-destination", str(out)])
    after = set(out.iterdir())
    created = sorted(after - before)
    if not created:
        raise RuntimeError(f"npm pack did not create tarball for {pkg}@{version}")
    return created[-1]


def extract(tarball: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    run(["tar", "-xzf", str(tarball), "-C", str(target)])


def list_files(base: Path) -> dict[str, str]:
    result = {}
    for path in sorted(base.rglob("*")):
        if path.is_file():
            rel = str(path.relative_to(base))
            result[rel] = sha256(path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package")
    parser.add_argument("known_good")
    parser.add_argument("suspicious")
    parser.add_argument("--out", default="out/npm-artifact-diff")
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    kg_tar = npm_pack(args.package, args.known_good, out / "tarballs")
    sus_tar = npm_pack(args.package, args.suspicious, out / "tarballs")

    kg_dir = out / "known-good"
    sus_dir = out / "suspicious"
    extract(kg_tar, kg_dir)
    extract(sus_tar, sus_dir)

    kg_files = list_files(kg_dir)
    sus_files = list_files(sus_dir)

    added = sorted(set(sus_files) - set(kg_files))
    removed = sorted(set(kg_files) - set(sus_files))
    modified = sorted(k for k in set(kg_files) & set(sus_files) if kg_files[k] != sus_files[k])

    report = {
        "package": args.package,
        "known_good": args.known_good,
        "suspicious": args.suspicious,
        "known_good_tarball": str(kg_tar),
        "suspicious_tarball": str(sus_tar),
        "known_good_sha256": sha256(kg_tar),
        "suspicious_sha256": sha256(sus_tar),
        "known_good_size": kg_tar.stat().st_size,
        "suspicious_size": sus_tar.stat().st_size,
        "added_files": added,
        "removed_files": removed,
        "modified_files": modified,
        "manifest_files_to_review": [p for p in added + modified if p.endswith("package/package.json")],
        "suspicious_execution_triggers_to_review": [
            "package.json scripts: preinstall, install, postinstall, prepare, prepublishOnly",
            "new native binaries",
            "new obfuscated JavaScript",
            "new curl, wget, node, bun, python, sh execution"
        ],
    }

    (out / "artifact-diff.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
