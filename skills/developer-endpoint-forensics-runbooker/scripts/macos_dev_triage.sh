#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   IOC_REGEX='domain|filename|package' ./macos_dev_triage.sh

: "${IOC_REGEX:?Set IOC_REGEX}"
OUT="${OUT:-out/macos-dev-triage}"
mkdir -p "$OUT"

sw_vers > "$OUT/sw_vers.txt"
uname -a > "$OUT/uname.txt"
ps auxww > "$OUT/ps-auxww.txt"
lsof -i -P -n > "$OUT/lsof-network.txt" 2>/dev/null || true

echo "[+] Launch agents and daemons"
ls -la "$HOME/Library/LaunchAgents" /Library/LaunchAgents /Library/LaunchDaemons 2>/dev/null > "$OUT/launch-items.txt" || true

echo "[+] IOC search in profiles, extensions, package caches"
for d in "$HOME/.npm" "$HOME/Library/Caches/pip" "$HOME/.vscode/extensions" "$HOME/.cargo/registry" "$HOME/go/pkg/mod" "$HOME/Library/Application Support/Code/User"; do
  [ -d "$d" ] && rg -n "$IOC_REGEX" "$d" 2>/dev/null | tee -a "$OUT/ioc-hits.txt" || true
done

echo "[+] Credential inventory. Do not upload blindly."
for f in \
  "$HOME/.git-credentials" "$HOME/.config/gh/hosts.yml" "$HOME/.npmrc" "$HOME/.pypirc" \
  "$HOME/.aws/credentials" "$HOME/.kube/config" "$HOME/.docker/config.json" "$HOME/.ssh/config"; do
  [ -e "$f" ] && ls -l "$f"
done > "$OUT/credential-file-inventory.txt"

echo "[+] Done. Review $OUT"
