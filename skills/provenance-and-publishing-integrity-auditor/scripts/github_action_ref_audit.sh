#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   REPO=owner/repo REF=v1 DEFAULT_BRANCH=main ./github_action_ref_audit.sh

: "${REPO:?Set REPO owner/repo}"
: "${REF:?Set REF}"
: "${DEFAULT_BRANCH:=main}"

OUT="${OUT:-out/github-action-ref-audit}"
mkdir -p "$OUT"

git init "$OUT/repo" >/dev/null
git -C "$OUT/repo" remote add origin "https://github.com/${REPO}.git"
git -C "$OUT/repo" fetch --tags origin "$DEFAULT_BRANCH" --quiet

REF_SHA="$(git -C "$OUT/repo" rev-parse "refs/tags/${REF}" 2>/dev/null || git -C "$OUT/repo" rev-parse "origin/${REF}" 2>/dev/null || true)"
DEFAULT_SHA="$(git -C "$OUT/repo" rev-parse "origin/${DEFAULT_BRANCH}")"

REACHABLE=false
if [ -n "$REF_SHA" ] && git -C "$OUT/repo" merge-base --is-ancestor "$REF_SHA" "origin/${DEFAULT_BRANCH}" 2>/dev/null; then
  REACHABLE=true
fi

SIGNED="unknown"
if [ -n "$REF_SHA" ]; then
  if git -C "$OUT/repo" verify-commit "$REF_SHA" >/dev/null 2>&1; then
    SIGNED=true
  else
    SIGNED=false
  fi
fi

jq -n \
  --arg repo "$REPO" \
  --arg ref "$REF" \
  --arg default_branch "$DEFAULT_BRANCH" \
  --arg ref_sha "$REF_SHA" \
  --arg default_sha "$DEFAULT_SHA" \
  --argjson reachable "$REACHABLE" \
  --arg signed "$SIGNED" \
  '{
    repo:$repo,
    ref:$ref,
    default_branch:$default_branch,
    ref_sha:$ref_sha,
    default_sha:$default_sha,
    reachable_from_default_branch:$reachable,
    commit_signature_status:$signed,
    suspicious: (($reachable | not) or ($signed == "false"))
  }' | tee "$OUT/ref-audit.json"
