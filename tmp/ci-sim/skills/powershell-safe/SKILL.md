---
name: powershell-safe
description: Use whenever running powershell.exe/pwsh, writing .ps1 scripts, or doing file I/O via shell on Windows. Prevents blanked files, encoding corruption, and accidental deletion: read-modify-write pipeline trap, UTF-16/BOM redirection pitfalls, JSON depth truncation, dangerous aliases, empty-variable deletes, verify-after-write discipline.
triggers: [user, model]
allowed-tools: [read, exec, write, edit, grep]
---

# PowerShell Safe

PowerShell footguns silently blank files and corrupt encoding. Targets Windows PowerShell 5.1 (`powershell.exe`), the default on Windows machines without `pwsh`.

## Rule zero: file content does not go through the shell

Use `write`/`edit` tools to create or edit real files. Never:

- `echo "..." > file.ps1` for real files.
- `Set-Content`/`Out-File`/`Add-Content` for code or config.
- Redirect (`>`, `>>`) is only acceptable for disposable output (logs, temp dumps).

Redirect re-encodes, may emit BOM, does no surgical diff, and if the left side produces `$null` the existing file becomes blank.

## The classic bug: read and write the same file in one pipeline

```powershell
Get-Content $f | ForEach-Object { $_ -replace 'a','b' } | Set-Content $f
# RESULT: $f BLANKED. Set-Content opens for write before Get-Content finishes.
```

Equally fatal variants: `type $f | ... > $f`, `Import-Csv $f | ... | Export-Csv $f`.

Correct patterns, in order:

```powershell
# 1. Read fully into memory BEFORE writing
$c = [IO.File]::ReadAllText($f)
$c = $c -replace 'a','b'
[IO.File]::WriteAllText($f, $c)   # UTF-8 no BOM

# 2. Temp + move (safer: original survives mid-failure)
$tmp = "$f.tmp"
# ...generate content into $tmp...
if ((Get-Item $tmp).Length -eq 0) { throw "tmp empty, aborting" }
Move-Item -Force $tmp $f
```

## Encoding: PS 5.1 silent corruption

- `>`/`>>` are `Out-File`: in 5.1 they write **UTF-16LE with BOM**. Git sees binary, diff dies, parsers break.
- `Out-File -Encoding utf8` / `Set-Content -Encoding utf8` in 5.1 write **UTF-8 with BOM**. BOM breaks shebang, some JSON/YAML parsers, diff tools.
- UTF-8 without BOM in 5.1: `[IO.File]::WriteAllText($path, $text)`.
- Detect BOM: `Get-Content -Encoding Byte -TotalCount 3 $f` -> `239 187 191` = UTF-8 BOM; `255 254` = UTF-16LE.
- PS7 (`pwsh`) defaults to utf8NoBOM; check `$PSVersionTable.PSVersion` before relying on it.
- Never pipe `.exe` output via `>`: re-encodes to UTF-16. Capture in a variable + `WriteAllText`, or `cmd /c "foo.exe > out.txt"`.

## $null blanks files

```powershell
$content = Get-Something     # failed, returned $null
$content | Out-File $f       # $f is now BLANK
```

Before any write: `if ([string]::IsNullOrEmpty($content)) { throw "empty content" }`.

## JSON round-trip is destructive

- `ConvertTo-Json` defaults `-Depth 2`: deeper objects become `"System.Collections.Hashtable"` strings. Always `-Depth 32`.
- `ConvertFrom-Json` in 5.1 loses comments and may reorder keys. For point edits, use `edit` tool or surgical regex instead of deserialize->modify->serialize.
- After writing JSON programmatically, validate: `Get-Content $f -Raw | ConvertFrom-Json` must parse.
- `Test-Json` only exists in PS7; in 5.1 the try/catch around `ConvertFrom-Json` is the test.

## Destructive ops: Remove-Item, empty variables, -LiteralPath

```powershell
$p = Get-TargetDir                     # returned $null or ""
Remove-Item -Recurse -Force "$p\sub"   # becomes "\sub" or cwd!
```

- Check path variables: `if ([string]::IsNullOrWhiteSpace($p)) { throw }`.
- `Test-Path -LiteralPath $p` before deleting; if absent, stop.
- Use `-LiteralPath` (not `-Path`) when the path may contain `[ ] * ?` (wildcards delete neighbors).
- `-WhatIf` first on `-Recurse` when the target isn't obviously disposable.

## Quoting and escapes

- Single quotes = literal; double quotes interpolate `$var` and `` `n `` (backtick is the PS escape, not `\`).
- `&&` does not exist in PS 5.1. Chain with `;` or `cmd1; if ($LASTEXITCODE -eq 0) { cmd2 }`.
- `$?` = last cmdlet bool; `$LASTEXITCODE` = last `.exe` exit code. Do not mix.
- Inside the exec tool (Git Bash), `$` is eaten by bash. For anything beyond one line, write a `.ps1` with the `write` tool and run `powershell -NoProfile -ExecutionPolicy Bypass -File x.ps1`.

## Aliases that lie

| Alias | Actually is | Trap |
|---|---|---|
| `curl` | `Invoke-WebRequest` | Not curl.exe: no `-k`, different output, slow `.Content` download |
| `wget` | `Invoke-WebRequest` | same |
| `sc` | `Set-Content` | `sc file x` BLANKS the file; `sc.exe` is services |
| `iex` | `Invoke-Expression` | never with external input |
| `rm`,`ls`,`cat`,`cp`,`mv`,`echo` | PS cmdlets | Unix flags missing or change meaning |

In scripts write full cmdlet names or explicit `.exe` (`curl.exe`, `sc.exe`).

## Errors: try/catch catches almost nothing

- try/catch only catches **terminating errors**. Use `-ErrorAction Stop` on critical cmdlets or `$ErrorActionPreference = 'Stop'` at the top.
- `-NoProfile` when invoking scripts: user profiles inject unpredictable behavior.

## Post-write verification (mandatory)

```powershell
Get-Item $f | Select-Object Length
Get-Content $f -TotalCount 5
# JSON: Get-Content $f -Raw | ConvertFrom-Json | Out-Null
```

Size 0 or unexpected encoding = stop and investigate. "The command ran without error" is NOT verification.

## Checklist before writing/deleting via PowerShell

1. Target exists? `Test-Path` done?
2. Backup if a real file? `Copy-Item $f "$f.bak"`.
3. Content validated (non-null, parses)?
4. Explicit correct encoding? (UTF-8 no BOM = `WriteAllText`)
5. Reading and writing the same file? (forbidden in one pipeline)
6. Path variable checked non-empty? `-LiteralPath`?
7. After writing, read back and confirmed?

## Cascade

- `edge-cases`: what if $var is empty / file missing / BOM present.
- `shell-safe`: sibling skill, same class of disaster in bash.
