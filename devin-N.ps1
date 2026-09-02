# devin-N.ps1 — Launcher do Devin com as funcoes 2,3,4,5,7,8
# Suporta ate 4 instancias em 1 a 4 projetos; worktrees apenas se 2+ instancias no mesmo projeto.
# O comando `devin` inicia um REPL interativo no diretorio atual.

# Mensagens centralizadas (templates para futura i18n)
$M = @{
    UsandoTerminal = 'Usando terminal base: {0}'
    WtNaoEncontrado = 'wt.exe nao encontrado. Novas instancias abrirao em janelas de PowerShell separadas.'
    SelecioneWorkspace = "`nSelecione os projetos no terminal (ate 4 instancias)..."
    SelecaoCancelada = 'Selecao de {0} cancelada. Encerrando.'
    WorkspaceDefinido = "Workspace definido para: {0}`n"
    NenhumaPastaSelecionada = "Nenhuma pasta selecionada. Mantendo no diretorio atual.`n"
    DimensaoJanela = 'Aviso: Nao foi possivel obter as dimensoes da janela. Redimensionamento desabilitado.'
    NaoGitRepo = 'O projeto nao e um repositorio Git. Apenas 1 instancia e permitida.'
    ConfigurandoInstancias = "`nConfigurando {0} instancia(s) em {1} projeto(s)..."
    WorktreeWorkspaceGit = "`n[WORKTREE] Projeto e um repositorio Git."
    SincronizandoReferencias = 'Sincronizando referencias remotas...'
    ReferenciasAtualizadas = '  Referencias remotas atualizadas.'
    ReferenciasFalha = '  Nao foi possivel atualizar as referencias remotas (sem acesso ou sem remoto configurado).'
    MetadadosBranches = 'Obtendo metadados das branches...'
    ListandoBranches = 'Listando branches existentes...'
    NenhumBranch = '  (nenhum branch encontrado)'
    BranchSelecionando = "`n[BRANCH] Selecionando branch para a instancia {0}..."
    BranchAtiva = '  Branch ativa: {0}{1}'
    BranchTrocarFalha = "  Aviso: nao foi possivel trocar para '{0}' (ha alteracoes locais ou conflito). Continuando na branch atual."
    WorktreeCriando = "`n[WORKTREE] Criando worktrees isolados..."
    WorktreeInstancia = '  Instancia {0} -> {1}'
    WorktreeBranch = '    Branch: {0}{1}'
    WorktreeMerge = '  Cada instancia edita arquivos isoladamente. Merge manual apos tarefa.'
    WorktreeFalha = '  Aviso: Falha ao criar worktrees ({0}). Removendo o que foi criado e usando mesmo diretorio.'
    PaineisDivididos = 'Abrindo paineis divididos (split pane) no Windows Terminal...'
    PaineisAbertos = 'Paineis extras abertos. Ajuste os divisores com Alt+Shift+setas.'
    JanelasSeparadas = 'Nao esta no Windows Terminal - abrindo janelas separadas (fallback).'
    WtNaoEncontradoJanelas = 'wt.exe nao encontrado - abrindo janelas de PowerShell separadas.'
    JanelaGeracao = 'Aguardando geracao da janela {0}...'
    JanelaPosicionada = 'Terminal {0} posicionado com sucesso.'
    JanelaTimeout = 'Aviso: A nova janela {0} demorou muito para responder e nao foi redimensionada.'
    EstabilizacaoCpu = 'Aguardando 3 segundos para estabilizacao da CPU...'
    IniciandoPrincipal = 'Iniciando a instancia principal neste terminal. Feche-a ou encerre-a para continuar o script...'
    SincronizandoBranch = "`nSincronizando branch com remoto..."
    BranchAtualizada = '  Branch atualizada (fast-forward).'
    FastForwardFalha = '  Nao foi possivel fast-forward (sem upstream ou divergencia).'
    PullIgnorado = '  Pull ignorado: ha alteracoes locais.'
    PrincipalEncerradaTerminais = "`nInstancia principal encerrada. Finalizando terminais extras..."
    TerminaisFechados = 'Terminais extras fechados com sucesso.'
    PrincipalEncerrada = "`nInstancia principal encerrada."
    PaineisFecham = 'Paineis extras (split pane) fecham automaticamente em instantes...'
    LimpandoWorktrees = "`n[WORKTREE] Limpando worktrees..."
    WorktreesRemovidos = '  Worktrees removidos. Branches criadas removidas.'
    BranchOriginalRestaurada = "  Branch original '{0}' restaurada."
    BranchOriginalFalha = "  Aviso: nao foi possivel restaurar a branch '{0}' (ha alteracoes locais)."
    TerminalRestaurado = 'Terminal restaurado para a posicao e tamanho originais.'
    RetornandoDiretorio = "`nRetornando ao diretorio original: {0}"
    ProjetoJaSelecionado = 'Projeto ja selecionado. Escolha outro ou cancele.'
    TotalInstancias = 'Total de instancias: {0}'
    AdicionarProjeto = 'Adicionar outro projeto?'
    QuantasInstancias = 'Quantas instancias em `{0}`?'
    BranchBaseSelecione = "`n[BRANCH] Selecione a branch base para a nova branch no projeto '{0}'..."
    BranchJaEscolhida = ' (ja escolhida neste projeto)'
    AvisoBranchIgual = 'Aviso: a branch `{0}` ja foi escolhida para outra instancia deste projeto. Escolha outra.'
    BranchNomePersonalizado = 'Digite o nome da nova branch (Enter para `{0}`):'
    BranchNomeInvalido = 'Nome de branch invalido. Tente outro.'
    BranchNomeExiste = 'A branch `{0}` ja existe neste projeto. Escolha outro nome.'
    BranchNomeReservado = 'O nome `{0}` esta reservado para outra instancia deste projeto. Escolha outro.'
}

