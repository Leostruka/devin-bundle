<#
.SYNOPSIS
  Devin bundle installer (Windows / PowerShell).
  Restores skills + consolidated AGENTS.md to the correct Devin config locations.

.PARAMETER DryRun
  Show what would happen without writing anything.

.PARAMETER Force
  Overwrite existing skills/rules without prompting.

.EXAMPLE
  .\install.ps1
  .\install.ps1 -DryRun
  .\install.ps1 -Force
#>
[CmdletBinding()]
param(
  [switch]$DryRun,
  [switch]$Force
)

$ErrorActionPreference = "Stop"
$bundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillsSrc  = Join-Path $bundleRoot "skills"
$agentsSrc  = Join-Path $bundleRoot "agents"
$rulesSrc   = Join-Path $bundleRoot "AGENTS.md"

if (-not (Test-Path $skillsSrc)) { throw "skills/ folder not found next to install.ps1 ($bundleRoot)" }
if (-not (Test-Path $rulesSrc))  { throw "AGENTS.md not found next to install.ps1 ($bundleRoot)" }

# --- Resolve target dirs (Windows: %APPDATA%/devin) ---
$devinHome = Join-Path $env:APPDATA "devin"
$skillsDst = Join-Path $devinHome "skills"
$agentsDst = Join-Path $devinHome "agents"
$rulesDst  = Join-Path $devinHome "AGENTS.md"

function Write-Step($msg) { Write-Host "`n[*] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    [+] $msg" -ForegroundColor Green }
function Write-Skip($msg) { Write-Host "    [~] $msg (dry-run)" -ForegroundColor Yellow }
function Write-Warn($msg) { Write-Host "    [!] $msg" -ForegroundColor Yellow }

Write-Host "================================================" -ForegroundColor DarkGray
Write-Host "  Devin Bundle Installer" -ForegroundColor White
Write-Host "  Target : $devinHome" -ForegroundColor DarkGray
if ($DryRun) { Write-Host "  Mode   : DRY-RUN" -ForegroundColor Yellow }
Write-Host "================================================" -ForegroundColor DarkGray

# --- 1. Ensure dirs ---
Write-Step "Ensure target directories"
if ($DryRun) {
  Write-Skip "would create $devinHome (if missing)"
  Write-Skip "would create $skillsDst (if missing)"
} else {
  New-Item -ItemType Directory -Force -Path $devinHome | Out-Null
  New-Item -ItemType Directory -Force -Path $skillsDst | Out-Null
  if (-not (Test-Path $agentsDst)) { New-Item -ItemType Directory -Force -Path $agentsDst | Out-Null }
  Write-Ok "$devinHome"
  Write-Ok "$skillsDst"
  Write-Ok "$agentsDst"
}

# --- 2. Install rules (AGENTS.md) ---
Write-Step "Install consolidated rules"
if (Test-Path $rulesDst) {
  $existingHash = (Get-FileHash $rulesDst -Algorithm SHA256).Hash
  $newHash      = (Get-FileHash $rulesSrc  -Algorithm SHA256).Hash
  if ($existingHash -eq $newHash) {
    Write-Ok "AGENTS.md already up-to-date"
  } elseif ($Force) {
    if ($DryRun) { Write-Skip "would overwrite $rulesDst" } else { Copy-Item $rulesSrc $rulesDst -Force; Write-Ok "overwrote $rulesDst" }
  } else {
    Write-Warn "$rulesDst exists and differs from bundle. Use -Force to overwrite."
  }
} else {
  if ($DryRun) { Write-Skip "would write $rulesDst" } else { Copy-Item $rulesSrc $rulesDst; Write-Ok "wrote $rulesDst" }
}

# --- 3. Install skills ---
Write-Step "Install skills"
$skillDirs = Get-ChildItem $skillsSrc -Directory
$installed = 0; $skipped = 0; $updated = 0

foreach ($skill in $skillDirs) {
  $dst = Join-Path $skillsDst $skill.Name
  $src = $skill.FullName

  if (Test-Path $dst) {
    # Compare by hashing all files in each folder
    $srcHash = (Get-ChildItem $src -Recurse -File | Sort-Object FullName | ForEach-Object { (Get-FileHash $_.FullName -Algorithm SHA256).Hash }) -join "`n"
    $dstHash = (Get-ChildItem $dst -Recurse -File | Sort-Object FullName | ForEach-Object { (Get-FileHash $_.FullName -Algorithm SHA256).Hash }) -join "`n"

    if ($srcHash -eq $dstHash) {
      Write-Ok "$($skill.Name) (unchanged)"
      $skipped++
    } elseif ($Force) {
      if ($DryRun) { Write-Skip "would update $($skill.Name)" } else { Remove-Item $dst -Recurse -Force; Copy-Item $src $dst -Recurse -Force; Write-Ok "updated $($skill.Name)" }
      $updated++
    } else {
      Write-Warn "$($skill.Name) exists and differs. Use -Force to update."
    }
  } else {
    if ($DryRun) { Write-Skip "would install $($skill.Name)" } else { Copy-Item $src $dst -Recurse -Force; Write-Ok "installed $($skill.Name)" }
    $installed++
  }
}

# --- 3b. Install agent profiles ---
if (Test-Path $agentsSrc) {
  Write-Step "Install agent profiles"
  $agentFiles = Get-ChildItem $agentsSrc -Filter "*.md"
  $agentInstalled = 0; $agentUpdated = 0
  foreach ($agentFile in $agentFiles) {
    $dstFile = Join-Path $agentsDst $agentFile.Name
    if (Test-Path $dstFile) {
      $srcHash = (Get-FileHash $agentFile.FullName -Algorithm SHA256).Hash
      $dstHash = (Get-FileHash $dstFile -Algorithm SHA256).Hash
      if ($srcHash -eq $dstHash) {
        Write-Ok "$($agentFile.Name) (unchanged)"
      } elseif ($Force) {
        if ($DryRun) { Write-Skip "would update $($agentFile.Name)" } else { Copy-Item $agentFile.FullName $dstFile -Force; Write-Ok "updated $($agentFile.Name)" }
        $agentUpdated++
      } else {
        Write-Warn "$($agentFile.Name) exists and differs. Use -Force to update."
      }
    } else {
      if ($DryRun) { Write-Skip "would install $($agentFile.Name)" } else { Copy-Item $agentFile.FullName $dstFile; Write-Ok "installed $($agentFile.Name)" }
      $agentInstalled++
    }
  }
}

# --- 4. Summary ---
Write-Step "Summary"
Write-Host "    Skills installed : $installed"
Write-Host "    Skills updated   : $updated"
Write-Host "    Skills unchanged : $skipped"
if (Test-Path $agentsSrc) {
  Write-Host "    Agents installed : $agentInstalled"
  Write-Host "    Agents updated   : $agentUpdated"
}
if ($DryRun) { Write-Host "`nDry-run complete. Re-run without -DryRun to apply." -ForegroundColor Yellow }
else { Write-Host "`nDone. Restart Devin CLI to pick up new skills/rules." -ForegroundColor Green }
