#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   SINCE=2026-05-18T19:10:24Z UNTIL=2026-05-21T00:00:00Z ./aws_github_oidc_audit.sh

: "${SINCE:?Set SINCE}"
: "${UNTIL:?Set UNTIL}"

OUT="${OUT:-out/aws-github-oidc-audit}"
mkdir -p "$OUT"

aws iam list-roles --output json |
jq -r '
  .Roles[]
  | select(
      .AssumeRolePolicyDocument.Statement[]?
      | (.Principal.Federated? // "" | tostring | contains("token.actions.githubusercontent.com"))
    )
  | {role_name:.RoleName, arn:.Arn, assume_role_policy:.AssumeRolePolicyDocument}
' > "$OUT/github-oidc-trusted-roles.json"

aws ec2 describe-regions --all-regions \
  --query 'Regions[?OptInStatus==`opt-in-not-required` || OptInStatus==`opted-in`].RegionName' \
  --output text | tr '\t' '\n' > "$OUT/regions.txt"

while read -r REGION; do
  aws cloudtrail lookup-events \
    --region "$REGION" \
    --start-time "$SINCE" \
    --end-time "$UNTIL" \
    --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRoleWithWebIdentity \
    --output json |
  jq -r --arg region "$REGION" '
    .Events[] | .CloudTrailEvent | fromjson |
    {
      region: $region,
      eventTime,
      sourceIPAddress,
      userAgent,
      roleArn: .requestParameters.roleArn,
      roleSessionName: .requestParameters.roleSessionName,
      subjectFromWebIdentityToken: .requestParameters.subjectFromWebIdentityToken,
      audience: .requestParameters.audience,
      assumedRoleArn: .responseElements.assumedRoleUser.arn,
      accessKeyId: .responseElements.credentials.accessKeyId,
      errorCode,
      errorMessage
    }
  ' >> "$OUT/assume-role-with-web-identity.jsonl" || true
done < "$OUT/regions.txt"

jq -r 'select(.accessKeyId != null) | [.region, .accessKeyId] | @tsv' "$OUT/assume-role-with-web-identity.jsonl" |
while IFS=$'\t' read -r REGION ACCESS_KEY_ID; do
  aws cloudtrail lookup-events \
    --region "$REGION" \
    --start-time "$SINCE" \
    --end-time "$UNTIL" \
    --lookup-attributes AttributeKey=AccessKeyId,AttributeValue="$ACCESS_KEY_ID" \
    --output json |
  jq -r --arg region "$REGION" --arg key "$ACCESS_KEY_ID" '
    .Events[] | .CloudTrailEvent | fromjson |
    {
      region: $region,
      accessKeyId: $key,
      eventTime,
      eventSource,
      eventName,
      sourceIPAddress,
      userAgent,
      requestParameters,
      responseElements,
      errorCode,
      errorMessage
    }
  ' >> "$OUT/follow-on-api-calls.jsonl" || true
done

jq -r '
  select(.eventName | test("Put|Update|Create|Delete|Attach|Detach|Assume|PassRole|RunInstances|CreateAccessKey|PutRolePolicy|AttachRolePolicy|UpdateAssumeRolePolicy|GetSecretValue|GetParameter|BatchGetImage|PutImage"))
' "$OUT/follow-on-api-calls.jsonl" > "$OUT/high-risk-api-calls.jsonl" || true

echo "[+] Done. Review $OUT"
