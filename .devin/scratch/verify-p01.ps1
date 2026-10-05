# P0-1: restore de branch original em todos os modos + delete merged-only de branches registradas.
# EXPECT: HEAD volta a main; branch merged deletada; unmerged preservada; proj sem OriginalBranch ignorado.
$ErrorActionPreference = 'Stop'
$global:M = @{
    BranchOriginalRestaurada = 'REST {0}'
    BranchOriginalFalha = 'FALHA {0}'
}
. (Join-Path $PSScriptRoot 'Import-DevinFunctions.ps1')
Import-DevinFunctions -Path (Join-Path $PSScriptRoot '..\..\devin-N.ps1') -Names @('Restore-OriginalBranches','Remove-CreatedBranches')

$tmp = Join-Path $env:TEMP "devin-N-verify-p01-$PID"
New-Item -ItemType Directory -Path $tmp | Out-Null
try {
    git -C $tmp init -q -b main repo
    $repo = Join-Path $tmp 'repo'
    git -C $repo config user.email t@t; git -C $repo config user.name t
    'base' | Set-Content (Join-Path $repo 'file.txt')
    git -C $repo add .; git -C $repo commit -qm init

    # simula: filho criou devin-abc-a no dir real; outra branch com commit unmerged
    git -C $repo switch -c devin-abc-a -q
    git -C $repo switch -c devin-unmerged main -q
    'x' | Set-Content (Join-Path $repo 'u.txt')
    git -C $repo add u.txt; git -C $repo commit -qm u
    git -C $repo switch devin-abc-a -q
    $head = git -C $repo branch --show-current
    if ($head -ne 'devin-abc-a') { Write-Output "FAIL setup: head=$head"; exit 1 }

    $proj = [PSCustomObject]@{
        Path = $repo; IsGitRepo = $true; OriginalBranch = 'main'
        CreatedWorktrees = @(); CreatedBranches = @('devin-abc-a','devin-unmerged')
        WorktreesRoot = $null
    }
    $projNull = [PSCustomObject]@{
        Path = $repo; IsGitRepo = $true; OriginalBranch = $null
        CreatedWorktrees = @(); CreatedBranches = @(); WorktreesRoot = $null
    }

    Restore-OriginalBranches -Projetos @($proj, $projNull)
    $head = git -C $repo branch --show-current
    if ($head -ne 'main') { Write-Output "FAIL: head=$head (esperado main)"; exit 1 }
    Write-Output '  restore -> main: OK'

    Remove-CreatedBranches -Projetos @($proj)
    if (git -C $repo branch --list devin-abc-a) { Write-Output 'FAIL: branch merged nao deletada'; exit 1 }
    if (-not (git -C $repo branch --list devin-unmerged)) { Write-Output 'FAIL: branch unmerged deletada'; exit 1 }
    Write-Output '  merged deletada + unmerged preservada: OK'
    Write-Output 'P0-1 PASS'
}
finally {
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
