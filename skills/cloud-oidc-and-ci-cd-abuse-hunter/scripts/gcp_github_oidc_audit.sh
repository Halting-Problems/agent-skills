#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   PROJECT=my-project SINCE=2026-05-18T19:10:24Z UNTIL=2026-05-21T00:00:00Z ./gcp_github_oidc_audit.sh

: "${PROJECT:?Set PROJECT}"
: "${SINCE:?Set SINCE}"
: "${UNTIL:?Set UNTIL}"

OUT="${OUT:-out/gcp-github-oidc-audit}"
mkdir -p "$OUT"

FILTER=$(cat <<EOF
timestamp >= "${SINCE}"
timestamp <= "${UNTIL}"
(
  protoPayload.serviceName="sts.googleapis.com"
  OR protoPayload.serviceName="iamcredentials.googleapis.com"
  OR protoPayload.serviceName="iam.googleapis.com"
)
(
  protoPayload.authenticationInfo.principalSubject:"repo:"
  OR protoPayload.metadata.mapped_principal:"workloadIdentityPools"
  OR protoPayload.methodName:"GenerateAccessToken"
)
EOF
)

gcloud logging read "$FILTER" --project "$PROJECT" --format=json > "$OUT/wif-and-impersonation-events.json"

jq -r '
  .[] |
  {
    timestamp,
    serviceName: .protoPayload.serviceName,
    methodName: .protoPayload.methodName,
    principalEmail: .protoPayload.authenticationInfo.principalEmail,
    principalSubject: .protoPayload.authenticationInfo.principalSubject,
    mappedPrincipal: .protoPayload.metadata.mapped_principal,
    resourceName: .protoPayload.resourceName,
    serviceAccount: .resource.labels.email_id,
    request: .protoPayload.request,
    authorizationInfo: .protoPayload.authorizationInfo
  }
' "$OUT/wif-and-impersonation-events.json" > "$OUT/wif-and-impersonation-events.jsonl"

jq -r '.[] | select(.protoPayload.serviceName == "iamcredentials.googleapis.com") | .resource.labels.email_id // empty' "$OUT/wif-and-impersonation-events.json" | sort -u > "$OUT/impersonated-service-accounts.txt"

while read -r SA; do
  [ -z "$SA" ] && continue
  FOLLOW_FILTER=$(cat <<EOF
timestamp >= "${SINCE}"
timestamp <= "${UNTIL}"
protoPayload.authenticationInfo.principalEmail="${SA}"
(
  protoPayload.methodName:"create"
  OR protoPayload.methodName:"update"
  OR protoPayload.methodName:"delete"
  OR protoPayload.methodName:"setIamPolicy"
  OR protoPayload.methodName:"Deploy"
  OR protoPayload.methodName:"Run"
  OR protoPayload.methodName:"Upload"
)
EOF
)
  gcloud logging read "$FOLLOW_FILTER" --project "$PROJECT" --format=json |
  jq -r --arg sa "$SA" '.[] | {serviceAccount:$sa, timestamp, serviceName:.protoPayload.serviceName, methodName:.protoPayload.methodName, resourceName:.protoPayload.resourceName, request:.protoPayload.request, authorizationInfo:.protoPayload.authorizationInfo}' \
  >> "$OUT/follow-on-service-account-activity.jsonl" || true
done < "$OUT/impersonated-service-accounts.txt"

echo "[+] Done. Review $OUT"
