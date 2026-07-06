#!/usr/bin/env bash
set -euo pipefail

OUT="${OUT:-out/vscode-extension-inventory}"
mkdir -p "$OUT"

for base in "$HOME/.vscode/extensions" "$HOME/.vscode-insiders/extensions" "$HOME/.cursor/extensions"; do
  [ -d "$base" ] || continue
  find "$base" -maxdepth 2 -name package.json -print | while read -r manifest; do
    jq -r --arg manifest "$manifest" '{
      manifest:$manifest,
      name,
      publisher,
      version,
      activationEvents,
      main,
      browser,
      contributes
    }' "$manifest" >> "$OUT/extensions.jsonl" || true
  done
done

echo "[+] Suspicious activation and process helpers"
rg -n 'activationEvents|workspaceContains|onStartupFinished|child_process|exec\(|spawn\(|curl|wget|token|credential|ssh|aws|gcloud|azure' \
  "$HOME/.vscode/extensions" "$HOME/.vscode-insiders/extensions" "$HOME/.cursor/extensions" 2>/dev/null |
  tee "$OUT/suspicious-extension-patterns.txt" || true

echo "[+] Done. Review $OUT"
