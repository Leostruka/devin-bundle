# P0-2: gate `status --porcelain` antes de `worktree remove --force`.
# EXPECT: worktree sujo + resposta 'n' -> preservado; 's' -> removido; limpo -> removido sem prompt.
$ErrorActionPreference = 'Stop'
$global:M = @{
    WorktreeSujo = 'SUJO {0}'
    WorktreeSujoConfirm = 'CONFIRM?'
    WorktreePreservado = 'PRESERVADO {0}'
    WorktreeBloqueado = 'BLOQ {0} {1}'
}
. (Join-Path $PSScriptRoot 'Import-DevinFunctions.ps1')
Import-DevinFunctions -Path (Join-Path $PSScriptRoot '..\..\devin-N.ps1') -Names @('Escape-Sq','Get-WorktreePorcelainInfo','Get-WorktreeDirtyFiles','Remove-WorktreeSafe','Remove-DirRobust')

$tmp = Join-Path $env:TEMP "devin-N-verify-p02-$PID"
New-Item -ItemType Directory -Path $tmp | Out-Null
try {
    git -C $tmp init -q repo
    $repo = Join-Path $tmp 'repo'
    git -C $repo config user.email t@t; git -C $repo config user.name t
    'base' | Set-Content (Join-Path $repo 'file.txt')
    git -C $repo add .; git -C $repo commit -qm init
    New-Item -ItemType Directory -Path (Join-Path $repo '.worktrees') | Out-Null

    $wt = Join-Path $repo '.worktrees\instancia-a'
    git -C $repo worktree add $wt -b wt-a -q

    'sujo' | Set-Content (Join-Path $wt 'file.txt')

    function global:Read-Host { param($Prompt) 'n' }
    $res = Remove-WorktreeSafe -RepoPath $repo -WorktreePath $wt
    if ($res -or -not (Test-Path -LiteralPath (Join-Path $wt 'file.txt'))) {
        Write-Output 'FAIL: worktree sujo removido apesar de resposta n'; exit 1
    }
    Write-Output '  dirty+deny -> preservado: OK'

    function global:Read-Host { param($Prompt) 's' }
    $res = Remove-WorktreeSafe -RepoPath $repo -WorktreePath $wt
    if (-not $res -or (Test-Path -LiteralPath $wt)) {
        Write-Output 'FAIL: remocao confirmada nao removeu'; exit 1
    }
    Write-Output '  dirty+confirm -> removido: OK'

    $wt2 = Join-Path $repo '.worktrees\instancia-b'
    git -C $repo worktree add $wt2 -b wt-b -q
    $res = Remove-WorktreeSafe -RepoPath $repo -WorktreePath $wt2
    if (-not $res -or (Test-Path -LiteralPath $wt2)) {
        Write-Output 'FAIL: worktree limpo nao removido'; exit 1
    }
    Write-Output '  clean -> removido sem prompt: OK'
    Write-Output 'P0-2 PASS'
}
finally {
    Pop-Location -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
