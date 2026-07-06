#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   PACKAGE=vendor/package VERSION=1.2.3 ./composer_artifact_check.sh
: "${PACKAGE:?Set PACKAGE}"
: "${VERSION:?Set VERSION}"

OUT="${OUT:-out/composer-artifact-check}"
mkdir -p "$OUT"

composer show "$PACKAGE" "$VERSION" --all --format=json > "$OUT/composer-show.json" || true

echo "[+] Searching composer.lock in current repo"
if [ -f composer.lock ]; then
  jq --arg pkg "$PACKAGE" '.packages[]? | select(.name == $pkg)' composer.lock > "$OUT/composer-lock-match.json" || true
fi

echo "[+] Files to inspect if installed:"
cat > "$OUT/review-checklist.txt" <<EOF
vendor/composer/autoload_files.php
vendor/composer/installed.json
vendor/${PACKAGE}/composer.json
vendor/${PACKAGE}/**/*.php
composer.json autoload.files
composer.json scripts
EOF

echo "[+] Local suspicious PHP patterns:"
if [ -d "vendor/${PACKAGE}" ]; then
  rg -n 'eval\(|base64_decode|shell_exec|proc_open|curl_exec|file_get_contents\("http|openssl_decrypt|autoload\.files' "vendor/${PACKAGE}" || true
fi
