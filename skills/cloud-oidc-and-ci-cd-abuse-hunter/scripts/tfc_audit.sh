#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   TFC_TOKEN=<token> SINCE=2026-05-18T19:10:24.000Z ./tfc_audit.sh

: "${TFC_TOKEN:?Set TFC_TOKEN}"
: "${SINCE:?Set SINCE}"

OUT="${OUT:-out/tfc-audit}"
mkdir -p "$OUT"

PAGE=1
while true; do
  RESP="$(curl -fsSL \
    --header "Authorization: Bearer ${TFC_TOKEN}" \
    "https://app.terraform.io/api/v2/organization/audit-trail?page%5Bnumber%5D=${PAGE}&page%5Bsize%5D=1000&since=${SINCE}")"
  jq -c '.data[]' <<< "$RESP" >> "$OUT/tfc-audit-events.jsonl"
  NEXT_PAGE="$(jq -r '.pagination.next_page // empty' <<< "$RESP")"
  [ -z "$NEXT_PAGE" ] && break
  PAGE="$NEXT_PAGE"
done

jq -r '
  select(
    (.resource.type | test("run|workspace|var|state_version|authentication_token|team|oauth_token|vcs_repo|policy|policy_check"; "i"))
    and
    (.resource.action | test("create|apply|force_execute|update|destroy|delete|override|download|show"; "i"))
  )
' "$OUT/tfc-audit-events.jsonl" > "$OUT/high-risk-tfc-events.jsonl"

echo "[+] Done. Review $OUT"