# 2. Salva o diretorio atual
$diretorioOriginal = Get-Location
$bundleRoot = $PSScriptRoot

# 3. Prefere PowerShell 7 para subprocessos
$psExecutable = "powershell.exe"
if (Get-Command pwsh -ErrorAction SilentlyContinue) {
    $psExecutable = "pwsh.exe"
}
Write-Host ($M.UsandoTerminal -f $psExecutable) -ForegroundColor DarkGray

# Localiza o Windows Terminal (wt.exe) para abrir paineis/janelas extras
$wtCmd = Get-Command wt -ErrorAction SilentlyContinue
$wtPath = if ($wtCmd) { $wtCmd.Source } else { $null }
if (-not $wtPath) { Write-Host $M.WtNaoEncontrado -ForegroundColor DarkYellow }

# 4. Carrega utilitarios e menu full-terminal
Add-Type -AssemblyName System.Windows.Forms
. (Join-Path $bundleRoot "devin-session-launcher.ps1")

function Select-FolderTerminal {
    param(
        [string]$InitialPath,
        [switch]$AllowCancel
    )

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

        $selected = Show-TerminalList -Items $items -Title "Selecione o workspace ($current)" -ToString { param($x) $x.Name }
        if (-not $selected) {
            if ($AllowCancel) { return $null }
            return $current
        }

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
            $driveSelected = Show-TerminalList -Items $drives -Title "Selecione o drive" -ToString { param($x) $x.Name }
            if ($driveSelected) { $current = $driveSelected.Caminho }
            continue
        }
        $current = $selected.Caminho
    }
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
            $json = gh pr list --state all --json number,headRefName,state,isDraft,reviewDecision,statusCheckRollup,author,updatedAt,createdAt,mergedAt --limit 200 2>&1 | Where-Object { $_ -is [string] } | Out-String
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
            $nameWithOwner = (gh repo view --json nameWithOwner -q .nameWithOwner 2>&1 | Where-Object { $_ -is [string] } | Out-String).Trim()
            if ($? -and $nameWithOwner -and $nameWithOwner -notmatch 'error|fatal') {
                $names = gh api "repos/$nameWithOwner/branches?per_page=100" --paginate --jq '.[] | select(.protected == true) | .name' 2>&1 | Where-Object { $_ -is [string] }
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
                $output = (gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>&1 | Where-Object { $_ -is [string] } | Out-String).Trim()
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
                $ref = git rev-parse --abbrev-ref refs/remotes/origin/HEAD 2>&1 | Where-Object { $_ -is [string] } | Select-Object -First 1
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
                $info = git remote show origin 2>&1 | Where-Object { $_ -is [string] }
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

    $branchType = $BranchOption.Type
    $currentMark = if ($BranchOption.IsCurrent) { '*' } else { '' }

    $syncToken = ''
    $meta = $MetaMap[$BranchName]
    if ($meta) {
        if (-not $meta.HasUpstream -and -not $meta.ExistsOnRemote) {
            $syncToken = 'sem remoto'
        }
        elseif ($meta.Ahead -gt 0 -and $meta.Behind -gt 0) {
            $syncToken = "+$($meta.Ahead)/-$($meta.Behind)"
        }
        elseif ($meta.Ahead -gt 0) {
            $syncToken = "+$($meta.Ahead)"
        }
        elseif ($meta.Behind -gt 0) {
            $syncToken = "-$($meta.Behind)"
        }
    }

    $prNumber = '-'
    $prState = '-'
    $author = 'n/a'
    $review = 'n/a'
    $ci = 'n/a'
    $activity = 'n/a'

    $pr = $PrMap[$BranchName]
    if ($pr) {
        $prNumber = "$($pr.number)"
        $state = $pr.state
        if ($pr.mergedAt) { $state = 'MERGED' }
        elseif ($state -eq 'OPEN') { $state = if ($pr.isDraft) { 'DRAFT' } else { 'OPEN' } }
        elseif ($state -eq 'CLOSED') { $state = 'CLOSED' }
        else { $state = $state.ToString().ToUpper() }
        $prState = $state

        if (-not $Short) {
            $author = $pr.author?.login ?? 'n/a'
            $review = if ($pr.reviewDecision) { $pr.reviewDecision.ToString().ToLower().Replace('_', ' ') } else { 'n/a' }

            $ci = 'n/a'
            if ($pr.statusCheckRollup) {
                $rollups = @($pr.statusCheckRollup)
                if ($rollups.Count -gt 0) {
                    $anyPending = $rollups | Where-Object {
                        $s = $_.PSObject.Properties['status']?.Value
                        $st = $_.PSObject.Properties['state']?.Value
                        ($s -and $s -ne 'COMPLETED') -or ($st -and $st -eq 'PENDING')
                    }
                    if ($anyPending) {
                        $ci = 'PENDING'
                    }
                    else {
                        $failures = $rollups | Where-Object {
                            $c = $_.PSObject.Properties['conclusion']?.Value
                            $st = $_.PSObject.Properties['state']?.Value
                            ($c -and $c -notin @('SUCCESS','NEUTRAL','SKIPPED','null')) -or
                            ($st -and $st -notin @('SUCCESS','NEUTRAL','SKIPPED','null'))
                        }
                        if ($failures) { $ci = 'FAILURE' }
                        else { $ci = 'SUCCESS' }
                    }
                }
            }
        }

        $dateValue = $pr.updatedAt
        if ($dateValue) {
            try {
                $dt = if ($dateValue -is [datetime]) { $dateValue } else { [datetime]::Parse($dateValue, [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::RoundtripKind) }
                $days = [int]((Get-Date) - $dt).TotalDays
                if ($days -gt 30) { $activity = "stale ${days}d" }
                else { $activity = "ativo ${days}d" }
            }
            catch { Write-Verbose "Falha ao calcular atividade/stale para '$BranchName': $_" }
        }
    }

    if ($activity -eq 'n/a' -and $meta -and $meta.LastCommit) {
        try {
            $dt = if ($meta.LastCommit -is [datetime]) { $meta.LastCommit } else { [datetime]::Parse($meta.LastCommit, [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::RoundtripKind) }
            $days = [int]((Get-Date) - $dt).TotalDays
            if ($days -gt 30) { $activity = "stale ${days}d" }
            else { $activity = "ativo ${days}d" }
        }
        catch { Write-Verbose "Falha ao calcular atividade/stale para '$BranchName': $_" }
    }

    $flagList = @()
    if ($BranchName -eq $DefaultBranch) { $flagList += 'default' }
    if ($ProtectedSet[$BranchName]) { $flagList += 'protegida' }
    $flags = $flagList -join ' | '

    if ($Short) {
        return [PSCustomObject]@{
            Type = $branchType
            Name = $BranchName
            CurrentMark = $currentMark
            Sync = $syncToken
            PrNumber = $prNumber
            PrState = $prState
            Author = $author
            Review = $review
            Ci = $ci
            Activity = $activity
            Flags = $flags
        }
    }

    return [PSCustomObject]@{
        Type = $branchType
        Name = $BranchName
        CurrentMark = $currentMark
        Sync = $syncToken
        PrNumber = $prNumber
        PrState = $prState
        Author = $author
        Review = $review
        Ci = $ci
        Activity = $activity
        Flags = $flags
    }
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
        [string]$Title
    )

    $rows = foreach ($opt in $Options) {
        Format-BranchStatus -BranchName $opt.Name -BranchOption $opt -MetaMap $MetaMap -PrMap $PrMap -ProtectedSet $ProtectedSet -DefaultBranch $DefaultBranch
    }

    $wType  = [Math]::Max(4, ($rows | ForEach-Object { $_.Type.Length }  | Measure-Object -Maximum).Maximum)
    $wName  = [Math]::Max(5, ($rows | ForEach-Object { $_.Name.Length }  | Measure-Object -Maximum).Maximum)
    $wCur   = [Math]::Max(1, ($rows | ForEach-Object { $_.CurrentMark.Length } | Measure-Object -Maximum).Maximum)
    $wSync  = [Math]::Max(4, ($rows | ForEach-Object { $_.Sync.Length }    | Measure-Object -Maximum).Maximum)
    $wPr    = [Math]::Max(3, ($rows | ForEach-Object { $_.PrNumber.Length } | Measure-Object -Maximum).Maximum)
    $wState = [Math]::Max(5, ($rows | ForEach-Object { $_.PrState.Length }  | Measure-Object -Maximum).Maximum)
    $wAuth  = [Math]::Max(6, ($rows | ForEach-Object { $_.Author.Length }   | Measure-Object -Maximum).Maximum)
    $wRev   = [Math]::Max(6, ($rows | ForEach-Object { $_.Review.Length }   | Measure-Object -Maximum).Maximum)
    $wCi    = [Math]::Max(2, ($rows | ForEach-Object { $_.Ci.Length }       | Measure-Object -Maximum).Maximum)
    $wAct   = [Math]::Max(3, ($rows | ForEach-Object { $_.Activity.Length } | Measure-Object -Maximum).Maximum)

    $wNameEx = $wName + $wCur + 1
    $selected = Show-TerminalList -Items $rows -Title $Title -ToString {
        param($x)
        $displayName = $x.Name
        if ($x.CurrentMark) { $displayName += " $($x.CurrentMark)" }
        $line = "[$($x.Type.PadRight($wType))] $($displayName.PadRight($wNameEx)) "
        $line += "$($x.Sync.PadRight($wSync)) | "
        $line += "#$($x.PrNumber.PadRight($wPr)) $($x.PrState.PadRight($wState)) "
        $line += "autor:$($x.Author.PadRight($wAuth)) "
        $line += "rev:$($x.Review.PadRight($wRev)) "
        $line += "CI:$($x.Ci.PadRight($wCi)) "
        $line += "$($x.Activity.PadRight($wAct))"
        if ($x.Flags) { $line += " [$($x.Flags)]" }
        $w = [Console]::WindowWidth
        if ($w -le 0) { $w = 120 }
        if ($line.Length -gt $w - 1) {
            $line = $line.Substring(0, [Math]::Min($line.Length, $w - 1))
        }
        $line
    }
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
    Write-Host $M.DimensaoJanela -ForegroundColor Yellow
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

# 4. Escolhe projetos e quantidade de instancias
$labels = @('A','B','C','D')
$projetos = @()
$instancias = @()
$totalInstancias = 0

Write-Host $M.SelecioneWorkspace -ForegroundColor Cyan

while ($totalInstancias -lt 4) {
    $vagas = 4 - $totalInstancias
    $title = if ($projetos.Count -eq 0) {
        "Selecione o projeto 1 ($vagas vagas)"
    } else {
        "Selecione outro projeto ou cancele ($vagas vagas)"
    }
    $initial = if ($projetos.Count -gt 0) { $projetos[-1].Path } else { $diretorioOriginal.Path }

    $projectPath = Select-FolderTerminal -InitialPath $initial -AllowCancel
    if (-not $projectPath) { break }

    $already = $projetos | Where-Object { $_.Path -eq $projectPath } | Select-Object -First 1
    if ($already) {
        Write-Host $M.ProjetoJaSelecionado -ForegroundColor Yellow
        continue
    }

    $isGitRepo = Test-Path -LiteralPath (Join-Path $projectPath ".git")
    $maxForProject = if ($isGitRepo) { $vagas } else { 1 }

    if (-not $isGitRepo) {
        Write-Host ($M.NaoGitRepo -f $projectPath) -ForegroundColor DarkYellow
    }

    $opcoesQuantidade = @()
    for ($i = 1; $i -le $maxForProject; $i++) {
        $opcoesQuantidade += [PSCustomObject]@{ Numero = $i; Label = "$i instancia(s)" }
    }

    $escolhaQuantidade = Show-TerminalList -Items $opcoesQuantidade -Title ($M.QuantasInstancias -f $projectPath) -ToString { param($x) $x.Label } -DefaultIndex 0
    $projectCount = if ($escolhaQuantidade) { $escolhaQuantidade.Numero } else { 1 }

    $projetos += [PSCustomObject]@{
        Path = $projectPath
        Count = $projectCount
        IsGitRepo = $isGitRepo
        WorktreesRoot = $null
        CreatedWorktrees = @()
        CreatedBranches = @()
        OriginalBranch = $null
        CurrentBranch = $null
    }

    $totalInstancias += $projectCount
    Write-Host ($M.TotalInstancias -f $totalInstancias) -ForegroundColor DarkGray

    if ($totalInstancias -ge 4) { break }

    $simNao = @(
        [PSCustomObject]@{ Resposta = $true; Label = 'Sim, adicionar outro projeto' },
        [PSCustomObject]@{ Resposta = $false; Label = 'Nao, concluir selecao' }
    )
    $continuar = Show-TerminalList -Items $simNao -Title ($M.AdicionarProjeto + " (total: $totalInstancias)") -ToString { param($x) $x.Label } -DefaultIndex 1
    if (-not $continuar -or -not $continuar.Resposta) { break }
}

if ($projetos.Count -eq 0) {
    Write-Host ($M.SelecaoCancelada -f 'projetos') -ForegroundColor Yellow
    exit
}

Write-Host ($M.ConfigurandoInstancias -f $totalInstancias, $projetos.Count) -ForegroundColor Cyan

# 5. Prepara instancias e worktrees
$positions = switch ($totalInstancias) {
    2 { @('esquerda','direita','','') }
    3 { @('esquerda','superior-direita','inferior-direita','') }
    4 { @('superior-esquerda','superior-direita','inferior-esquerda','inferior-direita') }
    default { @('','','','') }
}

$labelIdx = 0

foreach ($proj in $projetos) {
    $projectPath = $proj.Path
    $count = $proj.Count

    if ($proj.IsGitRepo) {
        Write-Host $M.WorktreeWorkspaceGit -ForegroundColor Magenta

        Remove-StaleWorktrees -RepoPath $projectPath

        Write-Host $M.SincronizandoReferencias -ForegroundColor DarkGray
        $null = git -C $projectPath fetch --all --prune 2>&1
        if ($?) {
            Write-Host $M.ReferenciasAtualizadas -ForegroundColor Green
        }
        else {
            Write-Host $M.ReferenciasFalha -ForegroundColor Yellow
        }

        Write-Host $M.MetadadosBranches -ForegroundColor DarkGray
        $branchMeta = Get-BranchMetadata -RepoPath $projectPath
        $prMap = Get-PullRequestMap -RepoPath $projectPath
        $protectedSet = Get-ProtectedBranchSet -RepoPath $projectPath
        $defaultBranch = Get-DefaultBranchName -RepoPath $projectPath

        Write-Host $M.ListandoBranches -ForegroundColor DarkGray

        $localBranches = @()
        $localBranches += @((git -C $projectPath branch --format='%(refname:short)' 2>$null) | Where-Object {
            $_ -ne "" -and $_ -notmatch "^(main|master|develop|HEAD)$"
        })

        $remoteBranches = @()
        $remoteBranches += @((git -C $projectPath branch -r --format='%(refname:short)' 2>$null) | Where-Object {
            $_ -ne "" -and $_ -notmatch "HEAD" -and $_ -notmatch "(main|master|develop)$" -and $_ -ne "origin"
        } | ForEach-Object {
            $clean = $_ -replace '^origin/', ''
            if ($clean -and $clean -ne 'HEAD') { $clean }
        })

        $remoteOnly = @($remoteBranches | Where-Object { $_ -notin $localBranches })
        $currentBranch = git -C $projectPath branch --show-current 2>$null

        $allOptions = @()
        if ($defaultBranch) {
            $localDefault = [bool](git -C $projectPath rev-parse --verify --quiet $defaultBranch 2>$null)
            $remoteDefault = [bool](git -C $projectPath rev-parse --verify --quiet "origin/$defaultBranch" 2>$null)
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
            Write-Host $M.NenhumBranch -ForegroundColor DarkGray
        }

        $newBranchOption = @{ Name = "devin-new"; Type = "new"; IsCurrent = $false }

        $selectedBranches = @()
        $selectedBranchNames = @()
        $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'

        for ($i = 0; $i -lt $count; $i++) {
            $pos = $positions[$labelIdx]
            $titulo = if ($pos) { "Selecione a branch - Instancia $($labels[$labelIdx]) ($pos)" } else { "Selecione a branch - Instancia $($labels[$labelIdx])" }

            $selectedNames = @($selectedBranches | ForEach-Object { $_.Name })
            $available = @($allOptions | Where-Object { $_.Name -notin $selectedNames })
            $available += $newBranchOption

            $selected = $null
            while (-not $selected) {
                $selected = Select-BranchTerminal -Options $available -MetaMap $branchMeta -PrMap $prMap -ProtectedSet $protectedSet -DefaultBranch $defaultBranch -Title $titulo
                if (-not $selected) { $selected = $newBranchOption }

                if ($selected.Name -ne 'devin-new' -and $selected.Name -in $selectedNames) {
                    Write-Host ($M.AvisoBranchIgual -f $selected.Name) -ForegroundColor Red
                    $selected = $null
                }
            }

            $selectedBranches += $selected

            $branch = $selected.Name
            $baseBranch = $null
            if ($selected.Type -eq 'new') {
                if ($allOptions.Count -gt 0) {
                    $baseOptions = $allOptions + @{ Name = $currentBranch; Type = 'local'; IsCurrent = $true }
                    $baseOptions = $baseOptions | Sort-Object Name -Unique
                    $baseSelected = Select-BranchTerminal -Options $baseOptions -MetaMap $branchMeta -PrMap $prMap -ProtectedSet $protectedSet -DefaultBranch $defaultBranch -Title ($M.BranchBaseSelecione -f $projectPath)
                    if (-not $baseSelected) { $baseSelected = @{ Name = $currentBranch; Type = 'local'; IsCurrent = $true } }
                    $baseBranch = $baseSelected.Name
                }
                else {
                    $baseBranch = $currentBranch
                }

                $defaultBranchName = "devin-$timestamp-$($labels[$labelIdx].ToLower())"
                $initialProjectLabelIdx = $labelIdx - $i
                $reservedAutoNames = @()
                for ($k = 0; $k -lt $count; $k++) {
                    $reservedAutoNames += "devin-$timestamp-$($labels[$initialProjectLabelIdx + $k].ToLower())"
                }

                while ($true) {
                    $customName = Read-Host ($M.BranchNomePersonalizado -f $defaultBranchName)
                    if ([string]::IsNullOrWhiteSpace($customName)) { $customName = $defaultBranchName }
                    $customName = $customName.Trim()

                    $null = git -C $projectPath check-ref-format --branch $customName 2>&1
                    $gitValid = $?

                    $localExists = [bool](git -C $projectPath rev-parse --verify --quiet $customName 2>$null)
                    $remoteExists = [bool](git -C $projectPath rev-parse --verify --quiet "origin/$customName" 2>$null)
                    $alreadySelected = $customName -in $selectedBranchNames
                    $reservedAuto = $customName -ne $defaultBranchName -and $customName -in $reservedAutoNames

                    if (-not $gitValid) {
                        Write-Host $M.BranchNomeInvalido -ForegroundColor Red
                    }
                    elseif ($localExists -or $remoteExists -or $alreadySelected) {
                        Write-Host ($M.BranchNomeExiste -f $customName) -ForegroundColor Red
                    }
                    elseif ($reservedAuto) {
                        Write-Host ($M.BranchNomeReservado -f $customName) -ForegroundColor Red
                    }
                    else {
                        $branch = $customName
                        break
                    }
                }
            }

            $selectedBranchNames += $branch

            $instancias += [PSCustomObject]@{
                Label = $labels[$labelIdx]
                Project = $proj
                ProjectPath = $projectPath
                BranchInfo = $selected
                Branch = $branch
                BaseBranch = $baseBranch
                WorktreePath = $null
                Position = $pos
                IsMain = ($labelIdx -eq 0)
            }

            $labelIdx++
        }

        $proj.OriginalBranch = $currentBranch
        $proj.CurrentBranch = $currentBranch
    }
    else {
        # Nao-Git: apenas 1 instancia, sem branch
        $instancias += [PSCustomObject]@{
            Label = $labels[$labelIdx]
            Project = $proj
            ProjectPath = $projectPath
            BranchInfo = $null
            Branch = $null
            BaseBranch = $null
            WorktreePath = $null
            Position = $positions[$labelIdx]
            IsMain = ($labelIdx -eq 0)
        }
        $labelIdx++
    }
}

# Cria worktrees por projeto conforme necessario
$numInstancias = $totalInstancias
$singleInstanceMode = ($numInstancias -eq 1 -and $projetos[0].IsGitRepo)

foreach ($proj in $projetos | Where-Object { $_.IsGitRepo -and $_.Count -gt 1 }) {
    Write-Host $M.WorktreeCriando -ForegroundColor Magenta
    $projectPath = $proj.Path
    $worktreesRoot = Join-Path $projectPath ".worktrees"
    if (-not (Test-Path -LiteralPath $worktreesRoot)) { New-Item -ItemType Directory -LiteralPath $worktreesRoot -Force | Out-Null }
    $proj.WorktreesRoot = $worktreesRoot

    try {
        $projInstances = @($instancias | Where-Object { $_.Project -eq $proj })
        foreach ($inst in $projInstances) {
            $worktree = Join-Path $worktreesRoot "instancia-$($inst.Label.ToLower())"

            $null = git -C $projectPath worktree remove "$worktree" --force 2>&1
            if (Test-Path -LiteralPath $worktree) { Remove-Item -LiteralPath $worktree -Recurse -Force -ErrorAction SilentlyContinue }

            $info = $inst.BranchInfo
            $branch = $inst.Branch

            if ($info.Type -eq "new") {
                $base = if ($inst.BaseBranch) { $inst.BaseBranch } else { $proj.CurrentBranch }
                $null = git -C $projectPath worktree add "$worktree" -b $branch $base 2>&1
            }
            elseif ($info.Type -eq "remote") {
                $null = git -C $projectPath worktree add "$worktree" -b $branch "origin/$branch" 2>&1
            }
            else {
                $null = git -C $projectPath worktree add "$worktree" $branch 2>&1
            }

            if (-not $?) { throw "git worktree add falhou para '$worktree' (branch '$branch')" }

            $inst.WorktreePath = $worktree
            $proj.CreatedWorktrees += $worktree
            if ($info.Type -eq "new") {
                $proj.CreatedBranches += $branch
            }

            $typeLabel = switch ($info.Type) { "new" { " (nova)" } "remote" { " (remota -> local)" } default { "" } }
            Write-Host ($M.WorktreeInstancia -f $inst.Label, $worktree) -ForegroundColor DarkCyan
            Write-Host ($M.WorktreeBranch -f $branch, $typeLabel) -ForegroundColor DarkGray
        }

        Write-Host $M.WorktreeMerge -ForegroundColor DarkGray
    }
    catch {
        Write-Host ($M.WorktreeFalha -f $_.Exception.Message) -ForegroundColor Yellow
        foreach ($wt in $proj.CreatedWorktrees) {
            $null = git -C $projectPath worktree remove "$wt" --force 2>&1
            if (Test-Path -LiteralPath $wt) { Remove-Item -LiteralPath $wt -Recurse -Force -ErrorAction SilentlyContinue }
        }
        foreach ($cb in $proj.CreatedBranches) {
            $null = git -C $projectPath branch -D $cb 2>&1
        }
        $proj.CreatedWorktrees = @()
        $proj.CreatedBranches = @()
        throw "Falha ao preparar instancias do projeto '$projectPath'. Encerrando."
    }
}

# Preenche WorkingDirectory para cada instancia
foreach ($inst in $instancias) {
    if ($inst.WorktreePath -and (Test-Path -LiteralPath $inst.WorktreePath)) {
        $inst | Add-Member -NotePropertyName WorkingDirectory -NotePropertyValue $inst.WorktreePath -Force
    }
    else {
        $inst | Add-Member -NotePropertyName WorkingDirectory -NotePropertyValue $inst.ProjectPath -Force
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

function Get-InstanceCommand {
    param([PSCustomObject]$Inst)
    $workingDir = $Inst.WorkingDirectory
    $branch = $Inst.Branch
    $baseBranch = $Inst.BaseBranch
    $isGitRepo = $Inst.Project.IsGitRepo
    $branchInfo = $Inst.BranchInfo
    $bundlePath = $bundleRoot.Replace("'", "''")

    $preCommands = @()
    $preCommands += "Set-Location -LiteralPath '$workingDir'"

    if ($isGitRepo -and $branch) {
        if ($branchInfo.Type -eq 'new') {
            $base = if ($baseBranch) { $baseBranch } else { $Inst.Project.CurrentBranch }
            $preCommands += "git -C '$workingDir' switch -c '$branch' '$base' 2>`$null"
        }
        elseif (-not $Inst.WorktreePath) {
            $preCommands += "git -C '$workingDir' switch '$branch' 2>`$null"
        }
    }

    $preCommands += ". '$bundlePath\devin-session-launcher.ps1'; Start-DevinSession; Write-Host 'Instancia principal ainda ativa - aguardando encerrar...'; while (Get-Process -Id $scriptPid -ErrorAction SilentlyContinue) { Start-Sleep 2 }; exit"
    return ($preCommands -join "; ")
}

# 5. Abre as instancias adicionais
if ($numInstancias -gt 1) {
    $scriptPid = $PID

    if ($insideWT -and $wtPath) {
        Write-Host $M.PaineisDivididos -ForegroundColor Cyan

        $subcommands = @()
        if ($numInstancias -eq 2) {
            $subcommands += "split-pane -V -d `"$($instancias[1].WorkingDirectory)`" $psExecutable -NoExit -Command `"$(Get-InstanceCommand -Inst $instancias[1])`""
            $subcommands += "move-focus left"
        }
        elseif ($numInstancias -eq 3) {
            $subcommands += "split-pane -V -d `"$($instancias[1].WorkingDirectory)`" $psExecutable -NoExit -Command `"$(Get-InstanceCommand -Inst $instancias[1])`""
            $subcommands += "split-pane -H -d `"$($instancias[2].WorkingDirectory)`" $psExecutable -NoExit -Command `"$(Get-InstanceCommand -Inst $instancias[2])`""
            $subcommands += "move-focus left"
        }
        elseif ($numInstancias -eq 4) {
            $subcommands += "split-pane -H -d `"$($instancias[2].WorkingDirectory)`" $psExecutable -NoExit -Command `"$(Get-InstanceCommand -Inst $instancias[2])`""
            $subcommands += "move-focus up"
            $subcommands += "split-pane -V -d `"$($instancias[1].WorkingDirectory)`" $psExecutable -NoExit -Command `"$(Get-InstanceCommand -Inst $instancias[1])`""
            $subcommands += "split-pane -H -d `"$($instancias[3].WorkingDirectory)`" $psExecutable -NoExit -Command `"$(Get-InstanceCommand -Inst $instancias[3])`""
            $subcommands += "move-focus left"
            $subcommands += "move-focus up"
        }

        $argsWT = "-w 0 " + ($subcommands -join " ; ")
        $proc = Start-Process -FilePath $wtPath -ArgumentList $argsWT -PassThru
        if (-not $proc) { Write-Warning "Nao foi possivel iniciar wt.exe para os paineis extras." }

        Write-Host $M.PaineisAbertos -ForegroundColor Green
    }
    elseif ($wtPath) {
        Write-Host $M.JanelasSeparadas -ForegroundColor DarkYellow

        for ($i = 1; $i -lt $numInstancias; $i++) {
            [int[]]$wtBefore = @(Get-Process WindowsTerminal -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)

            $inst = $instancias[$i]
            $cmd = Get-InstanceCommand -Inst $inst

            $argsWT = "-w new -d `"$($inst.WorkingDirectory)`" $psExecutable -NoExit -Command `"$cmd`""
            $proc = Start-Process -FilePath $wtPath -ArgumentList $argsWT -PassThru
            if (-not $proc) { Write-Warning "Nao foi possivel abrir a janela $($inst.Label) via wt.exe."; continue }

            $timeout = 0
            $hWndFilho = [IntPtr]::Zero

            Write-Host ($M.JanelaGeracao -f $inst.Label) -ForegroundColor DarkGray
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
                Write-Host ($M.JanelaPosicionada -f $inst.Label) -ForegroundColor Green
            }
            else {
                Write-Host ($M.JanelaTimeout -f $inst.Label) -ForegroundColor Yellow
            }
        }
    }
    else {
        Write-Host $M.WtNaoEncontradoJanelas -ForegroundColor DarkYellow

        for ($i = 1; $i -lt $numInstancias; $i++) {
            $inst = $instancias[$i]
            $cmd = Get-InstanceCommand -Inst $inst

            $proc = Start-Process -FilePath $psExecutable -ArgumentList "-NoExit -Command `"$cmd`"" -PassThru
            if (-not $proc) { Write-Warning "Nao foi possivel abrir a janela $($inst.Label)." }
            else { $processosAdicionais += $proc }
        }
    }

    Write-Host $M.EstabilizacaoCpu -ForegroundColor DarkGray
    Start-Sleep -Seconds 3
}

Write-Host $M.IniciandoPrincipal -ForegroundColor Green

# 7. Muda para o worktree/projeto da instancia principal e executa o devin
$mainInst = $instancias[0]
$mainPath = $mainInst.WorkingDirectory
if (Test-Path -LiteralPath $mainPath) {
    Set-Location -LiteralPath $mainPath
}

if ($mainInst.Project.IsGitRepo -and (Test-Path -LiteralPath (Join-Path $mainPath ".git"))) {
    $targetBranch = $mainInst.Branch
    if ($targetBranch) {
        if ($mainInst.BranchInfo.Type -eq 'new') {
            $base = if ($mainInst.BaseBranch) { $mainInst.BaseBranch } else { $mainInst.Project.CurrentBranch }
            $null = git -C $mainPath switch -c $targetBranch $base 2>&1
            if ($?) {
                Write-Host ($M.BranchAtiva -f $targetBranch, " (nova)") -ForegroundColor Green
            }
            else {
                Write-Host ($M.BranchTrocarFalha -f $targetBranch) -ForegroundColor Yellow
            }
        }
        elseif (-not $mainInst.WorktreePath) {
            $switchResult = git -C $mainPath switch $targetBranch 2>&1
            if ($?) {
                Write-Host ($M.BranchAtiva -f $targetBranch, "") -ForegroundColor Green
            }
            else {
                Write-Host ($M.BranchTrocarFalha -f $targetBranch) -ForegroundColor Yellow
            }
        }
    }

    # Sincroniza a branch da instancia principal com o remoto
    if ($mainInst.BranchInfo -and $mainInst.BranchInfo.Type -ne 'new') {
        Write-Host $M.SincronizandoBranch -ForegroundColor Cyan
        $null = git -C $mainPath diff --quiet 2>&1
        $clean = $?
        if ($clean) {
            $null = git -C $mainPath pull --ff-only 2>&1
            if ($?) { Write-Host $M.BranchAtualizada -ForegroundColor Green }
            else { Write-Host $M.FastForwardFalha -ForegroundColor Yellow }
        }
        else {
            Write-Host $M.PullIgnorado -ForegroundColor Yellow
        }
    }
}

# Decide entre retomar sessao existente ou iniciar nova
Start-DevinSession

# 8. Finaliza as instancias extras (fallback)
if ($processosAdicionais.Count -gt 0) {
    Write-Host $M.PrincipalEncerradaTerminais -ForegroundColor Yellow
    foreach ($p in $processosAdicionais) {
        if (-not $p.HasExited) {
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host $M.TerminaisFechados -ForegroundColor Green
}
else {
    Write-Host $M.PrincipalEncerrada -ForegroundColor DarkGray
    Write-Host $M.PaineisFecham -ForegroundColor DarkGray
}

# 5. Limpa worktrees por projeto
foreach ($proj in $projetos | Where-Object { $_.CreatedWorktrees.Count -gt 0 -or $_.CreatedBranches.Count -gt 0 }) {
    Write-Host ($M.LimpandoWorktrees + " (" + $proj.Path + ")") -ForegroundColor Magenta
    Push-Location -LiteralPath $proj.Path
    foreach ($wt in $proj.CreatedWorktrees) {
        git worktree remove $wt --force 2>$null
    }
    foreach ($cb in $proj.CreatedBranches) {
        git branch -D $cb 2>$null
    }
    Pop-Location
    if ($proj.WorktreesRoot -and (Test-Path -LiteralPath $proj.WorktreesRoot)) { Remove-Item -LiteralPath $proj.WorktreesRoot -Recurse -Force -ErrorAction SilentlyContinue }
    Write-Host $M.WorktreesRemovidos -ForegroundColor Green
}

# Restaura a branch original no modo 1 instancia
$mainProj = $mainInst.Project
if ($singleInstanceMode -and $mainProj.OriginalBranch -and $mainProj.IsGitRepo -and (Test-Path -LiteralPath (Join-Path $mainProj.Path ".git"))) {
    $null = git -C $mainProj.Path switch $mainProj.OriginalBranch 2>&1
    if ($?) { Write-Host ($M.BranchOriginalRestaurada -f $mainProj.OriginalBranch) -ForegroundColor Green }
    else { Write-Host ($M.BranchOriginalFalha -f $mainProj.OriginalBranch) -ForegroundColor Yellow }
}

# 8. Restora a janela principal ao tamanho/posicao originais
if ($windowUtilAvailable) {
    [WindowUtil]::SetWindowPos($hwndMain, [IntPtr]::Zero, [int]$origX, [int]$origY, [int]$origW, [int]$origH, 0x0040) | Out-Null
    Write-Host $M.TerminalRestaurado -ForegroundColor Cyan
}

# 2. Retorna ao diretorio original
Set-Location -LiteralPath $diretorioOriginal
Write-Host ($M.RetornandoDiretorio -f $diretorioOriginal.Path) -ForegroundColor Gray
