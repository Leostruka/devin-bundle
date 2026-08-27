# devin-N.ps1 — Launcher do Devin com as funcoes 2,3,4,5,7,8
# Suporta 1 a 4 instancias com worktrees isoladas.
# O comando `devin` inicia um REPL interativo no diretorio atual.

# 2. Salva o diretorio atual
$diretorioOriginal = Get-Location
$bundleRoot = $PSScriptRoot

# 3. Prefere PowerShell 7 para subprocessos
$psExecutable = "powershell.exe"
if (Get-Command pwsh -ErrorAction SilentlyContinue) {
    $psExecutable = "pwsh.exe"
}
Write-Host "Usando terminal base: $psExecutable" -ForegroundColor DarkGray

# 4. Carrega ConsoleGuiTools e prepara TUI no terminal
Add-Type -AssemblyName System.Windows.Forms
Import-Module Microsoft.PowerShell.ConsoleGuiTools -ErrorAction Stop
. (Join-Path $bundleRoot "devin-session-launcher.ps1")

function Select-FolderTerminal {
    param([string]$InitialPath)

    if (-not (Get-Command Out-ConsoleGridView -ErrorAction SilentlyContinue)) { return $InitialPath }
    if (-not (Test-Path -LiteralPath $InitialPath -PathType Container)) { $InitialPath = (Get-Location).Path }

    $current = $InitialPath
    while ($true) {
        $items = [System.Collections.ArrayList]::new()
        [void]$items.Add([PSCustomObject]@{ Name = '[Usar esta pasta]'; Caminho = $current; Tipo = 'acao' })

        $parent = Split-Path -Parent -Path $current
        if ($parent -and $parent -ne $current) {
            [void]$items.Add([PSCustomObject]@{ Name = '[Voltar]'; Caminho = $parent; Tipo = 'acao' })
        }
        else {
            [void]$items.Add([PSCustomObject]@{ Name = '[Trocar de drive]'; Caminho = ''; Tipo = 'acao' })
        }

        $subdirs = Get-ChildItem -Path $current -Directory -ErrorAction SilentlyContinue | Sort-Object Name
        foreach ($d in $subdirs) {
            [void]$items.Add([PSCustomObject]@{ Name = $d.Name; Caminho = $d.FullName; Tipo = 'pasta' })
        }

        $selected = $items | Out-ConsoleGridView -Title "Selecione o workspace" -OutputMode Single
        if (-not $selected) { return $null }

        if ($selected.Tipo -eq 'acao' -and $selected.Name -eq '[Usar esta pasta]') { return $selected.Caminho }
        if ($selected.Tipo -eq 'acao' -and $selected.Name -eq '[Trocar de drive]') {
            $drives = [System.IO.DriveInfo]::GetDrives() |
                Where-Object { $_.DriveType -in @('Fixed', 'Network') } |
                ForEach-Object {
                    [PSCustomObject]@{
                        Name = "Drive $($_.Name) ($($_.VolumeLabel))"
                        Caminho = $_.Name
                        Tipo = 'drive'
                    }
                }
            $driveSelected = $drives | Out-ConsoleGridView -Title "Selecione o drive" -OutputMode Single
            if ($driveSelected) { $current = $driveSelected.Caminho }
            continue
        }
        $current = $selected.Caminho
    }
}

# 5. Seleciona workspace via terminal
Write-Host "`nSelecione o workspace no terminal..." -ForegroundColor Cyan
$workspacePath = Select-FolderTerminal -InitialPath $diretorioOriginal.Path
if (-not $workspacePath) {
    Write-Host "Selecao de workspace cancelada. Encerrando." -ForegroundColor Yellow
    exit
}
if ($workspacePath -ne $diretorioOriginal.Path) {
    Set-Location $workspacePath
    Write-Host "Workspace definido para: $workspacePath`n" -ForegroundColor Green
}
else {
    Write-Host "Nenhuma pasta selecionada. Mantendo no diretorio atual.`n" -ForegroundColor Yellow
}

# 5. Carrega utilitarios Win32 para redimensionar janelas
if (-not ("WindowUtil" -as [type])) {
    Add-Type @"
    using System;
    using System.Runtime.InteropServices;

    public class WindowUtil {
        [StructLayout(LayoutKind.Sequential)]
        public struct RECT {
            public int Left;
            public int Top;
            public int Right;
            public int Bottom;
        }

        [DllImport("user32.dll")]
        public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

        [DllImport("kernel32.dll")]
        public static extern IntPtr GetConsoleWindow();

        [DllImport("user32.dll")]
        public static extern bool GetWindowRect(IntPtr hwnd, out RECT lpRect);
    }
"@
}

# ============================================================
# Funcoes auxiliares de metadados Git/GitHub
# ============================================================

