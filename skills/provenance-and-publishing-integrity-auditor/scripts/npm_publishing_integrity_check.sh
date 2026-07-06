#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   PACKAGE=@scope/pkg VERSION=1.2.3 ./npm_publishing_integrity_check.sh

: "${PACKAGE:?Set PACKAGE}"
: "${VERSION:?Set VERSION}"

OUT="${OUT:-out/npm-publishing-integrity}"
mkdir -p "$OUT"

npm view "${PACKAGE}@${VERSION}" --json > "$OUT/npm-view.json"

jq '{
  name,
  version,
  dist,
  maintainers,
  repository,
  scripts,
  time
}' "$OUT/npm-view.json" > "$OUT/npm-view-summary.json" || true

echo "[+] Downloading tarball for manifest review"
npm pack "${PACKAGE}@${VERSION}" --pack-destination "$OUT" >/dev/null
TARBALL="$(ls -1 "$OUT"/*.tgz | head -n 1)"
sha256sum "$TARBALL" > "$OUT/tarball.sha256"

tar -xzf "$TARBALL" -C "$OUT"
if [ -f "$OUT/package/package.json" ]; then
  jq '{name, version, scripts, repository, dist, dependencies, optionalDependencies, devDependencies}' "$OUT/package/package.json" > "$OUT/package-json-summary.json"
fi

echo "[+] Done. Review provenance, scripts, repository URL, and dist integrity under $OUT"
