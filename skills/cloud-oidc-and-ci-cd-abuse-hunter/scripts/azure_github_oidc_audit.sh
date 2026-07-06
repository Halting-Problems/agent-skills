#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   WORKSPACE_ID=<log-analytics-workspace-id> SINCE=2026-05-18T19:10:24Z UNTIL=2026-05-21T00:00:00Z ./azure_github_oidc_audit.sh

: "${WORKSPACE_ID:?Set WORKSPACE_ID}"
: "${SINCE:?Set SINCE}"
: "${UNTIL:?Set UNTIL}"

OUT="${OUT:-out/azure-github-oidc-audit}"
mkdir -p "$OUT"

az ad app list --all --query '[].{appId:appId, displayName:displayName, id:id}' -o json |
jq -c '.[]' |
while read -r APP; do
  APP_ID="$(jq -r '.appId' <<< "$APP")"
  DISPLAY_NAME="$(jq -r '.displayName' <<< "$APP")"
  az ad app federated-credential list --id "$APP_ID" -o json 2>/dev/null |
  jq -c --arg appId "$APP_ID" --arg displayName "$DISPLAY_NAME" '
    .[] | select(.issuer == "https://token.actions.githubusercontent.com") |
    {appId:$appId, appDisplayName:$displayName, federatedCredentialName:.name, issuer:.issuer, subject:.subject, audiences:.audiences}
  ' >> "$OUT/github-federated-apps.jsonl" || true
done

APP_ID_LIST="$(jq -r '.appId' "$OUT/github-federated-apps.jsonl" | sort -u | jq -R . | jq -s 'join(",")')"

cat > "$OUT/service-principal-signins.kql" <<EOF
let start = datetime(${SINCE});
let end = datetime(${UNTIL});
let appIds = dynamic([${APP_ID_LIST}]);
AADServicePrincipalSignInLogs
| where TimeGenerated between (start .. end)
| where AppId in (appIds)
| project TimeGenerated, AppDisplayName, AppId, ServicePrincipalId, ServicePrincipalName, ResourceDisplayName, IPAddress, Location, ResultType, ResultDescription, CorrelationId
| order by TimeGenerated asc
EOF

az monitor log-analytics query --workspace "$WORKSPACE_ID" --analytics-query "$(cat "$OUT/service-principal-signins.kql")" -o json > "$OUT/service-principal-signins.json"

SP_ID_LIST="$(jq -r '.tables[0].rows[]?[3]' "$OUT/service-principal-signins.json" | sort -u | jq -R . | jq -s 'join(",")')"

cat > "$OUT/azure-activity-writes.kql" <<EOF
let start = datetime(${SINCE});
let end = datetime(${UNTIL});
let spIds = dynamic([${SP_ID_LIST}]);
let appIds = dynamic([${APP_ID_LIST}]);
AzureActivity
| where TimeGenerated between (start .. end)
| where CategoryValue =~ "Administrative"
| where OperationNameValue has_any ("write", "delete", "action", "deployments")
| where Caller in (spIds) or Claims has_any (appIds)
| project TimeGenerated, Caller, CallerIpAddress, OperationNameValue, ActivityStatusValue, ResourceGroup, ResourceProviderValue, ResourceId, CorrelationId, Claims, Properties
| order by TimeGenerated asc
EOF

az monitor log-analytics query --workspace "$WORKSPACE_ID" --analytics-query "$(cat "$OUT/azure-activity-writes.kql")" -o json > "$OUT/azure-activity-writes.json"

echo "[+] Done. Review $OUT"