function Get-BranchMetadata {
    param([string]$RepoPath)
    $meta = @{}
    try {
        $remoteMeta = @{}
        $remoteLines = git -C $RepoPath for-each-ref 'refs/remotes' --format='%(refname:short)|%(objectname:short)|%(committerdate:iso8601)' 2>&1
        foreach ($line in $remoteLines) {
            $parts = $line -split '\|', 3
            if ($parts.Count -lt 3) { continue }
            $ref = $parts[0]
            if ($ref -match '^([^/]+)/(.+)$' -and $matches[2] -ne 'HEAD') {
                $remoteName = $matches[1]
                $branchName = $matches[2]
                $sha = $parts[1]
                $date = if ($parts[2]) { [datetime]::Parse($parts[2], [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::RoundtripKind) } else { $null }
                $remoteMeta[$branchName] = @{
                    Remote = $remoteName
                    Ref = $ref
                    Sha = $sha
                    Date = $date
                }
            }
        }

        $headLines = git -C $RepoPath for-each-ref 'refs/heads' --format='%(refname:short)|%(upstream:short)|%(objectname:short)|%(committerdate:iso8601)' 2>&1
        foreach ($line in $headLines) {
            $parts = $line -split '\|', 4
            if ($parts.Count -lt 4) { continue }
            $name = $parts[0]
            $upstream = $parts[1]
            $sha = $parts[2]
            $lastCommit = if ($parts[3]) { [datetime]::Parse($parts[3], [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::RoundtripKind) } else { $null }
            $hasUpstream = -not [string]::IsNullOrWhiteSpace($upstream)
            $remoteInfo = $remoteMeta[$name]
            $existsOnRemote = $null -ne $remoteInfo

            $ahead = 0
            $behind = 0
            $target = $null
            if ($hasUpstream) { $target = $upstream }
            elseif ($existsOnRemote) { $target = $remoteInfo.Ref }

            if ($target) {
                $counts = git -C $RepoPath rev-list --left-right --count "refs/heads/$name...$target" 2>&1
                if ($counts -and $counts -match '(\d+)\s+(\d+)') {
                    $ahead = [int]$matches[1]
                    $behind = [int]$matches[2]
                }
            }

            if ($existsOnRemote -and $remoteInfo.Date -and ((-not $lastCommit) -or ($remoteInfo.Date -gt $lastCommit))) {
                $lastCommit = $remoteInfo.Date
                $sha = $remoteInfo.Sha
            }

            $meta[$name] = @{
                Type = if ($hasUpstream) { 'tracked' } else { 'local' }
                Upstream = $upstream
                HasUpstream = ($hasUpstream -or $existsOnRemote)
                ExistsOnRemote = $existsOnRemote
                Ahead = $ahead
                Behind = $behind
                LastCommit = $lastCommit
                Sha = $sha
            }
        }

        foreach ($name in $remoteMeta.Keys) {
            if (-not $meta.ContainsKey($name)) {
                $ri = $remoteMeta[$name]
                $meta[$name] = @{
                    Type = 'remote'
                    Upstream = $ri.Ref
                    HasUpstream = $true
                    ExistsOnRemote = $true
                    Ahead = 0
                    Behind = 0
                    LastCommit = $ri.Date
                    Sha = $ri.Sha
                }
            }
        }
    }
    catch { Write-Warning "Falha ao obter metadados das branches: $_" }
    return $meta
}

function Get-PullRequestMap {
    param([string]$RepoPath)
    $map = @{}
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { return $map }
    try {
        Push-Location -LiteralPath $RepoPath
        try {
            $json = gh pr list --state all --json number,headRefName,state,isDraft,reviewDecision,statusCheckRollup,author,updatedAt,createdAt,mergedAt --limit 200 2>&1 | Out-String
        }
        finally { Pop-Location }
        if ($json -and $json.Trim()) {
            $list = $json | ConvertFrom-Json
            foreach ($pr in $list) {
                $existing = $map[$pr.headRefName]
                $prUpdated = [datetime]$pr.updatedAt
                if ((-not $existing) -or ($prUpdated -gt [datetime]$existing.updatedAt)) {
                    $map[$pr.headRefName] = $pr
                }
            }
        }
    }
    catch { Write-Warning "Falha ao listar PRs: $_" }
    return $map
}

function Get-ProtectedBranchSet {
    param([string]$RepoPath)
    $set = @{}
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { return $set }
    try {
        Push-Location -LiteralPath $RepoPath
        try {
            $nameWithOwner = (gh repo view --json nameWithOwner -q .nameWithOwner 2>&1).Trim()
            if ($? -and $nameWithOwner -and $nameWithOwner -notmatch 'error|fatal') {
                $names = gh api "repos/$nameWithOwner/branches?per_page=100" --paginate --jq '.[] | select(.protected == true) | .name' 2>&1
                if ($?) {
                    foreach ($n in $names) { $set[$n.Trim()] = $true }
                }
            }
        }
        finally { Pop-Location }
    }
    catch { Write-Warning "Falha ao obter branches protegidas: $_" }
    return $set
}

function Get-DefaultBranchName {
    param([string]$RepoPath)
    $default = $null
    if (Get-Command gh -ErrorAction SilentlyContinue) {
        try {
            Push-Location -LiteralPath $RepoPath
            try {
                $output = (gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>&1).Trim()
                if ($? -and $output -and $output -notmatch 'error|fatal') { $default = $output }
            }
            finally { Pop-Location }
        }
        catch { Write-Verbose "Falha ao detectar branch default via gh: $_" }
    }
    if (-not $default) {
        try {
            Push-Location -LiteralPath $RepoPath
            try {
                $ref = git rev-parse --abbrev-ref refs/remotes/origin/HEAD 2>&1
                if ($ref -match '^origin/(.+)$') { $default = $matches[1] }
            }
            finally { Pop-Location }
        }
        catch { Write-Verbose "Falha ao detectar branch default via origin/HEAD: $_" }
    }
    if (-not $default) {
        try {
            Push-Location -LiteralPath $RepoPath
            try {
                $info = git remote show origin 2>&1
                $m = $info | Select-String -Pattern 'HEAD branch:\s*(.+)$'
                if ($m) { $default = $m.Matches[0].Groups[1].Value.Trim() }
            }
            finally { Pop-Location }
        }
        catch { Write-Verbose "Falha ao detectar branch default via git remote show: $_" }
    }
    return $default
}

function Format-BranchStatus {
    param([string]$BranchName, [hashtable]$BranchOption, [hashtable]$MetaMap, [hashtable]$PrMap, [hashtable]$ProtectedSet, [string]$DefaultBranch, [switch]$Short)
    $tokens = @()
    if ($BranchOption.IsCurrent) { $tokens += 'atual' }
    if ($BranchOption.Type -eq 'remote') { $tokens += 'remota' }

    $meta = $MetaMap[$BranchName]
    if ($meta) {
        if (-not $meta.HasUpstream -and -not $meta.ExistsOnRemote) {
            $tokens += 'sem remoto'
        }
        else {
            if ($meta.Ahead -gt 0 -and $meta.Behind -gt 0) {
                $tokens += "divergiu +$($meta.Ahead)/-$($meta.Behind)"
            }
            elseif ($meta.Ahead -gt 0) {
                $tokens += "ahead +$($meta.Ahead)"
            }
            elseif ($meta.Behind -gt 0) {
                $tokens += "behind -$($meta.Behind)"
            }
        }
    }

    $pr = $PrMap[$BranchName]
    if ($pr) {
        $state = $pr.state
        if ($pr.mergedAt) { $state = 'merged' }
        elseif ($state -eq 'OPEN') { $state = if ($pr.isDraft) { 'rascunho' } else { 'aberto' } }
        elseif ($state -eq 'CLOSED') { $state = 'fechado' }
        else { $state = $state.ToString().ToLower() }
        if ($Short) {
            $tokens += "PR#$($pr.number) $state"
        }
        else {
            $review = if ($pr.reviewDecision) { $pr.reviewDecision.ToString().ToLower().Replace('_', ' ') } else { 'sem revisao' }
            $ci = 'n/a'
            if ($pr.statusCheckRollup) {
                $rollups = @($pr.statusCheckRollup)
                if ($rollups.Count -gt 0) {
                    $anyPending = $rollups | Where-Object { ($_.status -and $_.status -ne 'COMPLETED') -or ($_.state -and $_.state -eq 'PENDING') }
                    if ($anyPending) {
                        $ci = 'PENDING'
                    }
                    else {
                        $failures = $rollups | Where-Object {
                            ($_.conclusion -and $_.conclusion -notin @('SUCCESS','NEUTRAL','SKIPPED','null')) -or
                            ($_.state -and $_.state -notin @('SUCCESS','NEUTRAL','SKIPPED','null'))
                        }
                        if ($failures) { $ci = 'FAILURE' }
                        else { $ci = 'SUCCESS' }
                    }
                }
            }
            $tokens += "PR #$($pr.number) $state | autor:$($pr.author.login) | $review | CI:$ci"
        }
    }

    if (-not $Short) {
        $dateValue = $null
        if ($pr -and $pr.updatedAt) { $dateValue = $pr.updatedAt }
        elseif ($meta -and $meta.LastCommit) { $dateValue = $meta.LastCommit }
        if ($dateValue) {
            try {
                $dt = if ($dateValue -is [datetime]) { $dateValue } else { [datetime]::Parse($dateValue, [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::RoundtripKind) }
                $days = [int]((Get-Date) - $dt).TotalDays
                if ($days -gt 30) { $tokens += "stale ${days}d" }
                else { $tokens += "ativo ${days}d" }
            }
            catch { Write-Verbose "Falha ao calcular atividade/stale para '$BranchName': $_" }
        }
    }

    if ($BranchName -eq $DefaultBranch) { $tokens += 'default' }
    if ($ProtectedSet[$BranchName]) { $tokens += 'protegida' }

    if ($tokens.Count -eq 0) { return '' }
    return ' [' + ($tokens -join ' | ') + ']'
}

function Remove-StaleWorktrees {
    param([string]$RepoPath)
    try {
        Push-Location -LiteralPath $RepoPath
        try {
            $lines = git worktree list --porcelain 2>&1
        }
        finally { Pop-Location }
        $paths = @()
        $currentPath = $null
        foreach ($line in $lines) {
            if ($line -match '^worktree\s+(.+)$') {
                $currentPath = $matches[1]
                $normPath = $currentPath -replace '/', '\'
                if ($normPath -match '\\\.worktrees\\instancia-') {
                    $paths += $currentPath
                }
            }
            elseif ($line -eq '') { $currentPath = $null }
        }
        foreach ($p in $paths) {
            try {
                Push-Location -LiteralPath $RepoPath
                try { $null = git worktree remove "$p" --force 2>&1 } finally { Pop-Location }
            }
            catch { Write-Verbose "Falha ao remover worktree '$p': $_" }
            if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction SilentlyContinue }
        }
        Push-Location -LiteralPath $RepoPath
        try { $null = git worktree prune 2>&1 } finally { Pop-Location }
    }
    catch { Write-Warning "Falha ao remover worktrees antigas: $_" }
}

function Select-BranchTerminal {
    param(
        [array]$Options,
        [hashtable]$MetaMap,
        [hashtable]$PrMap,
        [hashtable]$ProtectedSet,
        [string]$DefaultBranch,
        [string]$Title,
        [string]$PreFilter = ''
    )

    if (-not (Get-Command Out-ConsoleGridView -ErrorAction SilentlyContinue)) { return $null }

    $rows = foreach ($opt in $Options) {
        $status = Format-BranchStatus -BranchName $opt.Name -BranchOption $opt -MetaMap $MetaMap -PrMap $PrMap -ProtectedSet $ProtectedSet -DefaultBranch $DefaultBranch
        [PSCustomObject]@{
            Name = $opt.Name
            Tipo = $opt.Type
            Atual = if ($opt.IsCurrent) { 'sim' } else { '' }
            Status = $status
        }
    }

    $selected = $rows | Out-ConsoleGridView -Title $Title -OutputMode Single -Filter $PreFilter
    if (-not $selected) { return $null }
    return ($Options | Where-Object { $_.Name -eq $selected.Name } | Select-Object -First 1)
}

function Get-ConsoleWindowInfo {
    $currentPid = $PID
    $hwnd = [IntPtr]::Zero
    $insideWT = $false
    while ($true) {
        $cimProc = Get-CimInstance Win32_Process -Filter "ProcessId=$currentPid" -ErrorAction SilentlyContinue
        if (-not $cimProc -or $cimProc.ParentProcessId -eq 0) { break }

        $parentProc = Get-Process -Id $cimProc.ParentProcessId -ErrorAction SilentlyContinue
        if ($parentProc -and $parentProc.Name -eq "WindowsTerminal") {
            $hwnd = $parentProc.MainWindowHandle
            $insideWT = $true
            break
        }
        $currentPid = $cimProc.ParentProcessId
    }
    if ($hwnd -eq [IntPtr]::Zero) {
        $hwnd = [WindowUtil]::GetConsoleWindow()
    }
    return [PSCustomObject]@{ Handle = $hwnd; InsideWT = $insideWT }
}

$wtInfo = Get-ConsoleWindowInfo
$hwndMain = $wtInfo.Handle
$insideWT = $wtInfo.InsideWT
$windowUtilAvailable = $false

$rectOriginal = New-Object WindowUtil+RECT
if ($hwndMain -ne [IntPtr]::Zero -and [WindowUtil]::GetWindowRect($hwndMain, [ref]$rectOriginal)) {
    $origX = $rectOriginal.Left
    $origY = $rectOriginal.Top
    $origW = $rectOriginal.Right - $rectOriginal.Left
    $origH = $rectOriginal.Bottom - $rectOriginal.Top
    $windowUtilAvailable = $true
}
else {
    Write-Host "Aviso: Nao foi possivel obter as dimensoes da janela. Redimensionamento desabilitado." -ForegroundColor Yellow
    $origX = 0
    $origY = 0
    $origW = 0
    $origH = 0
}

# 3. Detecta o monitor atual
$currentScreen = [System.Windows.Forms.Screen]::FromHandle($hwndMain)
$monitor = $currentScreen.WorkingArea
$W = $monitor.Width
$H = $monitor.Height
$OffsetX = $monitor.Left
$OffsetY = $monitor.Top

# 4. Escolhe quantas instancias iniciar
$isGitRepo = Test-Path -LiteralPath (Join-Path $workspacePath ".git")
if ($isGitRepo) {
    $titulo = "Quantidade de Janelas"
    $mensagem = "Escolha quantas instancias do devin iniciar:"
    $opcoes = [System.Management.Automation.Host.ChoiceDescription[]] @(
        "&1 - Uma instancia (Tela inteira)",
        "&2 - Duas instancias com Worktree isolado (Lado a Lado)",
        "&3 - Tres instancias com Worktree isolado",
        "&4 - Quatro instancias com Worktree isolado (2x2)"
    )
    $escolha = $host.UI.PromptForChoice($titulo, $mensagem, $opcoes, 0)
    $numInstancias = $escolha + 1
}
else {
    $numInstancias = 1
    Write-Host "Workspace nao e um repositorio Git. Apenas 1 instancia permitida." -ForegroundColor DarkYellow
}
Write-Host "`nConfigurando $numInstancias instancia(s) no workspace escolhido..." -ForegroundColor Cyan

# 5. Prepara worktrees isoladas
$labels = @('A','B','C','D')
$positions = switch ($numInstancias) {
    2 { @('esquerda','direita','','') }
    3 { @('esquerda','superior-direita','inferior-direita','') }
    4 { @('superior-esquerda','superior-direita','inferior-esquerda','inferior-direita') }
    default { @('','','','') }
}

$worktrees = @()
$createdWorktrees = @()
$branches = @()
$createdBranches = @()
$branchInfos = @()
$worktreesRoot = $null
$singleInstanceMode = $false
$originalBranch = $null

if ($isGitRepo) {
    Write-Host "`n[WORKTREE] Workspace e um repositorio Git." -ForegroundColor Magenta

    # Limpa worktrees antigas de execucoes anteriores
    Remove-StaleWorktrees -RepoPath $workspacePath

    # Sincroniza referencias remotas antes de apresentar as branches
    Write-Host "Sincronizando referencias remotas..." -ForegroundColor DarkGray
    $null = git -C $workspacePath fetch --all --prune 2>&1
    if ($?) {
        Write-Host "  Referencias remotas atualizadas." -ForegroundColor Green
    }
    else {
        Write-Host "  Nao foi possivel atualizar as referencias remotas (sem acesso ou sem remoto configurado)." -ForegroundColor Yellow
    }

    # Obtem metadados das branches e do GitHub
    Write-Host "Obtendo metadados das branches..." -ForegroundColor DarkGray
    $branchMeta = Get-BranchMetadata -RepoPath $workspacePath
    $prMap = Get-PullRequestMap -RepoPath $workspacePath
    $protectedSet = Get-ProtectedBranchSet -RepoPath $workspacePath
    $defaultBranch = Get-DefaultBranchName -RepoPath $workspacePath

    Write-Host "Listando branches existentes..." -ForegroundColor DarkGray

    $localBranches = @()
    $localBranches += @((git -C $workspacePath branch --format='%(refname:short)' 2>$null) | Where-Object {
        $_ -ne "" -and $_ -notmatch "^(main|master|develop|HEAD)$"
    })

    $remoteBranches = @()
    $remoteBranches += @((git -C $workspacePath branch -r --format='%(refname:short)' 2>$null) | Where-Object {
        $_ -ne "" -and $_ -notmatch "HEAD" -and $_ -notmatch "(main|master|develop)$" -and $_ -ne "origin"
    } | ForEach-Object {
        $clean = $_ -replace '^origin/', ''
        if ($clean -and $clean -ne 'HEAD') { $clean }
    })

    $remoteOnly = @($remoteBranches | Where-Object { $_ -notin $localBranches })
    $currentBranch = git -C $workspacePath branch --show-current 2>$null

    $allOptions = @()

    if ($defaultBranch) {
        $localDefault = [bool](git -C $workspacePath rev-parse --verify --quiet $defaultBranch 2>$null)
        $remoteDefault = [bool](git -C $workspacePath rev-parse --verify --quiet "origin/$defaultBranch" 2>$null)
        if ($localDefault -or $remoteDefault) {
            $allOptions += @{
                Name = $defaultBranch
                Type = if ($localDefault) { "local" } else { "remote" }
                IsCurrent = ($defaultBranch -eq $currentBranch)
            }
        }
    }

    if ($localBranches.Count -gt 0) {
        foreach ($b in $localBranches) {
            $allOptions += @{ Name = $b; Type = "local"; IsCurrent = ($b -eq $currentBranch) }
        }
    }

    if ($remoteOnly.Count -gt 0) {
        foreach ($b in $remoteOnly) {
            $allOptions += @{ Name = $b; Type = "remote"; IsCurrent = $false }
        }
    }

    if ($allOptions.Count -eq 0) {
        Write-Host "  (nenhum branch encontrado)" -ForegroundColor DarkGray
    }

    $newBranchOption = @{ Name = "devin-new"; Type = "new"; IsCurrent = $false }

    # Seleciona branches no terminal via ConsoleGuiTools
    $selectedBranches = @()
    for ($i = 0; $i -lt $numInstancias; $i++) {
        $pos = $positions[$i]
        $titulo = if ($pos) { "Selecione a branch - Instancia $($labels[$i]) ($pos)" } else { "Selecione a branch - Instancia $($labels[$i])" }

        $selectedNames = @($selectedBranches | ForEach-Object { $_.Name })
        $available = @($allOptions | Where-Object { $_.Name -notin $selectedNames })
        $available += $newBranchOption

        $selected = Select-BranchTerminal -Options $available -MetaMap $branchMeta -PrMap $prMap -ProtectedSet $protectedSet -DefaultBranch $defaultBranch -Title $titulo
        if (-not $selected) {
            Write-Host "Selecao de branch cancelada. Encerrando." -ForegroundColor Yellow
            exit
        }
        $selectedBranches += $selected
        Write-Host "  Instancia $($labels[$i]) -> $($selected.Name)" -ForegroundColor Cyan
    }

    if ($numInstancias -eq 1) {
        $singleInstanceMode = $true
        $originalBranch = git -C $workspacePath branch --show-current 2>$null
        Write-Host "`n[BRANCH] Selecionando branch para a instancia unica..." -ForegroundColor Magenta
        $info = $selectedBranches[0]
        $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        $targetBranch = if ($info.Type -eq 'new') { "devin-$timestamp-a" } else { $info.Name }

        $switchResult = $null
        $createdThisBranch = $null
        if ($info.Type -eq 'new') {
            $switchResult = git -C $workspacePath switch -c $targetBranch 2>&1
            if ($?) { $createdThisBranch = $targetBranch }
        }
        elseif ($info.Type -eq 'remote') {
            $switchResult = git -C $workspacePath switch -c $targetBranch "origin/$targetBranch" 2>&1
        }
        else {
            $switchResult = git -C $workspacePath switch $targetBranch 2>&1
        }

        if ($?) {
            if ($createdThisBranch) { $createdBranches += $createdThisBranch }
            $typeLabel = switch ($info.Type) { "new" { " (nova)" } "remote" { " (remota -> local)" } default { "" } }
            Write-Host "  Branch ativa: $targetBranch$typeLabel" -ForegroundColor Green
        }
        else {
            Write-Host "  Aviso: nao foi possivel trocar para '$targetBranch' (ha alteracoes locais ou conflito). Continuando na branch atual." -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "`n[WORKTREE] Criando worktrees isolados..." -ForegroundColor Magenta

        $worktreesRoot = Join-Path $workspacePath ".worktrees"
        if (-not (Test-Path -LiteralPath $worktreesRoot)) { New-Item -ItemType Directory -LiteralPath $worktreesRoot -Force | Out-Null }

        $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'

        try {
            for ($i = 0; $i -lt $numInstancias; $i++) {
                $worktree = Join-Path $worktreesRoot "instancia-$($labels[$i].ToLower())"

                $null = git -C $workspacePath worktree remove "$worktree" --force 2>&1
                if (Test-Path -LiteralPath $worktree) { Remove-Item -LiteralPath $worktree -Recurse -Force -ErrorAction SilentlyContinue }

                $info = $selectedBranches[$i]
                $branch = $info.Name
                if ($info.Type -eq "new") { $branch = "devin-$timestamp-$($labels[$i].ToLower())" }

                if ($info.Type -eq "new") {
                    $null = git -C $workspacePath worktree add "$worktree" -b $branch 2>&1
                }
                elseif ($info.Type -eq "remote") {
                    $null = git -C $workspacePath worktree add "$worktree" -b $branch "origin/$branch" 2>&1
                }
                else {
                    $null = git -C $workspacePath worktree add "$worktree" $branch 2>&1
                }

                if (-not $?) { throw "git worktree add falhou para '$worktree' (branch '$branch')" }

                $worktrees += $worktree
                $createdWorktrees += $worktree
                $branches += $branch
                if ($info.Type -eq "new") { $createdBranches += $branch }
                $branchInfos += @{ Name = $branch; Type = $info.Type }

                $typeLabel = switch ($info.Type) { "new" { " (nova)" } "remote" { " (remota -> local)" } default { "" } }
                Write-Host "  Instancia $($labels[$i]) -> $worktree" -ForegroundColor DarkCyan
                Write-Host "    Branch: $branch$typeLabel" -ForegroundColor DarkGray
            }

            Write-Host "  Cada instancia edita arquivos isoladamente. Merge manual apos tarefa." -ForegroundColor DarkGray
        }
        catch {
            Write-Host "  Aviso: Falha ao criar worktrees ($($_.Exception.Message)). Removendo o que foi criado e usando mesmo diretorio." -ForegroundColor Yellow
            foreach ($wt in $createdWorktrees) {
                $null = git -C $workspacePath worktree remove "$wt" --force 2>&1
                if (Test-Path -LiteralPath $wt) { Remove-Item -LiteralPath $wt -Recurse -Force -ErrorAction SilentlyContinue }
            }
            foreach ($cb in $createdBranches) {
                $null = git -C $workspacePath branch -D $cb 2>&1
            }
            $worktrees = @()
            $createdWorktrees = @()
            $branches = @()
            $createdBranches = @()
            $branchInfos = @()
            $numInstancias = 1
        }
    }
}

# 3. Calcula posicoes da grade na tela
$grid = @()
if ($numInstancias -eq 1) {
    $grid += [PSCustomObject]@{X = $OffsetX; Y = $OffsetY; W = $W; H = $H }
}
elseif ($numInstancias -eq 2) {
    $grid += [PSCustomObject]@{X = $OffsetX; Y = $OffsetY; W = $W / 2; H = $H }
    $grid += [PSCustomObject]@{X = ($OffsetX + $W / 2); Y = $OffsetY; W = ($W / 2); H = $H }
}
elseif ($numInstancias -eq 3) {
    $grid += [PSCustomObject]@{X = $OffsetX; Y = $OffsetY; W = $W / 2; H = $H }
    $grid += [PSCustomObject]@{X = ($OffsetX + $W / 2); Y = $OffsetY; W = ($W / 2); H = $H / 2 }
    $grid += [PSCustomObject]@{X = ($OffsetX + $W / 2); Y = ($OffsetY + $H / 2); W = ($W / 2); H = $H / 2 }
}
else { # 4
    $grid += [PSCustomObject]@{X = $OffsetX; Y = $OffsetY; W = $W / 2; H = $H / 2 }
    $grid += [PSCustomObject]@{X = ($OffsetX + $W / 2); Y = $OffsetY; W = ($W / 2); H = $H / 2 }
    $grid += [PSCustomObject]@{X = $OffsetX; Y = ($OffsetY + $H / 2); W = $W / 2; H = $H / 2 }
    $grid += [PSCustomObject]@{X = ($OffsetX + $W / 2); Y = ($OffsetY + $H / 2); W = ($W / 2); H = $H / 2 }
}

# 3. Define tamanho/posicao da janela principal
if ($numInstancias -eq 1) {
    $mainRect = $grid[0]
}
elseif ($insideWT) {
    $mainRect = [PSCustomObject]@{X = $OffsetX; Y = $OffsetY; W = $W; H = $H }
}
else {
    $mainRect = $grid[0]
}
if ($windowUtilAvailable) {
    [WindowUtil]::SetWindowPos($hwndMain, [IntPtr]::Zero, [int]$mainRect.X, [int]$mainRect.Y, [int]$mainRect.W, [int]$mainRect.H, 0x0040) | Out-Null
}

$processosAdicionais = @()

# 5. Abre as instancias adicionais
if ($numInstancias -gt 1) {
    $scriptPid = $PID
    $cmd = "Import-Module Microsoft.PowerShell.ConsoleGuiTools -ErrorAction Stop; . '$bundleRoot\devin-session-launcher.ps1'; Start-DevinSession; Write-Host 'Instancia principal ainda ativa - aguardando encerrar...'; while (Get-Process -Id $scriptPid -ErrorAction SilentlyContinue) { Start-Sleep 2 }; exit"

    if ($insideWT) {
        Write-Host "Abrindo paineis divididos (split pane) no Windows Terminal..." -ForegroundColor Cyan

        $subcommands = @()
        if ($numInstancias -eq 2) {
            $subcommands += "split-pane -V -d `"$($worktrees[1])`" $psExecutable -NoExit -Command `"$cmd`""
            $subcommands += "move-focus left"
        }
        elseif ($numInstancias -eq 3) {
            $subcommands += "split-pane -V -d `"$($worktrees[1])`" $psExecutable -NoExit -Command `"$cmd`""
            $subcommands += "split-pane -H -d `"$($worktrees[2])`" $psExecutable -NoExit -Command `"$cmd`""
            $subcommands += "move-focus left"
        }
        elseif ($numInstancias -eq 4) {
            $subcommands += "split-pane -H -d `"$($worktrees[2])`" $psExecutable -NoExit -Command `"$cmd`""
            $subcommands += "move-focus up"
            $subcommands += "split-pane -V -d `"$($worktrees[1])`" $psExecutable -NoExit -Command `"$cmd`""
            $subcommands += "split-pane -H -d `"$($worktrees[3])`" $psExecutable -NoExit -Command `"$cmd`""
            $subcommands += "move-focus left"
            $subcommands += "move-focus up"
        }

        $argsWT = "-w 0 " + ($subcommands -join " ; ")
        Start-Process -FilePath "wt.exe" -ArgumentList $argsWT

        Write-Host "Paineis extras abertos. Ajuste os divisores com Alt+Shift+setas." -ForegroundColor Green
    }
    else {
        Write-Host "Nao esta no Windows Terminal - abrindo janelas separadas (fallback)." -ForegroundColor DarkYellow

        for ($i = 1; $i -lt $numInstancias; $i++) {
            [int[]]$wtBefore = @(Get-Process WindowsTerminal -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)

            $argsWT = "-w new -d `"$($worktrees[$i])`" $psExecutable -NoExit -Command `"$cmd`""
            Start-Process -FilePath "wt.exe" -ArgumentList $argsWT

            $timeout = 0
            $hWndFilho = [IntPtr]::Zero

            Write-Host "Aguardando geracao da janela $($labels[$i])..." -ForegroundColor DarkGray
            while ($timeout -lt 60) {
                Start-Sleep -Milliseconds 200
                $wtAfter = Get-Process WindowsTerminal -ErrorAction SilentlyContinue

                $newWtProc = $wtAfter | Where-Object { $_.Id -notin $wtBefore -and $_.MainWindowHandle -ne 0 } | Select-Object -First 1

                if ($newWtProc -and $newWtProc.MainWindowHandle -ne [IntPtr]::Zero) {
                    $hWndFilho = $newWtProc.MainWindowHandle
                    $processosAdicionais += $newWtProc
                    break
                }
                $timeout++
            }

            if ($hWndFilho -ne [IntPtr]::Zero -and $windowUtilAvailable) {
                [WindowUtil]::SetWindowPos($hWndFilho, [IntPtr]::Zero, [int]$grid[$i].X, [int]$grid[$i].Y, [int]$grid[$i].W, [int]$grid[$i].H, 0x0040) | Out-Null
                Write-Host "Terminal $($labels[$i]) posicionado com sucesso." -ForegroundColor Green
            }
            else {
                Write-Host "Aviso: A nova janela $($labels[$i]) demorou muito para responder e nao foi redimensionada." -ForegroundColor Yellow
            }
        }
    }

    Write-Host "Aguardando 3 segundos para estabilizacao da CPU..." -ForegroundColor DarkGray
    Start-Sleep -Seconds 3
}

Write-Host "Iniciando a instancia principal neste terminal. Feche-a ou encerre-a para continuar o script..." -ForegroundColor Green

# 7. Muda para o worktree A (se houver) e executa o devin
if ($worktrees.Count -gt 0 -and (Test-Path -LiteralPath $worktrees[0])) {
    Set-Location -LiteralPath $worktrees[0]
}

# Sincroniza a branch da instancia principal com o remoto
$targetPath = if ($worktrees.Count -gt 0) { $worktrees[0] } else { $workspacePath }
if ($isGitRepo -and (Test-Path -LiteralPath (Join-Path $targetPath ".git"))) {
    Write-Host "`nSincronizando branch com remoto..." -ForegroundColor Cyan
    $null = git -C $targetPath diff --quiet 2>&1
    $clean = $?
    if ($clean) {
        $null = git -C $targetPath pull --ff-only 2>&1
        if ($?) { Write-Host "  Branch atualizada (fast-forward)." -ForegroundColor Green }
        else { Write-Host "  Nao foi possivel fast-forward (sem upstream ou divergencia)." -ForegroundColor Yellow }
    }
    else {
        Write-Host "  Pull ignorado: ha alteracoes locais." -ForegroundColor Yellow
    }
}

# Decide entre retomar sessao existente ou iniciar nova
Start-DevinSession

# 8. Finaliza as instancias extras (fallback)
if ($processosAdicionais.Count -gt 0) {
    Write-Host "`nInstancia principal encerrada. Finalizando terminais extras..." -ForegroundColor Yellow
    foreach ($p in $processosAdicionais) {
        if (-not $p.HasExited) {
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "Terminais extras fechados com sucesso." -ForegroundColor Green
}
else {
    Write-Host "`nInstancia principal encerrada." -ForegroundColor DarkGray
    Write-Host "Paineis extras (split pane) fecham automaticamente em instantes..." -ForegroundColor DarkGray
}

# 5. Limpa worktrees
if ($createdWorktrees.Count -gt 0 -or $createdBranches.Count -gt 0) {
    Write-Host "`n[WORKTREE] Limpando worktrees..." -ForegroundColor Magenta
    Push-Location -LiteralPath $workspacePath
    foreach ($wt in $createdWorktrees) {
        git worktree remove $wt --force 2>$null
    }
    foreach ($cb in $createdBranches) {
        git branch -D $cb 2>$null
    }
    Pop-Location
    if ($worktreesRoot -and (Test-Path -LiteralPath $worktreesRoot)) { Remove-Item -LiteralPath $worktreesRoot -Recurse -Force -ErrorAction SilentlyContinue }
    Write-Host "  Worktrees removidos. Branches criadas removidas." -ForegroundColor Green
}

# Restaura a branch original no modo 1 instancia
if ($singleInstanceMode -and $originalBranch -and $isGitRepo -and (Test-Path -LiteralPath (Join-Path $workspacePath ".git"))) {
    $null = git -C $workspacePath switch $originalBranch 2>&1
    if ($?) { Write-Host "  Branch original '$originalBranch' restaurada." -ForegroundColor Green }
    else { Write-Host "  Aviso: nao foi possivel restaurar a branch '$originalBranch' (ha alteracoes locais)." -ForegroundColor Yellow }
}

# 8. Restora a janela principal ao tamanho/posicao originais
if ($windowUtilAvailable) {
    [WindowUtil]::SetWindowPos($hwndMain, [IntPtr]::Zero, [int]$origX, [int]$origY, [int]$origW, [int]$origH, 0x0040) | Out-Null
    Write-Host "Terminal restaurado para a posicao e tamanho originais." -ForegroundColor Cyan
}

# 2. Retorna ao diretorio original
Set-Location -LiteralPath $diretorioOriginal
Write-Host "`nRetornando ao diretorio original: $($diretorioOriginal.Path)" -ForegroundColor Gray
