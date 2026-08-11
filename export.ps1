<#
.SYNOPSIS
  Devin bundle exporter (Windows / PowerShell).
  Regenerates skills/ and AGENTS.md in the bundle from the live Devin config on this machine.

.DESCRIPTION
  Reads manifest.json to know which skills to export and where to find them.
  Resolves %APPDATA%, %USERPROFILE%, ~ in original_path.
  Copies each skill folder into bundle/skills/, overwriting.
  Copies the live AGENTS.md (or ~/.config/devin/rules.md fallback) into bundle/AGENTS.md.
  Updates manifest.json with fresh SHA-256 hashes and export timestamps.
  Optionally stages + commits if -Commit is passed.

.PARAMETER Commit
  After export, run `git add -A && git commit` with a generated message.

.PARAMETER Push
  After commit, run `git push`. Implies -Commit.

.PARAMETER DryRun
  Show what would be copied without writing.

.EXAMPLE
  .\export.ps1
  .\export.ps1 -DryRun
  .\export.ps1 -Commit -Push
#>
[CmdletBinding()]
param(
  [switch]$DryRun,
  [switch]$Commit,
  [switch]$Push
)

$ErrorActionPreference = "Stop"
$bundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $bundleRoot "manifest.json"
$skillsDst   = Join-Path $bundleRoot "skills"
$rulesDst    = Join-Path $bundleRoot "AGENTS.md"

if (-not (Test-Path $manifestPath)) { throw "manifest.json not found at $manifestPath" }
$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json

function Write-Step($msg) { Write-Host "`n[*] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    [+] $msg" -ForegroundColor Green }
function Write-Skip($msg) { Write-Host "    [~] $msg (dry-run)" -ForegroundColor Yellow }
function Write-Warn($msg) { Write-Host "    [!] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "    [x] $msg" -ForegroundColor Red }

function Resolve-DevinPath($raw) {
  # Expand env vars and ~
  $expanded = $raw -replace '%APPDATA%',$env:APPDATA
  $expanded = $expanded -replace '%USERPROFILE%',$env:USERPROFILE
  $expanded = $expanded -replace '~',$env:USERPROFILE
  return $expanded
}

function Get-FolderHash($path) {
  if (-not (Test-Path $path)) { return $null }
  $files = Get-ChildItem $path -Recurse -File | Sort-Object FullName
  $hashes = $files | ForEach-Object { (Get-FileHash $_.FullName -Algorithm SHA256).Hash }
  return ($hashes -join "`n")
}

Write-Host "================================================" -ForegroundColor DarkGray
Write-Host "  Devin Bundle Exporter" -ForegroundColor White
Write-Host "  Source : $env:APPDATA\devin" -ForegroundColor DarkGray
Write-Host "  Bundle : $bundleRoot" -ForegroundColor DarkGray
if ($DryRun) { Write-Host "  Mode   : DRY-RUN" -ForegroundColor Yellow }
Write-Host "================================================" -ForegroundColor DarkGray

# --- 1. Ensure skills/ dir ---
if (-not (Test-Path $skillsDst)) {
  if ($DryRun) { Write-Skip "would create $skillsDst" }
  else { New-Item -ItemType Directory -Force -Path $skillsDst | Out-Null; Write-Ok "created $skillsDst" }
}

# --- 2. Export rules (AGENTS.md) ---
Write-Step "Export consolidated rules"
$rulesSources = @(
  "$env:APPDATA\devin\AGENTS.md",
  "$env:USERPROFILE\.config\devin\rules.md"
)
$rulesFound = $null
foreach ($r in $rulesSources) {
  if (Test-Path $r) { $rulesFound = $r; break }
}
if ($rulesFound) {
  if ($DryRun) { Write-Skip "would copy $rulesFound -> $rulesDst" }
  else {
    Copy-Item $rulesFound $rulesDst -Force
    Write-Ok "rules exported from $rulesFound"
  }
} else {
  Write-Warn "no AGENTS.md or rules.md found in standard locations; keeping existing bundle/AGENTS.md"
}

# --- 3. Export skills ---
Write-Step "Export skills"
$exported = 0; $unchanged = 0; $failed = 0
$updatedManifest = $manifest

foreach ($skill in $manifest.skills) {
  $name = $skill.name
  $srcRaw = $skill.original_path
  $src = Resolve-DevinPath $srcRaw
  $dst = Join-Path $skillsDst $name

  if (-not (Test-Path $src)) {
    Write-Err "$name : source not found at $src"
    $failed++
    continue
  }

  $srcHash = Get-FolderHash $src
  $dstHash = if (Test-Path $dst) { Get-FolderHash $dst } else { $null }

  if ($srcHash -eq $dstHash) {
    Write-Ok "$name (unchanged)"
    $unchanged++
  } else {
    if ($DryRun) {
      Write-Skip "would export $name from $src"
    } else {
      if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
      Copy-Item $src $dst -Recurse -Force
      Write-Ok "exported $name"
    }
    $exported++
  }

  # Update manifest with hash + timestamp
  $skill | Add-Member -NotePropertyName "export_hash" -NotePropertyValue $srcHash -Force
  $skill | Add-Member -NotePropertyName "exported_at" -NotePropertyValue (Get-Date -Format "o") -Force
}

# --- 4. Update manifest.json ---
if (-not $DryRun) {
  Write-Step "Update manifest.json"
  $manifest | ConvertTo-Json -Depth 10 | Set-Content $manifestPath -Encoding UTF8
  Write-Ok "manifest.json updated with hashes + timestamps"
}

# --- 5. Summary ---
Write-Step "Summary"
Write-Host "    Skills exported  : $exported"
Write-Host "    Skills unchanged : $unchanged"
Write-Host "    Skills failed    : $failed"

# --- 6. Optional git commit + push ---
if ($Commit -and -not $DryRun -and $failed -eq 0) {
  Write-Step "Git commit"
  Push-Location $bundleRoot
  try {
    git add -A 2>&1 | Out-Null
    $status = git status --porcelain
    if ($status) {
      $date = Get-Date -Format "yyyy-MM-dd"
      git commit -m "export: refresh skills + rules ($date)" 2>&1 | Out-Null
      Write-Ok "committed"
      if ($Push) {
        git push 2>&1 | ForEach-Object { Write-Host "    $_" }
        Write-Ok "pushed"
      }
    } else {
      Write-Ok "nothing to commit (bundle already up to date)"
    }
  } finally {
    Pop-Location
  }
}

if ($DryRun) { Write-Host "`nDry-run complete. Re-run without -DryRun to apply." -ForegroundColor Yellow }
else { Write-Host "`nExport complete." -ForegroundColor Green }
