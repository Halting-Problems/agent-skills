#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   IOC_REGEX='domain|filename|package' ./linux_dev_triage.sh

: "${IOC_REGEX:?Set IOC_REGEX}"
OUT="${OUT:-out/linux-dev-triage}"
mkdir -p "$OUT"

echo "[+] Basic host context"
{
  date -u
  uname -a
  id
  whoami
} > "$OUT/host-context.txt"

echo "[+] Process snapshot"
ps auxww > "$OUT/ps-auxww.txt"

echo "[+] Network snapshot"
(ss -plant || netstat -plant || true) > "$OUT/network-sockets.txt" 2>&1

echo "[+] Shell and profile IOC search"
rg -n "$IOC_REGEX" "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile" "$HOME/.config" 2>/dev/null | tee "$OUT/profile-ioc-hits.txt" || true

echo "[+] Package manager cache IOC search"
for d in "$HOME/.npm" "$HOME/.cache/pip" "$HOME/.cache/pypoetry" "$HOME/go/pkg/mod" "$HOME/.cargo/registry" "$HOME/.vscode/extensions"; do
  [ -d "$d" ] && rg -n "$IOC_REGEX" "$d" 2>/dev/null | tee -a "$OUT/cache-ioc-hits.txt" || true
done

echo "[+] Credential file inventory. Do not upload blindly."
for f in \
  "$HOME/.git-credentials" \
  "$HOME/.config/gh/hosts.yml" \
  "$HOME/.npmrc" \
  "$HOME/.pypirc" \
  "$HOME/.aws/credentials" \
  "$HOME/.azure/accessTokens.json" \
  "$HOME/.config/gcloud/application_default_credentials.json" \
  "$HOME/.kube/config" \
  "$HOME/.docker/config.json" \
  "$HOME/.ssh/config"; do
  [ -e "$f" ] && ls -l "$f"
done > "$OUT/credential-file-inventory.txt"

echo "[+] Done. Preserve $OUT and rotate credentials from a clean system if execution is confirmed."
