#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   GOOD_IMAGE=image@sha256:good BAD_IMAGE=image@sha256:bad ./container_image_diff.sh
: "${GOOD_IMAGE:?Set GOOD_IMAGE}"
: "${BAD_IMAGE:?Set BAD_IMAGE}"

OUT="${OUT:-out/container-image-diff}"
mkdir -p "$OUT"

docker pull "$GOOD_IMAGE"
docker pull "$BAD_IMAGE"

docker image inspect "$GOOD_IMAGE" > "$OUT/good-inspect.json"
docker image inspect "$BAD_IMAGE" > "$OUT/bad-inspect.json"

docker save "$GOOD_IMAGE" -o "$OUT/good.tar"
docker save "$BAD_IMAGE" -o "$OUT/bad.tar"

mkdir -p "$OUT/good" "$OUT/bad"
tar -xf "$OUT/good.tar" -C "$OUT/good"
tar -xf "$OUT/bad.tar" -C "$OUT/bad"

echo "[+] Image layer metadata diff"
diff -ru "$OUT/good" "$OUT/bad" > "$OUT/raw-diff.txt" || true

echo "[+] Generating SBOMs if syft is available"
if command -v syft >/dev/null 2>&1; then
  syft "$GOOD_IMAGE" -o cyclonedx-json > "$OUT/good-sbom.cdx.json" || true
  syft "$BAD_IMAGE" -o cyclonedx-json > "$OUT/bad-sbom.cdx.json" || true
fi

echo "[+] Done. Review $OUT"
