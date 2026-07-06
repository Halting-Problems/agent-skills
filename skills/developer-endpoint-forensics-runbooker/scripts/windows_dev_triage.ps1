param(
  [Parameter(Mandatory=$true)]
  [string]$IocRegex,
  [string]$Out = "out\windows-dev-triage"
)

New-Item -ItemType Directory -Force -Path $Out | Out-Null

Get-Date -Format o | Out-File "$Out\collection-time.txt"
Get-ComputerInfo | Out-File "$Out\computer-info.txt"
Get-Process | Select-Object Id,ProcessName,Path,StartTime -ErrorAction SilentlyContinue | ConvertTo-Json -Depth 3 | Out-File "$Out\processes.json"
Get-NetTCPConnection | ConvertTo-Json -Depth 3 | Out-File "$Out\tcp-connections.json"

$paths = @(
  "$env:USERPROFILE\.vscode\extensions",
  "$env:APPDATA\Code\User",
  "$env:USERPROFILE\AppData\Roaming\npm",
  "$env:LOCALAPPDATA\pip",
  "$env:USERPROFILE\.nuget\packages",
  "$env:USERPROFILE\.cargo\registry",
  "$env:USERPROFILE\go\pkg\mod"
)

foreach ($p in $paths) {
  if (Test-Path $p) {
    Select-String -Path "$p\*" -Pattern $IocRegex -Recurse -ErrorAction SilentlyContinue |
      Select-Object Path,LineNumber,Line |
      Export-Csv -Append -NoTypeInformation "$Out\ioc-hits.csv"
  }
}

$credPaths = @(
  "$env:USERPROFILE\.git-credentials",
  "$env:APPDATA\GitHub CLI\hosts.yml",
  "$env:USERPROFILE\.npmrc",
  "$env:USERPROFILE\.pypirc",
  "$env:USERPROFILE\.aws\credentials",
  "$env:USERPROFILE\.kube\config",
  "$env:USERPROFILE\.docker\config.json",
  "$env:USERPROFILE\.ssh\config"
)

$credPaths | Where-Object { Test-Path $_ } | ForEach-Object {
  Get-Item $_ | Select-Object FullName,Length,LastWriteTime
} | ConvertTo-Json -Depth 3 | Out-File "$Out\credential-file-inventory.json"

Write-Host "Done. Review $Out. Rotate credentials from a clean environment if execution is confirmed."
