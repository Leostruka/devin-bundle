$fail = $false
foreach ($f in 'devin-N.ps1', 'devin-session-launcher.ps1') {
    $t = $null; $e = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path (Join-Path $PSScriptRoot "..\..\$f")), [ref]$t, [ref]$e)
    if ($e) { $e | ForEach-Object { Write-Host "$f`: $($_.Message)" }; $fail = $true }
}
if ($fail) { exit 1 }
'PARSE OK'
