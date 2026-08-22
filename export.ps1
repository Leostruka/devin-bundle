<#
.SYNOPSIS
  Devin bundle exporter (Windows / PowerShell).
  Regenerates the FULL Devin CLI setup in the bundle from the live config on this machine.

.DESCRIPTION
  Exports the complete Devin CLI setup:
    - AGENTS.md (consolidated rules)
    - agents/ (custom subagent profiles)
    - skills/ (auto-discovers ALL skill directories, not just manifest-listed)
    - config.json (model, theme, attribution — org_id MASKED by default)
    - hooks.v1.json (PreToolUse, PostCompaction, Stop hooks)
    - scripts/ (hook Python scripts: check-ai-signature, check-push-green, post-compaction-reminder)
    - mcp_config.json (MCP server config — tokens MASKED by default)
    - credentials.toml (API keys — ALL values MASKED by default, use -NoMask for real)

  Secrets masking:
    - credentials.toml: ALL values replaced with MASKED (file has API keys)
    - config.json: org_id replaced with MASKED
    - mcp_config.json: env values (API_KEY, TOKEN, etc.) replaced with MASKED
    - Use -NoMask to export real secrets (required to restore credentials on another machine)

  Pre-push validation:
    - All .json files must parse
    - All .py files in scripts/ must have valid syntax
    - If validation fails, push is ABORTED

.PARAMETER DryRun
  Show what would be copied without writing.

.PARAMETER Commit
  After export, run git add -A && git commit with a generated message.

.PARAMETER Push
  After commit, validate + git push. Implies -Commit.

.PARAMETER NoMask
  Do NOT mask secrets. Required to export real credentials for restoration.
  WARNING: credentials.toml contains API keys. Only use on trusted machines.

.EXAMPLE
  .\export.ps1                    # export with masked secrets
  .\export.ps1 -DryRun            # show what would be copied
  .\export.ps1 -Commit -Push      # export + commit + validate + push
  .\export.ps1 -NoMask -Commit    # export real secrets + commit (do NOT push unmasked to public repo)
#>
[CmdletBinding()]
param(
  [switch]$DryRun,
  [switch]$Commit,
  [switch]$Push,
  [switch]$NoMask
)

$ErrorActionPreference = "Stop"
$bundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$devinHome  = Join-Path $env:APPDATA "devin"

# Bundle destination paths
$rulesDst      = Join-Path $bundleRoot "AGENTS.md"
$agentsDst     = Join-Path $bundleRoot "agents"
$skillsDst     = Join-Path $bundleRoot "skills"
$configDst     = Join-Path $bundleRoot "config.json"
$scriptsDst    = Join-Path $bundleRoot "scripts"
$mcpDst        = Join-Path $bundleRoot "mcp_config.json"
$credsDst      = Join-Path $bundleRoot "credentials.toml"

# Source paths
$rulesSrc      = Join-Path $devinHome "AGENTS.md"
$agentsSrc     = Join-Path $devinHome "agents"
$skillsSrc     = Join-Path $devinHome "skills"
$configSrc     = Join-Path $devinHome "config.json"
$scriptsSrc    = Join-Path $devinHome "scripts"
$mcpSrc        = Join-Path $devinHome "mcp_config.json"
$credsSrc      = Join-Path $devinHome "credentials.toml"

$script:Warnings = @()

