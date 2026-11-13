# P0-3: Remove-StaleWorktrees escopado por sessao.
# EXPECT: worktree locked (outra sessao) preservado; unlocked removido;
#         orfao preservado com marcador de sessao viva estrangeira; removido quando ela morre.
$ErrorActionPreference = 'Stop'
$global:M = @{
    WorktreeSujo = 'SUJO {0}'
    WorktreeSujoConfirm = 'CONFIRM?'
    WorktreePreservado = 'PRESERVADO {0}'
    WorktreeBloqueado = 'BLOQ {0} {1}'
}
function global:Read-Host { param($Prompt) 'n' }
. (Join-Path $PSScriptRoot 'Import-DevinFunctions.ps1')
Import-DevinFunctions -Path (Join-Path $PSScriptRoot '..\..\devin-N.ps1') -Names @('Escape-Sq','Get-WorktreePorcelainInfo','Get-WorktreeDirtyFiles','Remove-WorktreeSafe','Remove-DirRobust','Remove-StaleWorktrees')

# $env:TEMP devolve path 8.3 (FINGER~1); git registra path longo no porcelain.
# Rodar o repo dentro de scratch garante match de path com worktree list.
$tmp = Join-Path $PSScriptRoot "verify-p03-$PID"
New-Item -ItemType Directory -Path $tmp | Out-Null
$sleeper = $null
try {
    git -C $tmp init -q repo
    $repo = Join-Path $tmp 'repo'
    git -C $repo config user.email t@t; git -C $repo config user.name t
    'base' | Set-Content (Join-Path $repo 'file.txt')
    git -C $repo add .; git -C $repo commit -qm init
    $wtRoot = Join-Path $repo '.worktrees'
    New-Item -ItemType Directory -Path $wtRoot | Out-Null

    $wtA = Join-Path $wtRoot 'instancia-a'
    git -C $repo worktree add $wtA -b wt-a -q
    git -C $repo worktree lock $wtA --reason "devin-N 999999"
    $wtB = Join-Path $wtRoot 'instancia-b'
    git -C $repo worktree add $wtB -b wt-b -q

    $info = Get-WorktreePorcelainInfo -RepoPath $repo
    $keyA = ($wtA -replace '/', '\').TrimEnd('\')
    Write-Output ("  porcelain locked[{0}] reason='{1}'" -f $info[$keyA].Locked, $info[$keyA].Reason)
    if (-not $info[$keyA].Locked) { Write-Output 'FAIL: lock nao aparece no porcelain'; exit 1 }

    Remove-StaleWorktrees -RepoPath $repo
    if (-not (Test-Path -LiteralPath $wtA)) { Write-Output 'FAIL: worktree locked removido pelo sweep'; exit 1 }
    if (Test-Path -LiteralPath $wtB) { Write-Output 'FAIL: worktree unlocked preservado pelo sweep'; exit 1 }
    Write-Output '  locked preservado + unlocked varrido: OK'

    $orphan = Join-Path $wtRoot 'instancia-x'
    New-Item -ItemType Directory -Path $orphan | Out-Null
    $sleeper = Start-Process -FilePath pwsh -ArgumentList '-NoProfile','-Command','Start-Sleep 120' -PassThru
    New-Item -ItemType File -Path (Join-Path $wtRoot ".session-$($sleeper.Id)") -Force | Out-Null

    Remove-StaleWorktrees -RepoPath $repo
    if (-not (Test-Path -LiteralPath $orphan)) { Write-Output 'FAIL: orfao varrido com sessao estrangeira viva'; exit 1 }
    Write-Output '  orfao preservado com sessao estrangeira viva: OK'

    Stop-Process -Id $sleeper.Id -Force; $sleeper = $null
    Remove-StaleWorktrees -RepoPath $repo
    if (Test-Path -LiteralPath $orphan) { Write-Output 'FAIL: orfao preservado apos sessao estrangeira morrer'; exit 1 }
    if (Test-Path -LiteralPath (Join-Path $wtRoot '.session-*')) { }
    Write-Output '  orfao varrido apos morte da sessao estrangeira: OK'
    Write-Output 'P0-3 PASS'
}
finally {
    if ($sleeper) { Stop-Process -Id $sleeper.Id -Force -ErrorAction SilentlyContinue }
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
