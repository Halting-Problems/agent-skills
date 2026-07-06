#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   IMAGE=ghcr.io/org/image@sha256:... ./cosign_image_integrity_check.sh

: "${IMAGE:?Set IMAGE}"
OUT="${OUT:-out/cosign-image-integrity}"
mkdir -p "$OUT"

if command -v cosign >/dev/null 2>&1; then
  cosign triangulate "$IMAGE" > "$OUT/triangulate.txt" || true
  cosign verify "$IMAGE" --output json > "$OUT/cosign-verify.json" || true
  cosign verify-attestation "$IMAGE" --type slsaprovenance --output json > "$OUT/slsa-attestation.json" || true
else
  echo "cosign not found" > "$OUT/error.txt"
fi

docker image inspect "$IMAGE" > "$OUT/docker-inspect.json" || true
echo "[+] Done. Review $OUT"