function Write-Step($msg) { Write-Host "`n[*] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    [+] $msg" -ForegroundColor Green }
function Write-Skip($msg) { Write-Host "    [~] $msg" -ForegroundColor Yellow }
function Write-Warn($msg) { Write-Host "    [!] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "    [x] $msg" -ForegroundColor Red }

# --- Helpers ---

function Get-FolderHash($path) {
  if (-not (Test-Path $path)) { return $null }
  $files = Get-ChildItem $path -Recurse -File | Sort-Object FullName
  if ($files.Count -eq 0) { return "" }
  $hashes = $files | ForEach-Object { (Get-FileHash $_.FullName -Algorithm SHA256).Hash }
  return ($hashes -join "`n")
}

function Get-FileHash256($path) {
  if (-not (Test-Path $path)) { return $null }
  return (Get-FileHash $path -Algorithm SHA256).Hash
}

function Write-FileLF($path, $content) {
  $lf = $content -replace "`r`n", "`n"
  $utf8NoBom = [Text.UTF8Encoding]::new($false)
  [IO.File]::WriteAllText($path, $lf, $utf8NoBom)
}

function Copy-DirRecursive($src, $dst, $label) {
  if (-not (Test-Path $src)) {
    Write-Skip "$label (source not found: $src)"
    return 0
  }
  if ($DryRun) {
    $count = (Get-ChildItem $src -Recurse -File).Count
    Write-Skip "would copy $count files from $src"
    return $count
  }
  if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
  Copy-Item $src $dst -Recurse -Force
  $count = (Get-ChildItem $dst -Recurse -File).Count
  Write-Ok "$label ($count files)"
  return $count
}

function Mask-JsonSecrets($content) {
  if ($NoMask) { return $content }
  $masked = $content
  # Mask org_id in config.json
  $masked = $masked -replace '("org_id"\s*:\s*")[^"]+', '$1MASKED'
  # Mask env values in mcp_config.json (API_KEY, TOKEN, SECRET, PASSWORD, KEY)
  $masked = $masked -replace '("(?:API_KEY|TOKEN|SECRET|PASSWORD|KEY|api_key|token|secret|password|key)"\s*:\s*")[^"]+', '$1MASKED'
  # Mask URLs with embedded tokens (sk-, gho_, ghp_, etc.)
  $masked = $masked -replace '(https://[^/\s]+:[^@/]+@)', 'https://MASKED@'
  return $masked
}

function Mask-TomlSecrets($content) {
  if ($NoMask) { return $content }
  # credentials.toml: mask all values after = sign, preserve keys
  # Format: key = "value" or key = value
  $lines = $content -split "`n"
  $masked = @()
  foreach ($line in $lines) {
    if ($line -match '^\s*#' -or $line -match '^\s*\[' -or $line.Trim() -eq "") {
      $masked += $line
      continue
    }
    if ($line -match '^(\s*\S+\s*=\s*)(.+)$') {
      $masked += "$($Matches[1])`"MASKED`""
    } else {
      $masked += $line
    }
  }
  return ($masked -join "`n")
}

function Test-JsonFile($path) {
  if (-not (Test-Path $path)) { return $true }
  try {
    $null = Get-Content $path -Raw | ConvertFrom-Json -ErrorAction Stop
    return $true
  } catch {
    return $false
  }
}

function Test-PythonSyntax($path) {
  if (-not (Test-Path $path)) { return $true }
  try {
    # Use ast.parse to validate syntax without writing .pyc files
    $code = "import ast, sys; ast.parse(open(sys.argv[1], encoding='utf-8').read())"
    $null = & python -c $code $path 2>&1
    return $LASTEXITCODE -eq 0
  } catch {
    return $false
  }
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
Write-Host "  Devin Bundle Exporter (Full Setup)" -ForegroundColor White
Write-Host "  Source : $devinHome" -ForegroundColor DarkGray
Write-Host "  Bundle : $bundleRoot" -ForegroundColor DarkGray
Write-Host "  Mask   : $(-not $NoMask)" -ForegroundColor DarkGray
if ($DryRun) { Write-Host "  Mode   : DRY-RUN" -ForegroundColor Yellow }
if ($Commit) { Write-Host "  Commit : YES" -ForegroundColor DarkGray }
if ($Push)   { Write-Host "  Push   : YES (with validation)" -ForegroundColor DarkGray }
Write-Host "================================================" -ForegroundColor DarkGray

# --- 1. AGENTS.md ---
Write-Step "Export AGENTS.md (consolidated rules)"
if (Test-Path $rulesSrc) {
  $srcHash = Get-FileHash256 $rulesSrc
  $dstHash = Get-FileHash256 $rulesDst
  if ($srcHash -eq $dstHash) {
    Write-Ok "AGENTS.md (unchanged)"
  } else {
    if ($DryRun) { Write-Skip "would copy $rulesSrc" }
    else {
      $content = Get-Content $rulesSrc -Raw
      Write-FileLF $rulesDst $content
      Write-Ok "AGENTS.md exported"
    }
  }
} else {
  Write-Warn "AGENTS.md not found at $rulesSrc"
}

# --- 1b. Dedup AGENTS.md case variants (Windows/WSL bug workaround) ---
Write-Step "Dedup AGENTS.md case variants"
Invoke-DedupAgentsMd $devinHome "source"
Invoke-DedupAgentsMd $bundleRoot "bundle"

# --- 2. agents/ (custom subagent profiles) ---
Write-Step "Export agent profiles"
if (Test-Path $agentsSrc) {
  if (-not (Test-Path $agentsDst)) {
    if (-not $DryRun) { New-Item -ItemType Directory -Force -Path $agentsDst | Out-Null }
  }
  $agentFiles = Get-ChildItem $agentsSrc -Filter "*.md" -ErrorAction SilentlyContinue
  $agentExported = 0
  foreach ($agentFile in $agentFiles) {
    $dstFile = Join-Path $agentsDst $agentFile.Name
    $srcHash = Get-FileHash256 $agentFile.FullName
    $dstHash = Get-FileHash256 $dstFile
    if ($srcHash -eq $dstHash) {
      Write-Ok "$($agentFile.Name) (unchanged)"
    } else {
      if ($DryRun) { Write-Skip "would export $($agentFile.Name)" }
      else {
        $content = Get-Content $agentFile.FullName -Raw
        Write-FileLF $dstFile $content
        $agentExported++
      }
    }
  }
  if (-not $DryRun -and $agentExported -gt 0) { Write-Ok "exported $agentExported agent profiles" }
} else {
  Write-Warn "agents/ directory not found at $agentsSrc"
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

# --- 3. skills/ (auto-discover ALL) ---
Write-Step "Export skills (auto-discover)"
if (Test-Path $skillsSrc) {
  if (-not (Test-Path $skillsDst)) {
    if (-not $DryRun) { New-Item -ItemType Directory -Force -Path $skillsDst | Out-Null }
  }
  $skillDirs = Get-ChildItem $skillsSrc -Directory -ErrorAction SilentlyContinue
  $exported = 0; $unchanged = 0; $failed = 0
  foreach ($skill in $skillDirs) {
    $src = $skill.FullName
    $dst = Join-Path $skillsDst $skill.Name
    $srcHash = Get-FolderHash $src
    $dstHash = Get-FolderHash $dst
    if ($srcHash -eq $dstHash) {
      $unchanged++
    } else {
      if ($DryRun) {
        Write-Skip "would export $($skill.Name)"
      } else {
        try {
          if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
          Copy-Item $src $dst -Recurse -Force
          $exported++
        } catch {
          Write-Err "$($skill.Name): $($_.Exception.Message)"
          $failed++
        }
      }
    }
  }
  Write-Ok "Skills: $exported exported, $unchanged unchanged, $failed failed (total: $($skillDirs.Count))"
} else {
  Write-Warn "skills/ directory not found at $skillsSrc"
}

# --- 4. config.json ---
Write-Step "Export config.json (model, theme, attribution, hooks)"
if (Test-Path $configSrc) {
  if ($DryRun) { Write-Skip "would copy config.json (mask=$(-not $NoMask))" }
  else {
    $content = Get-Content $configSrc -Raw
    $masked = Mask-JsonSecrets $content
    # Normalize absolute APPDATA paths to {{APPDATA}} placeholder for portability
    $appdataNorm = ($env:APPDATA -replace '\\', '/')
    $appdataBack = $env:APPDATA
    $masked = $masked -replace [regex]::Escape($appdataNorm), '{{APPDATA}}'
    $masked = $masked -replace [regex]::Escape($appdataBack), '{{APPDATA}}'
    Write-FileLF $configDst $masked
    if ($masked -ne $content) { Write-Ok "config.json exported (org_id MASKED, paths normalized to {{APPDATA}})" }
    else { Write-Ok "config.json exported" }
  }
} else {
  Write-Warn "config.json not found at $configSrc"
}

# --- 5. scripts/ (hook Python scripts) ---
Write-Step "Export scripts/ (hook scripts)"
$scriptCount = Copy-DirRecursive -src $scriptsSrc -dst $scriptsDst -label "scripts/"
if ($scriptCount -eq 0 -and -not (Test-Path $scriptsSrc)) {
  Write-Warn "scripts/ not found at $scriptsSrc"
}

# --- 6. mcp_config.json ---
Write-Step "Export mcp_config.json (MCP servers)"
if (Test-Path $mcpSrc) {
  if ($DryRun) { Write-Skip "would copy mcp_config.json (mask=$(-not $NoMask))" }
  else {
    $content = Get-Content $mcpSrc -Raw
    $masked = Mask-JsonSecrets $content
    Write-FileLF $mcpDst $masked
    if ($masked -ne $content) { Write-Ok "mcp_config.json exported (tokens MASKED)" }
    else { Write-Ok "mcp_config.json exported" }
  }
} else {
  Write-Skip "mcp_config.json not found at $mcpSrc (no MCP servers configured)"
}

# --- 7. credentials.toml ---
Write-Step "Export credentials.toml (API keys)"
if (Test-Path $credsSrc) {
  if ($DryRun) {
    Write-Skip "would copy credentials.toml (mask=$(-not $NoMask))"
  } else {
    $content = Get-Content $credsSrc -Raw
    $masked = Mask-TomlSecrets $content
    Write-FileLF $credsDst $masked
    if (-not $NoMask) {
      Write-Ok "credentials.toml exported (ALL values MASKED — use -NoMask for real secrets)"
    } else {
      Write-Warn "credentials.toml exported with REAL SECRETS — do NOT push to public repo"
    }
  }
} else {
  Write-Skip "credentials.toml not found at $credsSrc"
}

# --- 8. Summary ---
Write-Step "Summary"
$componentCount = 0
foreach ($p in @($rulesDst, $agentsDst, $skillsDst, $configDst, $scriptsDst, $mcpDst, $credsDst)) {
  if (Test-Path $p) { $componentCount++ }
}
Write-Host "    Components in bundle: $componentCount / 7"

if ($script:Warnings.Count -gt 0) {
  Write-Host "    Warnings: $($script:Warnings.Count)" -ForegroundColor Yellow
}

# --- 9. Pre-push validation ---
function Invoke-Validation {
  Write-Step "Pre-push validation"
  $errors = @()

  # Validate JSON files
  $jsonFiles = @($configDst, $mcpDst) | Where-Object { Test-Path $_ }
  foreach ($jf in $jsonFiles) {
    if (Test-JsonFile $jf) {
      Write-Ok "$([System.IO.Path]::GetFileName($jf)) — valid JSON"
    } else {
      Write-Err "$([System.IO.Path]::GetFileName($jf)) — INVALID JSON"
      $errors += "Invalid JSON: $jf"
    }
  }

  # Validate Python syntax in scripts/
  if (Test-Path $scriptsDst) {
    $pyFiles = Get-ChildItem $scriptsDst -Filter "*.py" -Recurse
    foreach ($pf in $pyFiles) {
      if (Test-PythonSyntax $pf.FullName) {
        Write-Ok "$($pf.Name) — valid Python"
      } else {
        Write-Err "$($pf.Name) — INVALID Python syntax"
        $errors += "Invalid Python: $($pf.FullName)"
      }
    }
  }

  # Validate AGENTS.md exists and is non-empty
  if (-not (Test-Path $rulesDst) -or (Get-Item $rulesDst).Length -eq 0) {
    Write-Err "AGENTS.md — missing or empty"
    $errors += "AGENTS.md missing or empty"
  } else {
    Write-Ok "AGENTS.md — present and non-empty"
  }

  if ($errors.Count -gt 0) {
    Write-Err "Validation FAILED with $($errors.Count) error(s). Aborting commit/push."
    foreach ($e in $errors) { Write-Host "      - $e" -ForegroundColor Red }
    return $false
  }
  Write-Ok "All validations passed"
  return $true
}

# --- 10. Git commit + push ---
if ($Commit -or $Push) {
  if ($DryRun) {
    Write-Step "Git (dry-run)"
    Write-Skip "would git add -A && commit"
    if ($Push) { Write-Skip "would validate && git push" }
  } else {
    # Validate before committing
    $valid = Invoke-Validation
    if (-not $valid) {
      Write-Err "Validation failed — aborting commit/push. Fix errors and re-run."
      exit 1
    }

    Write-Step "Git commit"
    Push-Location $bundleRoot
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
      git add -A 2>&1 | Out-Null
      $status = git status --porcelain
      if ($status) {
        $date = Get-Date -Format "yyyy-MM-dd"
        $skillCount = if (Test-Path $skillsDst) { (Get-ChildItem $skillsDst -Directory).Count } else { 0 }
        $commitMsg = @"
export: refresh devin bundle ($date)

Skills: $skillCount total
Config: AGENTS.md, agents/, config.json, hooks.v1.json, scripts/, mcp_config.json, credentials.toml
Masked: $(-not $NoMask)
"@
        git commit -m $commitMsg 2>&1 | Out-Null
        Write-Ok "committed ($skillCount skills, full config)"

        if ($Push) {
          Write-Step "Git push"
          $pushResult = git push 2>&1
          $pushExit = $LASTEXITCODE
          if ($pushExit -eq 0) {
            Write-Ok "pushed"
          } else {
            Write-Err "push failed (exit $pushExit)"
            Write-Host "      $pushResult" -ForegroundColor Red
          }
        }
      } else {
        Write-Ok "nothing to commit (bundle already up to date)"
      }
    } finally {
      $ErrorActionPreference = $prevEAP
      Pop-Location
    }
  }
}

if ($DryRun) {
  Write-Host "`nDry-run complete. Re-run without -DryRun to apply." -ForegroundColor Yellow
} else {
  Write-Host "`nExport complete." -ForegroundColor Green
  if (-not $Commit -and -not $Push) {
    Write-Host "  Tip: run with -Commit -Push to commit and push in one step." -ForegroundColor DarkGray
  }
  if (-not $NoMask) {
    Write-Host "  Note: secrets are MASKED. Use -NoMask to export real credentials." -ForegroundColor DarkGray
  }
}
