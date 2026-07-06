#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   MODULE=github.com/org/pkg ./go_module_artifact_check.sh
: "${MODULE:?Set MODULE}"

OUT="${OUT:-out/go-module-artifact-check}"
mkdir -p "$OUT"

go env GOMODCACHE > "$OUT/gomodcache.txt"
GOMODCACHE="$(cat "$OUT/gomodcache.txt")"

echo "[+] Listing module info"
go list -m -json "$MODULE" > "$OUT/module.json" || true

echo "[+] Searching local repo lock data"
rg -n "$MODULE" go.mod go.sum . 2>/dev/null | tee "$OUT/local-references.txt" || true

echo "[+] Searching module cache for high-risk Go behavior"
SAFE_MODULE_PATH="$(echo "$MODULE" | sed 's/[A-Z]/!&/g' | tr '[:upper:]' '[:lower:]')"
rg -n 'func init\(|net\.LookupTXT|os/exec|exec\.Command|syscall|plugin\.Open|http\.Get|http\.Post|base64|crypto' "$GOMODCACHE" 2>/dev/null | tee "$OUT/cache-suspicious-patterns.txt" || true

echo "[+] Review module cache under: $GOMODCACHE"
