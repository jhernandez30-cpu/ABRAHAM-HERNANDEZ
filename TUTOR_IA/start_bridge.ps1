param(
  [string]$Python = "python",
  [string]$Port = "8787",
  [string]$BrainDb = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($BrainDb) {
  $env:TUTOR_IA_PERSIST_DIR = $BrainDb
}

$env:TUTOR_IA_WEB_PORT = $Port
& $Python (Join-Path $scriptDir "web_bridge.py")
