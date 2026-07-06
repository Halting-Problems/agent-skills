#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   CF_API_TOKEN=<token> CF_ACCOUNT_ID=<account-id> SINCE=2026-05-18T19:10:24Z ./cloudflare_audit.sh

: "${CF_API_TOKEN:?Set CF_API_TOKEN}"
: "${CF_ACCOUNT_ID:?Set CF_ACCOUNT_ID}"
: "${SINCE:?Set SINCE}"

OUT="${OUT:-out/cloudflare-audit}"
mkdir -p "$OUT"

curl -fsSL \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: application/json" \
  "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/audit_logs?since=${SINCE}" |
jq -r '
  .result[] |
  select(
    (.action.type // "" | test("create|update|delete|edit|purge|deploy"; "i"))
    or
    (.resource.type // "" | test("zone|dns|worker|pages|ruleset|token|access|cache|firewall"; "i"))
  ) |
  {when, actor, action, resource, interface, metadata}
' > "$OUT/cloudflare-write-events-after-exposure.jsonl"

echo "[+] Done. Review $OUT"
