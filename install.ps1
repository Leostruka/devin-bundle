<#
.SYNOPSIS
  Devin bundle installer (Windows / PowerShell).
  Restores the FULL Devin CLI setup to the correct config locations.

.DESCRIPTION
  Installs all bundle components:
    - AGENTS.md          → %APPDATA%\devin\AGENTS.md
    - agents\*.md        → %APPDATA%\devin\agents\
    - skills\*           → %APPDATA%\devin\skills\
    - config.json        → %APPDATA%\devin\config.json (MERGE — preserves local org_id)
    - hooks              → merged into %APPDATA%\devin\config.json under "hooks" key
    - scripts\*          → %APPDATA%\devin\scripts\
    - mcp_config.json    → %APPDATA%\devin\mcp_config.json (skips if MASKED)
    - credentials.toml   → %APPDATA%\devin\credentials.toml (only with -RestoreSecrets)

  Behavior:
    - Files that already exist and are identical → skipped
    - Files that exist and differ → skipped unless -Force (use -Backup to save first)
    - config.json: MERGE by default (preserve local org_id, apply bundle model/theme/etc.)
      Use -Force to overwrite completely.
    - credentials.toml: only installed with -RestoreSecrets. MASKED values are skipped.
    - mcp_config.json: skipped if env values are MASKED (can't restore tokens).

.PARAMETER DryRun
  Show what would happen without writing anything.

.PARAMETER Force
  Overwrite existing files that differ. For config.json, overwrites completely (no merge).

.PARAMETER Backup
  Before overwriting, save the existing file to %USERPROFILE%\.devin-import-backup-<timestamp>\.

.PARAMETER RestoreSecrets
  Install credentials.toml with real secrets. Only works if export was done with -NoMask.
  MASKED values are skipped with a warning.

.EXAMPLE
  .\install.ps1                    # install everything (skip existing, merge config)
  .\install.ps1 -DryRun            # show what would happen
  .\install.ps1 -Force -Backup     # overwrite everything, backup first
  .\install.ps1 -RestoreSecrets    # also install credentials.toml (if unmasked)
#>
[CmdletBinding()]
param(
  [switch]$DryRun,
  [switch]$Force,
  [switch]$Backup,
  [switch]$RestoreSecrets
)

$ErrorActionPreference = "Stop"
$bundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$devinHome  = Join-Path $env:APPDATA "devin"
$backupDir  = Join-Path $env:USERPROFILE ".devin-import-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

# Bundle source paths
$rulesSrc   = Join-Path $bundleRoot "AGENTS.md"
$agentsSrc  = Join-Path $bundleRoot "agents"
$skillsSrc  = Join-Path $bundleRoot "skills"
$configSrc  = Join-Path $bundleRoot "config.json"
$scriptsSrc = Join-Path $bundleRoot "scripts"
$mcpSrc     = Join-Path $bundleRoot "mcp_config.json"
$credsSrc   = Join-Path $bundleRoot "credentials.toml"

# Destination paths
$rulesDst   = Join-Path $devinHome "AGENTS.md"
$agentsDst  = Join-Path $devinHome "agents"
$skillsDst  = Join-Path $devinHome "skills"
$configDst  = Join-Path $devinHome "config.json"
$scriptsDst = Join-Path $devinHome "scripts"
$mcpDst     = Join-Path $devinHome "mcp_config.json"
$credsDst   = Join-Path $devinHome "credentials.toml"

$script:Copied = 0
$script:Skipped = 0
$script:Overwritten = 0
$script:Backed = 0
$script:Merged = 0

function Write-Step($msg) { Write-Host "`n[*] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    [+] $msg" -ForegroundColor Green }
function Write-Skip($msg) { Write-Host "    [~] $msg" -ForegroundColor Yellow }
function Write-Warn($msg) { Write-Host "    [!] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "    [x] $msg" -ForegroundColor Red }

function Get-FileHash256($path) {
  if (-not (Test-Path $path)) { return $null }
  return (Get-FileHash $path -Algorithm SHA256).Hash
}

function Get-FolderHash($path) {
  if (-not (Test-Path $path)) { return $null }
  $files = Get-ChildItem $path -Recurse -File | Sort-Object FullName
  if ($files.Count -eq 0) { return "" }
  $hashes = $files | ForEach-Object { (Get-FileHash $_.FullName -Algorithm SHA256).Hash }
  return ($hashes -join "`n")
}

function Backup-File($path) {
  if (-not (Test-Path $path)) { return }
  $rel = $path.Replace($env:APPDATA, "").TrimStart('\', '/')
  $bPath = if ($rel) { Join-Path $backupDir $rel } else { $backupDir }
  New-Item -ItemType Directory -Path (Split-Path $bPath -Parent) -Force | Out-Null
  if ($DryRun) {
    Write-Skip "backup: $path → $bPath"
  } else {
    Copy-Item $path $bPath -Force
  }
  $script:Backed++
}

function Install-File($src, $dst, $label) {
  if (-not (Test-Path $src)) {
    Write-Skip "$label (not in bundle)"
    return
  }
  $pretty = $dst.Replace($env:APPDATA, "%APPDATA%\devin")
  if (Test-Path $dst) {
    $srcHash = Get-FileHash256 $src
    $dstHash = Get-FileHash256 $dst
    if ($srcHash -eq $dstHash) {
      Write-Ok "$label (unchanged)"
      $script:Skipped++
      return
    }
    if (-not $Force) {
      Write-Warn "$label — exists and differs (use -Force to overwrite)"
      $script:Skipped++
      return
    }
    if ($Backup) { Backup-File $dst }
    if ($DryRun) {
      Write-Skip "would overwrite $label"
    } else {
      Copy-Item $src $dst -Force
      Write-Ok "overwrote $label"
    }
    $script:Overwritten++
  } else {
    if ($DryRun) {
      Write-Skip "would install $label"
    } else {
      New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
      Copy-Item $src $dst -Force
      Write-Ok "installed $label"
    }
    $script:Copied++
  }
}

function Install-SkillDir($src, $dst, $name) {
  if (Test-Path $dst) {
    $srcHash = Get-FolderHash $src
    $dstHash = Get-FolderHash $dst
    if ($srcHash -eq $dstHash) {
      $script:Skipped++
      return "skip"
    }
    if (-not $Force) {
      $script:Skipped++
      return "diff"
    }
    if ($Backup) { Backup-File $dst }
    if ($DryRun) {
      return "would-update"
    }
    Remove-Item $dst -Recurse -Force
    Copy-Item $src $dst -Recurse -Force
    $script:Overwritten++
    return "updated"
  } else {
    if ($DryRun) {
      return "would-install"
    }
    Copy-Item $src $dst -Recurse -Force
    $script:Copied++
    return "installed"
  }
}

function Merge-ConfigJson($src, $dst) {
  # Merge bundle config into local config, preserving local org_id
  try {
    $bundleConfig = Get-Content $src -Raw | ConvertFrom-Json
  } catch {
    Write-Err "bundle config.json is invalid JSON — skipping"
    return
  }

  if (-not (Test-Path $dst)) {
    # No local config — just copy bundle with {{APPDATA}} expanded
    if ($DryRun) { Write-Skip "would install config.json" }
    else {
      $content = Get-Content $src -Raw
      $content = $content -replace '\{\{APPDATA\}\}', ($env:APPDATA -replace '\\', '/')
      $utf8NoBom = [Text.UTF8Encoding]::new($false)
      [IO.File]::WriteAllText($dst, $content, $utf8NoBom)
      Write-Ok "installed config.json ({{APPDATA}} expanded)"
    }
    $script:Copied++
    return
  }

  try {
    $localConfig = Get-Content $dst -Raw | ConvertFrom-Json
  } catch {
    Write-Warn "local config.json is invalid JSON — using -Force behavior"
    if ($Force) { Install-File $src $dst "config.json" }
    return
  }

  # If identical, skip
  $srcHash = Get-FileHash256 $src
  $dstHash = Get-FileHash256 $dst
  if ($srcHash -eq $dstHash) {
    Write-Ok "config.json (unchanged)"
    $script:Skipped++
    return
  }

  if ($Force) {
    if ($Backup) { Backup-File $dst }
    if ($DryRun) { Write-Skip "would overwrite config.json completely" }
    else {
      $content = Get-Content $src -Raw
      $content = $content -replace '\{\{APPDATA\}\}', ($env:APPDATA -replace '\\', '/')
      $utf8NoBom = [Text.UTF8Encoding]::new($false)
      [IO.File]::WriteAllText($dst, $content, $utf8NoBom)
      Write-Ok "overwrote config.json (complete, {{APPDATA}} expanded)"
    }
    $script:Overwritten++
    return
  }

  # Merge: preserve local org_id, apply bundle settings
  if ($DryRun) {
    Write-Skip "would merge config.json (preserve local org_id)"
    $script:Merged++
    return
  }

  if ($Backup) { Backup-File $dst }

  # Build merged config: start with bundle, force org_id to MASKED (never inherit bundle's),
  # then override with local org_id only if local has a real (non-MASKED) value
  $merged = $bundleConfig
  if (-not $merged.devin) { $merged | Add-Member -NotePropertyName "devin" -NotePropertyValue @{} -Force }
  $merged.devin.org_id = "MASKED"
  if ($localConfig.devin -and $localConfig.devin.org_id -and $localConfig.devin.org_id -ne "MASKED") {
    $merged.devin.org_id = $localConfig.devin.org_id
  }

  $json = ($merged | ConvertTo-Json -Depth 10) -replace "`r`n", "`n"
  # Expand {{APPDATA}} placeholder to the real path (forward slashes)
  $json = $json -replace '\{\{APPDATA\}\}', ($env:APPDATA -replace '\\', '/')
  $utf8NoBom = [Text.UTF8Encoding]::new($false)
  [IO.File]::WriteAllText($dst, $json, $utf8NoBom)
  Write-Ok "merged config.json (preserved local org_id, {{APPDATA}} expanded)"
  $script:Merged++
}

function Test-HasMasked($path) {
  if (-not (Test-Path $path)) { return $false }
  $content = Get-Content $path -Raw
  return $content -match "MASKED"
}

# --- Strip BOM from file (if present) ---
# BOM (EF BB BF) in YAML frontmatter can prevent parsers from recognizing
# the `---` delimiter, causing model/name/allowed-tools fields to be ignored.
function Invoke-StripBom($path) {
  if (-not (Test-Path $path)) { return }
  $bytes = [IO.File]::ReadAllBytes($path)
  if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    if ($DryRun) {
      Write-Skip "would strip BOM from $(Split-Path $path -Leaf)"
    } else {
      $content = [Text.Encoding]::UTF8.GetString($bytes, 3, $bytes.Length - 3)
      $utf8NoBom = [Text.UTF8Encoding]::new($false)
      [IO.File]::WriteAllText($path, $content, $utf8NoBom)
      Write-Ok "stripped BOM from $(Split-Path $path -Leaf)"
    }
  }
}

# --- Case sensitivity detection ---
# Returns $true if case-sensitive, $false if case-insensitive.
function Test-CaseSensitive($path) {
  $testName = ".__casetest_$(Get-Random)"
  $testFile = Join-Path $path $testName
  try {
    Set-Content -Path $testFile -Value "x" -ErrorAction Stop
    $upperFile = Join-Path $path $testName.ToUpper()
    $exists = Test-Path $upperFile
    Remove-Item $testFile -Force -ErrorAction SilentlyContinue
    return -not $exists
  } catch {
    return $true  # assume case-sensitive on error
  }
}

# --- Dedup AGENTS.md case variants ---
# On case-sensitive FSs: removes agents.md (lowercase) if it exists as a
# separate file. On case-insensitive FSs (Windows/WSL /mnt/c, macOS default):
# AGENTS.md and agents.md are the same file — warns about Devin CLI duplicate
# listing (known bug, not fixable from filesystem level).
function Invoke-DedupAgentsMd($dir, $label) {
  $canonical = Join-Path $dir "AGENTS.md"
  if (-not (Test-Path $canonical)) { return }

  if (Test-CaseSensitive $dir) {
    $lower = Join-Path $dir "agents.md"
    if (Test-Path $lower) {
      Write-Warn "${label}: found agents.md (lowercase) duplicate — removing"
      if ($DryRun) {
        Write-Skip "would remove agents.md duplicate"
      } else {
        Remove-Item $lower -Force
        Write-Ok "${label}: removed agents.md duplicate (kept AGENTS.md)"
      }
    }
  } else {
    Write-Skip "${label}: case-insensitive FS — Devin CLI may list AGENTS.md twice (known bug, not fixable here)"
  }
}

# --- Header ---

Write-Host "================================================" -ForegroundColor DarkGray
Write-Host "  Devin Bundle Installer (Full Setup)" -ForegroundColor White
Write-Host "  Source : $bundleRoot" -ForegroundColor DarkGray
Write-Host "  Target : $devinHome" -ForegroundColor DarkGray
if ($DryRun) { Write-Host "  Mode   : DRY-RUN" -ForegroundColor Yellow }
if ($Force)   { Write-Host "  Force  : YES" -ForegroundColor DarkGray }
if ($Backup)  { Write-Host "  Backup : YES ($backupDir)" -ForegroundColor DarkGray }
if ($RestoreSecrets) { Write-Host "  Secrets: RESTORE" -ForegroundColor DarkGray }
Write-Host "================================================" -ForegroundColor DarkGray

# Validate bundle has required files
if (-not (Test-Path $rulesSrc)) { throw "AGENTS.md not found in bundle ($bundleRoot)" }
if (-not (Test-Path $skillsSrc)) { throw "skills/ folder not found in bundle ($bundleRoot)" }

# Ensure target dirs
Write-Step "Ensure target directories"
if (-not $DryRun) {
  New-Item -ItemType Directory -Force -Path $devinHome | Out-Null
  New-Item -ItemType Directory -Force -Path $skillsDst | Out-Null
  New-Item -ItemType Directory -Force -Path $agentsDst | Out-Null
  New-Item -ItemType Directory -Force -Path $scriptsDst | Out-Null
  Write-Ok "$devinHome"
} else {
  Write-Skip "would create target dirs"
}

# --- 1. AGENTS.md ---
Write-Step "Install AGENTS.md"
Install-File -src $rulesSrc -dst $rulesDst -label "AGENTS.md"

# --- 1b. Dedup AGENTS.md case variants (Windows/WSL bug workaround) ---
Write-Step "Dedup AGENTS.md case variants"
Invoke-DedupAgentsMd $devinHome "target"
Invoke-DedupAgentsMd $bundleRoot "bundle"

# --- 2. agents/ ---
Write-Step "Install agent profiles"
if (Test-Path $agentsSrc) {
  $agentFiles = Get-ChildItem $agentsSrc -Filter "*.md"
  foreach ($agentFile in $agentFiles) {
    Install-File -src $agentFile.FullName -dst (Join-Path $agentsDst $agentFile.Name) -label $agentFile.Name
  }
} else {
  Write-Skip "agents/ not in bundle"
}

# --- 2b. Strip BOM from agent files (YAML frontmatter safety) ---
Write-Step "Strip BOM from agent files"
$agentFiles = Get-ChildItem $agentsDst -Filter "*.md" -ErrorAction SilentlyContinue
if ($agentFiles) {
  foreach ($af in $agentFiles) {
    Invoke-StripBom $af.FullName
  }
} else {
  Write-Skip "no agent files to check"
}

# --- 3. skills/ ---
Write-Step "Install skills"
if (Test-Path $skillsSrc) {
  $skillDirs = Get-ChildItem $skillsSrc -Directory
  $installed = 0; $updated = 0; $skipped = 0; $diff = 0
  foreach ($skill in $skillDirs) {
    $result = Install-SkillDir -src $skill.FullName -dst (Join-Path $skillsDst $skill.Name) -name $skill.Name
    switch ($result) {
      "installed"      { $installed++; Write-Ok "$($skill.Name) (installed)" }
      "updated"        { $updated++; Write-Ok "$($skill.Name) (updated)" }
      "skip"           { $skipped++ }
      "diff"           { $diff++; Write-Warn "$($skill.Name) — differs (use -Force)" }
      "would-install"  { Write-Skip "would install $($skill.Name)" }
      "would-update"   { Write-Skip "would update $($skill.Name)" }
    }
  }
  Write-Host "    → installed: $installed | updated: $updated | unchanged: $skipped | differs: $diff (total: $($skillDirs.Count))" -ForegroundColor DarkGray
}

# --- 4. config.json (merge) ---
Write-Step "Install config.json (merge — preserves local org_id)"
if (Test-Path $configSrc) {
  Merge-ConfigJson -src $configSrc -dst $configDst
} else {
  Write-Skip "config.json not in bundle"
}

# --- 5. scripts/ ---
Write-Step "Install scripts/ (hook scripts)"
if (Test-Path $scriptsSrc) {
  $scriptFiles = Get-ChildItem $scriptsSrc -File
  foreach ($sf in $scriptFiles) {
    Install-File -src $sf.FullName -dst (Join-Path $scriptsDst $sf.Name) -label "scripts/$($sf.Name)"
  }
} else {
  Write-Skip "scripts/ not in bundle"
}

# --- 6. mcp_config.json ---
Write-Step "Install mcp_config.json"
if (Test-Path $mcpSrc) {
  if (Test-HasMasked $mcpSrc) {
    Write-Warn "mcp_config.json has MASKED values — tokens cannot be restored"
    Write-Host "    Install the file structure anyway? Use -Force to overwrite with masked version." -ForegroundColor DarkGray
    if ($Force) {
      Install-File -src $mcpSrc -dst $mcpDst -label "mcp_config.json (masked)"
    } else {
      Write-Skip "mcp_config.json (masked — use -Force to install structure, tokens need manual restore)"
    }
  } else {
    Install-File -src $mcpSrc -dst $mcpDst -label "mcp_config.json"
  }
} else {
  Write-Skip "mcp_config.json not in bundle"
}

# --- 7. credentials.toml ---
Write-Step "Install credentials.toml"
if (Test-Path $credsSrc) {
  if (-not $RestoreSecrets) {
    Write-Skip "credentials.toml — use -RestoreSecrets to install"
  } elseif (Test-HasMasked $credsSrc) {
    Write-Warn "credentials.toml has MASKED values — cannot restore real secrets"
    Write-Host "    Re-export with -NoMask on the source machine, then re-install with -RestoreSecrets." -ForegroundColor DarkGray
  } else {
    Install-File -src $credsSrc -dst $credsDst -label "credentials.toml (REAL SECRETS)"
    Write-Warn "credentials.toml installed with real secrets — keep this machine secure"
  }
} else {
  Write-Skip "credentials.toml not in bundle"
}

# --- Summary ---
Write-Step "Summary"
Write-Host "    Installed:   $script:Copied" -ForegroundColor Green
Write-Host "    Overwritten: $script:Overwritten" -ForegroundColor Yellow
Write-Host "    Merged:      $script:Merged" -ForegroundColor Cyan
Write-Host "    Skipped:     $script:Skipped" -ForegroundColor DarkYellow
Write-Host "    Backups:     $script:Backed" -ForegroundColor DarkCyan

if ($script:Backed -gt 0 -and -not $DryRun) {
  Write-Host "`n    Backups saved in: $backupDir" -ForegroundColor DarkCyan
}

if ($DryRun) {
  Write-Host "`nDry-run complete. Re-run without -DryRun to apply." -ForegroundColor Yellow
} else {
  Write-Host "`nDone. Restart Devin CLI to pick up new config." -ForegroundColor Green
  if (-not $RestoreSecrets -and (Test-Path $credsSrc)) {
    Write-Host "  Tip: run with -RestoreSecrets to install credentials.toml." -ForegroundColor DarkGray
  }
}
