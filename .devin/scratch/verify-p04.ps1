# P0-4: escaping em Get-InstanceCommand + EncodedCommand uniforme no fallback pwsh.
# EXPECT: comando gerado com aspas nos valores passa no ParseInput; fallback nao usa -Command cru.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Import-DevinFunctions.ps1')
Import-DevinFunctions -Path (Join-Path $PSScriptRoot '..\..\devin-N.ps1') -Names @('Escape-Sq','Get-InstanceCommand','ConvertTo-EncodedCommand')

$global:bundleRoot = "C:\bundle'x"
$global:doneFlag = "C:\temp\flag'x"
$global:scriptPid = 1234

$inst = [PSCustomObject]@{
    WorkingDirectory = "C:\proj's"
    Branch = "feat'x"
    BaseBranch = "ma'in"
    BranchInfo = @{ Type = 'new' }
    WorktreePath = $null
    Project = [PSCustomObject]@{ IsGitRepo = $true; CurrentBranch = 'main' }
}

$cmd = Get-InstanceCommand -Inst $inst
$tok = $null; $err = $null
[void][System.Management.Automation.Language.Parser]::ParseInput($cmd, [ref]$tok, [ref]$err)
if ($err -and $err.Count -gt 0) {
    Write-Output "FAIL: comando gerado nao parseia: $($err[0].Message)"; Write-Output $cmd; exit 1
}
Write-Output '  comando com aspas nos valores parseia: OK'

$enc = ConvertTo-EncodedCommand $cmd
$decoded = [System.Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($enc))
if ($decoded -ne $cmd) { Write-Output 'FAIL: EncodedCommand round-trip diverge'; exit 1 }
Write-Output '  EncodedCommand round-trip: OK'

$src = Get-Content -LiteralPath (Join-Path $PSScriptRoot '..\..\devin-N.ps1') -Raw
if ($src -match '-NoExit -Command') { Write-Output 'FAIL: fallback pwsh ainda usa -Command cru'; exit 1 }
Write-Output '  fallback pwsh sem -Command cru: OK'
Write-Output 'P0-4 PASS'
