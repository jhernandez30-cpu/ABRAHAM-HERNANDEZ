param(
  [string]$Python = "python",
  [string]$Port = "8787",
  [string]$BrainDb = "",
  [string]$TutorRoot = "C:\Users\herna\Documents\tutor_ia",
  [string]$ObsidianVault = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($TutorRoot -and (Test-Path -LiteralPath $TutorRoot)) {
  $env:TUTOR_IA_ROOT = $TutorRoot
  $TutorBackend = Join-Path $TutorRoot "backend"
  $pythonPaths = @($TutorRoot)
  if (Test-Path -LiteralPath $TutorBackend) {
    $pythonPaths += $TutorBackend
  }
  $pythonPathText = $pythonPaths -join ";"
  $env:PYTHONPATH = if ($env:PYTHONPATH) { "$pythonPathText;$env:PYTHONPATH" } else { $pythonPathText }
}

if (-not $BrainDb -and $TutorRoot) {
  $candidateBrainDb = Join-Path $TutorRoot "vectores\brain_db"
  if (-not (Test-Path -LiteralPath $candidateBrainDb)) {
    $candidateBrainDb = Join-Path $TutorRoot "brain_db"
  }
  if (Test-Path -LiteralPath $candidateBrainDb) {
    $BrainDb = $candidateBrainDb
  }
}

if ($BrainDb) {
  $env:TUTOR_IA_PERSIST_DIR = $BrainDb
}

if (-not $ObsidianVault -and $TutorRoot) {
  $candidateVault = Join-Path $TutorRoot "conocimiento"
  if (-not (Test-Path -LiteralPath $candidateVault)) {
    $candidateVault = Join-Path $TutorRoot "Tutor_IA"
  }
  if (Test-Path -LiteralPath $candidateVault) {
    $ObsidianVault = $candidateVault
  }
}

if ($ObsidianVault) {
  $env:TUTOR_IA_OBSIDIAN_DIR = $ObsidianVault
  $env:TUTOR_IA_OBSIDIAN_ENABLED = "1"
}

$env:TUTOR_IA_WEB_PORT = $Port
& $Python (Join-Path $scriptDir "web_bridge.py")
