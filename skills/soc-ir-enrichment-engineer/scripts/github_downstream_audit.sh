#!/usr/bin/env bash
set -euo pipefail

# Audit GitHub downstream activity after a suspected token exposure.
#
# Usage:
#   ORG=my-org SINCE=2026-05-18T19:10:24Z UNTIL=2026-05-21T00:00:00Z ./github_downstream_audit.sh

: "${ORG:?Set ORG}"
: "${SINCE:?Set SINCE}"
: "${UNTIL:?Set UNTIL}"

OUT="${OUT:-out/github-downstream-audit}"
mkdir -p "$OUT"

SINCE_DATE="${SINCE%%T*}"
UNTIL_DATE="${UNTIL%%T*}"

echo "[+] Pulling audit log if accessible"
gh api "/orgs/${ORG}/audit-log" \
  --method GET \
  -f "phrase=created:${SINCE_DATE}..${UNTIL_DATE}" \
  --paginate \
  --jq '.[] | {
    ts: .created_at,
    action: .action,
    actor: .actor,
    actor_ip: .actor_ip,
    repo: .repo,
    user: .user,
    oauth_application_name: .oauth_application_name,
    token_id: .token_id,
    raw: .
  }' > "$OUT/audit-events.jsonl" || true

echo "[+] Listing repositories"
gh repo list "$ORG" --limit 1000 --json nameWithOwner --jq '.[].nameWithOwner' > "$OUT/repos.txt"

while read -r FULL_REPO; do
  OWNER="${FULL_REPO%/*}"
  REPO="${FULL_REPO#*/}"
  echo "[+] Repo $FULL_REPO"

  gh api "/repos/${OWNER}/${REPO}/commits" \
    -f "since=${SINCE}" -f "until=${UNTIL}" -f per_page=100 --paginate \
    --jq '.[] | {repo:"'"$FULL_REPO"'", sha, ts:.commit.committer.date, author:.author.login, committer:.committer.login, message:.commit.message, html_url}' \
    >> "$OUT/commits-after-exposure.jsonl" || true

  gh api "/repos/${OWNER}/${REPO}/releases" -f per_page=100 --paginate \
    --jq '.[] | select(.created_at >= "'"$SINCE"'" and .created_at <= "'"$UNTIL"'") |
      {repo:"'"$FULL_REPO"'", tag_name, name, created_at, published_at, author:.author.login, target_commitish, html_url}' \
    >> "$OUT/releases-after-exposure.jsonl" || true

  gh api "/repos/${OWNER}/${REPO}/actions/secrets" -f per_page=100 --paginate \
    --jq '.secrets[]? | select(.updated_at >= "'"$SINCE"'") |
      {repo:"'"$FULL_REPO"'", scope:"repo", name, created_at, updated_at}' \
    >> "$OUT/repo-secrets-updated.jsonl" || true

  gh api "/repos/${OWNER}/${REPO}/actions/workflows" -f per_page=100 --paginate \
    --jq '.workflows[]? | {repo:"'"$FULL_REPO"'", id, name, path, state, created_at, updated_at, html_url}' \
    >> "$OUT/workflows-current.jsonl" || true

done < "$OUT/repos.txt"

echo "[+] Packages after exposure"
for TYPE in container npm maven rubygems nuget; do
  gh api "/orgs/${ORG}/packages" -f "package_type=${TYPE}" -f per_page=100 --paginate \
    --jq '.[] | {name, package_type}' | while read -r PACKAGE_JSON; do
      NAME="$(jq -r '.name' <<< "$PACKAGE_JSON")"
      PACKAGE_TYPE="$(jq -r '.package_type' <<< "$PACKAGE_JSON")"
      ENCODED_NAME="$(jq -rn --arg v "$NAME" '$v|@uri')"
      gh api "/orgs/${ORG}/packages/${PACKAGE_TYPE}/${ENCODED_NAME}/versions" -f per_page=100 --paginate \
        --jq '.[] | select(.created_at >= "'"$SINCE"'" or .updated_at >= "'"$SINCE"'") |
          {package_name:"'"$NAME"'", package_type:"'"$PACKAGE_TYPE"'", version_id:.id, name, created_at, updated_at, metadata}' \
        >> "$OUT/packages-after-exposure.jsonl" || true
    done
done

echo "[+] Done. Review $OUT"
