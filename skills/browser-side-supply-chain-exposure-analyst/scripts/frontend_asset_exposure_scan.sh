#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   IOC_REGEX='art-template|malicious-domain|payloadString' ASSET_DIR=dist ./frontend_asset_exposure_scan.sh

: "${IOC_REGEX:?Set IOC_REGEX}"
: "${ASSET_DIR:=dist}"

OUT="${OUT:-out/browser-exposure-scan}"
mkdir -p "$OUT"

echo "[+] Searching source and lockfiles"
rg -n "$IOC_REGEX" package.json package-lock.json pnpm-lock.yaml yarn.lock src . 2>/dev/null | tee "$OUT/source-lockfile-hits.txt" || true

echo "[+] Searching built assets"
if [ -d "$ASSET_DIR" ]; then
  rg -n "$IOC_REGEX" "$ASSET_DIR" | tee "$OUT/built-asset-hits.txt" || true
  find "$ASSET_DIR" -type f \( -name '*.js' -o -name '*.map' -o -name '*.html' \) -print > "$OUT/asset-files.txt"
  while read -r f; do
    sha256sum "$f"
  done < "$OUT/asset-files.txt" > "$OUT/asset-sha256.txt"
else
  echo "Asset directory not found: $ASSET_DIR" | tee "$OUT/error.txt"
fi

cat > "$OUT/exposure-decision-template.yaml" <<EOF
browser_exposure:
  classification: unknown
  evidence:
    source_hits: $OUT/source-lockfile-hits.txt
    built_asset_hits: $OUT/built-asset-hits.txt
    asset_hashes: $OUT/asset-sha256.txt
  closure_required:
    - clean rebuild from safe dependency graph
    - CDN/cache invalidation evidence
    - proof poisoned assets are no longer served
    - WAF/proxy/browser telemetry reviewed
EOF

echo "[+] Done. Review $OUT"
