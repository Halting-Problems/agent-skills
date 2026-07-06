#!/usr/bin/env bash
set -euo pipefail

# Audit npm, PyPI, and NuGet publishes after exposure.
#
# Usage:
#   SINCE=2026-05-18T19:10:24Z ./registry_publish_audit.sh
#
# Optional input files:
#   npm-packages.txt
#   pypi-packages.txt
#   nuget-packages.txt

: "${SINCE:?Set SINCE}"
OUT="${OUT:-out/registry-publish-audit}"
mkdir -p "$OUT"

if [ -f npm-packages.txt ]; then
  while read -r PKG; do
    [ -z "$PKG" ] && continue
    ENCODED="$(jq -rn --arg v "$PKG" '$v|@uri')"
    curl -fsSL "https://registry.npmjs.org/${ENCODED}" |
      jq -r --arg pkg "$PKG" --arg since "$SINCE" '
        .time | to_entries[] |
        select(.key != "created" and .key != "modified") |
        select(.value >= $since) |
        {registry:"npm", package:$pkg, version:.key, published_at:.value}
      ' >> "$OUT/npm-after-exposure.jsonl" || true
  done < npm-packages.txt
fi

if [ -f pypi-packages.txt ]; then
  while read -r PKG; do
    [ -z "$PKG" ] && continue
    curl -fsSL "https://pypi.org/pypi/${PKG}/json" |
      jq -r --arg pkg "$PKG" --arg since "$SINCE" '
        .releases | to_entries[] as $version |
        $version.value[] |
        select(.upload_time_iso_8601 >= $since) |
        {registry:"pypi", package:$pkg, version:$version.key, filename, packagetype, upload_time_iso_8601, digests, url}
      ' >> "$OUT/pypi-after-exposure.jsonl" || true
  done < pypi-packages.txt
fi

if [ -f nuget-packages.txt ]; then
  while read -r PKG; do
    [ -z "$PKG" ] && continue
    LOWER="$(tr '[:upper:]' '[:lower:]' <<< "$PKG")"
    curl -fsSL "https://api.nuget.org/v3/registration5-semver1/${LOWER}/index.json" |
      jq -r --arg pkg "$PKG" --arg since "$SINCE" '
        .items[] | .items[]? | .catalogEntry |
        select(.published >= $since) |
        {registry:"nuget", package:$pkg, version, published, authors, packageContent}
      ' >> "$OUT/nuget-after-exposure.jsonl" || true
  done < nuget-packages.txt
fi

echo "[+] Done. Review $OUT"
