# Gate de regressao RES-1..26: cada ancora deve bater no codigo atual.
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$N = Get-Content -Raw (Join-Path $root 'devin-N.ps1')
$L = Get-Content -Raw (Join-Path $root 'devin-session-launcher.ps1')
$C = Get-Content -Raw (Join-Path $root 'devin-N.cmd')

$checks = @(
    @{ Id = 'RES-1';  Desc = 'launcher dot-sourced no comando filho'; Pass = ($N -match "devin-session-launcher\.ps1" -and $N -match "bundlePath\\devin-session-launcher") }
    @{ Id = 'RES-2';  Desc = 'branch --merged preserva unmerged';     Pass = ($N -match 'branch --merged') }
    @{ Id = 'RES-3';  Desc = 'rollback transacional de worktree';     Pass = ($N -match 'WorktreeFalha' -and $N -match 'Remove-WorktreeSafe') }
    @{ Id = 'RES-4';  Desc = 'CreatedBranches registradas';           Pass = ($N -match 'CreatedBranches \+=') }
    @{ Id = 'RES-5';  Desc = 'Esc=null cancela (nao "nova sessao")';  Pass = ($L -match 'SessaoCancelada' -and $L -match 'null -eq \$selected') }
    @{ Id = 'RES-6';  Desc = '.cmd usa pwsh, nao powershell 5.1';     Pass = ($C -match 'pwsh\.exe' -and $C -notmatch 'powershell\.exe') }
    @{ Id = 'RES-7';  Desc = 'cancelamento reporta msg';              Pass = ($N -match 'SelecaoCancelada') }
    @{ Id = 'RES-8';  Desc = '$available escalar -> array';           Pass = ($N -match '\$available = @\(') }
    @{ Id = 'RES-9';  Desc = 'zero dialogs WinForms no launcher';     Pass = ($L -notmatch 'OpenFileDialog|SaveFileDialog|System\.Windows\.Forms') }
    @{ Id = 'RES-10'; Desc = 'Find-WorkingWt shim Scoop';             Pass = ($N -match 'function Find-WorkingWt') }
    @{ Id = 'RES-11'; Desc = 'sem catch{} vazio';                     Pass = ($N -notmatch 'catch\s*\{\s*\}' -and $L -notmatch 'catch\s*\{\s*\}') }
    @{ Id = 'RES-12'; Desc = '-LiteralPath em Test/Remove-Item';      Pass = ($N -match 'Test-Path -LiteralPath' -and $L -match 'Test-Path -LiteralPath') }
    @{ Id = 'RES-13'; Desc = 'restore branch original (todos modos)'; Pass = ($N -match 'Restore-OriginalBranches -Projetos') }
    @{ Id = 'RES-14'; Desc = 'fetch --all --prune unico';             Pass = (([regex]::Matches($N, 'fetch --all --prune')).Count -eq 1) }
    @{ Id = 'RES-15'; Desc = 'deteccao WT unica (Get-ConsoleWindowInfo)'; Pass = (([regex]::Matches($N, 'Get-ConsoleWindowInfo')).Count -ge 1 -and [regex]::Matches($N, 'MainWindowHandle').Count -le 2) }
    @{ Id = 'RES-16'; Desc = 'stderr gh separado';                    Pass = ($N -match 'gh pr list' -and $N -match 'gh repo view') }
    @{ Id = 'RES-17'; Desc = 'erro devin ls reportado';               Pass = ($L -match 'ListaSessoesFalha' -and $L -match '\$ls\.Stderr') }
    @{ Id = 'RES-18'; Desc = 'PreFilter morto';                       Pass = ($L -notmatch 'PreFilter' -and $N -notmatch 'PreFilter') }
    @{ Id = 'RES-19'; Desc = 'wt Start-Process com check $proc';      Pass = ($N -match 'Start-Process -FilePath \$wtPath' -and $N -match '-not \$proc') }
    @{ Id = 'RES-20'; Desc = 'msgs centralizadas em $M/$LM';          Pass = ($N -match '\$M = @\{' -and $L -match '\$LM = @\{') }
    @{ Id = 'RES-21'; Desc = 'fuzzy + digitos + help ?';              Pass = ($L -match 'function Test-FuzzyMatch' -and $L -match "-le '9'" -and $L -match "-eq '\?'") }
    @{ Id = 'RES-22'; Desc = 'orphan dir sweep + nomes reservados';   Pass = ($N -match 'Remove-StaleWorktrees' -and $N -match 'reservedAutoNames') }
    @{ Id = 'RES-23'; Desc = 'merged-only branch delete';             Pass = ($N -match 'Remove-CreatedBranches' -and $N -match '--merged') }
    @{ Id = 'RES-24'; Desc = 'Set-StrictMode -Off';                   Pass = ($N -match 'Set-StrictMode -Off') }
    @{ Id = 'RES-25'; Desc = 'spinner sanitiza \n';                   Pass = ($L -match "-replace '\[\\r\\n\]\+'") }
    @{ Id = 'RES-26'; Desc = 'Esc sai de loops';                      Pass = ($L -match "'Escape'" -and $N -match 'SelecaoCancelada') }
)

$fail = 0
foreach ($c in $checks) {
    $status = if ($c.Pass) { 'PASS' } else { 'FAIL'; $fail++ }
    "{0} {1} {2}" -f $status, $c.Id, $c.Desc
}
"----"
"$fail FAIL / $($checks.Count) checks"
if ($fail -gt 0) { exit 1 }
