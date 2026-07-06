#!/usr/bin/env bash
set -euo pipefail

# Query Kubernetes audit logs for CI/CD deployment activity after exposure.
#
# Usage:
#   SINCE=2026-05-18T19:10:24Z UNTIL=2026-05-21T00:00:00Z AUDIT_LOG=audit.jsonl ./k8s_deploy_audit.sh

: "${SINCE:?Set SINCE}"
: "${UNTIL:?Set UNTIL}"
: "${AUDIT_LOG:?Set AUDIT_LOG}"

OUT="${OUT:-out/k8s-deploy-audit}"
mkdir -p "$OUT"

jq -r --arg since "$SINCE" --arg until "$UNTIL" '
  select(.requestReceivedTimestamp >= $since and .requestReceivedTimestamp <= $until)
  | select(.verb | IN("create", "update", "patch", "delete", "deletecollection"))
  | {
      ts: .requestReceivedTimestamp,
      verb,
      user: .user.username,
      groups: .user.groups,
      sourceIPs,
      userAgent,
      namespace: .objectRef.namespace,
      resource: .objectRef.resource,
      subresource: .objectRef.subresource,
      name: .objectRef.name,
      responseCode: .responseStatus.code,
      requestURI
    }
' "$AUDIT_LOG" > "$OUT/write-events.jsonl"

jq -r '
  select(
    (.resource // "") |
    IN("deployments","daemonsets","statefulsets","cronjobs","jobs","pods","secrets","configmaps","roles","rolebindings","clusterroles","clusterrolebindings","validatingwebhookconfigurations","mutatingwebhookconfigurations","serviceaccounts")
  )
' "$OUT/write-events.jsonl" > "$OUT/high-risk-write-events.jsonl"

echo "[+] Done. Review $OUT"
