# devin-N.ps1 — Launcher do Devin com as funcoes 2,3,4,5,7,8
# Suporta ate 4 instancias em 1 a 4 projetos; worktrees apenas se 2+ instancias no mesmo projeto.
# O comando `devin` inicia um REPL interativo no diretorio atual.

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$DevinArgs = @()
)

Set-StrictMode -Off

# Mensagens centralizadas (templates para futura i18n)
$M = @{
    UsandoTerminal = 'Usando terminal base: {0}'
    WtNaoEncontrado = 'wt.exe nao encontrado. Novas instancias abrirao em janelas de PowerShell separadas.'
    SelecioneWorkspace = "`nSelecione os projetos no terminal (ate 4 instancias)..."
    SelecaoCancelada = 'Selecao de {0} cancelada. Encerrando.'
    WorkspaceDefinido = "Workspace definido para: {0}`n"
    NenhumaPastaSelecionada = "Nenhuma pasta selecionada. Mantendo no diretorio atual.`n"
    DimensaoJanela = 'Aviso: Nao foi possivel obter as dimensoes da janela. Redimensionamento desabilitado.'
    NaoGitRepo = 'O projeto "{0}" nao e um repositorio Git. Apenas 1 instancia e permitida e nao havera selecao de branch.'
    ArgsIgnorados = 'Aviso: argumentos nao utilizados pelo launcher (ignorados): {0}'
    EscolhaReconfigurar = 'Escolha qual projeto reconfigurar (Esc volta ao resumo)'
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
    EstabilizacaoCpu = 'Verificando instancias extras (max 10s)...'
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
    WorktreeSujo = '  Worktree "{0}" tem alteracoes nao commitadas:'
    WorktreeSujoConfirm = '  Remover mesmo assim, descartando as alteracoes? [s/N]'
    WorktreePreservado = '  Worktree "{0}" preservado.'
    WorktreeBloqueado = '  Worktree "{0}" bloqueado por outra sessao ({1}). Ignorando.'
    DepFaltando = 'Dependencias obrigatorias ausentes: {0}. Instale-as e tente novamente.'
    DepGhAusente = 'gh CLI ausente: metadados de PR/branches protegidas ficarao vazios.'
    DepGhSemAuth = 'gh nao autenticado (gh auth status falhou): metadados gh podem vir vazios.'
    MetadadosGithub = 'Obtendo metadados do GitHub (PRs, protegidas, default)...'
}

# Sentinel da opcao "nova branch": contem '[' e espaco, invalidos em git check-ref-format
$script:NewBranchSentinel = '[Nova branch]'

function Find-WorkingWt {
    $candidates = @()
    try {
        $candidates = (& where.exe 'wt' 2>$null) -split '\r?\n' |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ }
    } catch { Write-Verbose "where.exe wt falhou: $_" }

    foreach ($candidate in $candidates) {
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }

        $shimFile = [System.IO.Path]::ChangeExtension($candidate, '.shim')
        if (Test-Path -LiteralPath $shimFile) {
            $content = Get-Content -LiteralPath $shimFile -Raw
            $m = [regex]::Match(
                $content,
                '^\s*path\s*=\s*"(.+?)"\s*$',
                [System.Text.RegularExpressions.RegexOptions]::Multiline
            )
            if ($m.Success) {
                $target = $m.Groups[1].Value
                if (Test-Path -LiteralPath $target -PathType Leaf) {
                    return $candidate
                }
            }
            continue
        }

        return $candidate
    }

    return $null
}

function Test-DevinPreflight {
    # Falha cedo: git/devin obrigatorios; gh (e auth) so avisos.
    $missing = @()
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { $missing += 'git' }
    if (-not (Get-Command devin -ErrorAction SilentlyContinue)) { $missing += 'devin' }
    $warnings = @()
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        $warnings += 'gh-ausente'
    }
    else {
        $null = gh auth status 2>&1
        if ($LASTEXITCODE -ne 0) { $warnings += 'gh-sem-auth' }
    }
    return [PSCustomObject]@{ Missing = $missing; Warnings = $warnings }
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
$wtPath = Find-WorkingWt
if (-not $wtPath) { Write-Host $M.WtNaoEncontrado -ForegroundColor DarkYellow }

if ($DevinArgs.Count -gt 0) {
    Write-Host ($M.ArgsIgnorados -f ($DevinArgs -join ' ')) -ForegroundColor DarkYellow
}

# Preflight de dependencias: falha antes de criar worktrees/paineis
$preflight = Test-DevinPreflight
if ($preflight.Missing.Count -gt 0) {
    Write-Host ($M.DepFaltando -f ($preflight.Missing -join ', ')) -ForegroundColor Red
    exit 1
}
foreach ($w in $preflight.Warnings) {
    if ($w -eq 'gh-ausente') { Write-Host $M.DepGhAusente -ForegroundColor DarkYellow }
    elseif ($w -eq 'gh-sem-auth') { Write-Host $M.DepGhSemAuth -ForegroundColor DarkYellow }
}
Write-Verbose "Preflight: missing=[$($preflight.Missing -join ',')] warnings=[$($preflight.Warnings -join ',')] wt=$wtPath"

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
        [void]$items.Add([PSCustomObject]@{ Name = '[>] Usar esta pasta'; Caminho = $current; Tipo = 'acao' })

        $parent = Split-Path -Parent -Path $current
        if ($parent -and $parent -ne $current) {
            [void]$items.Add([PSCustomObject]@{ Name = '[..] Voltar'; Caminho = $parent; Tipo = 'acao' })
        }
        else {
            [void]$items.Add([PSCustomObject]@{ Name = '[D] Trocar de drive'; Caminho = ''; Tipo = 'acao' })
        }

        $subdirs = Get-ChildItem -Path $current -Directory -ErrorAction SilentlyContinue | Sort-Object Name
        foreach ($d in $subdirs) {
            [void]$items.Add([PSCustomObject]@{ Name = "[+] $($d.Name)"; Caminho = $d.FullName; Tipo = 'pasta' })
        }

        $breadcrumbs = ($current -split '\\' | Where-Object { $_ }) -join ' > '
        if ([string]::IsNullOrWhiteSpace($breadcrumbs)) { $breadcrumbs = $current }

        $selected = Show-TerminalList -Items $items -Title "Selecione o workspace" -Subtitle $breadcrumbs -ToString { param($x) $x.Name } -OnCtrlL { return [PSCustomObject]@{ __CtrlL = $true } }

        if ($selected -and $selected.__CtrlL) {
            Clear-Host
            Write-Host "Editar caminho (Enter confirma, Esc cancela)" -ForegroundColor Cyan
            Write-Host -NoNewline "Caminho: " -ForegroundColor DarkGray
            $newPath = Read-EditableLine -Initial $current -PathCompletion
            if ($null -eq $newPath) {
                # Esc: volta a navegacao
            }
            elseif (Test-Path -LiteralPath $newPath -PathType Container) {
                $current = (Resolve-Path -LiteralPath $newPath).Path
            }
            elseif ($newPath) {
                Write-Host "`nCaminho invalido. Pressione qualquer tecla." -ForegroundColor Red
                $null = [Console]::ReadKey($true)
            }
            continue
        }

        if (-not $selected) {
            # Esc sobe um nivel; se estiver na raiz, cancela ou mantem
            if ($parent -and $parent -ne $current) {
                $current = $parent
                continue
            }
            if ($AllowCancel) { return $null }
            return $current
        }

        if ($selected.Tipo -eq 'acao' -and $selected.Name -match '^\[>\]') { return $selected.Caminho }
        if ($selected.Tipo -eq 'acao' -and $selected.Name -match '^\[\.\.\]') {
            $current = $parent
            continue
        }
        if ($selected.Tipo -eq 'acao' -and $selected.Name -match '^\[D\]') {
            $drives = [System.IO.DriveInfo]::GetDrives() |
                Where-Object { $_.DriveType -in @('Fixed', 'Network') } |
                ForEach-Object {
                    [PSCustomObject]@{
                        Name = "[D] $($_.Name) ($($_.VolumeLabel))"
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

        $headLines = git -C $RepoPath for-each-ref 'refs/heads' --format='%(refname:short)|%(upstream:short)|%(objectname:short)|%(committerdate:iso8601)|%(upstream:track)' 2>&1
        foreach ($line in $headLines) {
            $parts = $line -split '\|'
            if ($parts.Count -lt 5) { continue }
            $name = $parts[0]
            $upstream = $parts[1]
            $sha = $parts[2]
            $lastCommit = if ($parts[3]) { [datetime]::Parse($parts[3], [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::RoundtripKind) } else { $null }
            $track = $parts[4]
            $hasUpstream = -not [string]::IsNullOrWhiteSpace($upstream)
            $remoteInfo = $remoteMeta[$name]
            $existsOnRemote = $null -ne $remoteInfo

            # ahead/behind via %(upstream:track) na mesma chamada; rev-list so p/ fallback sem upstream
            $ahead = 0
            $behind = 0
            if ($hasUpstream) {
                if ($track -match 'ahead (\d+)') { $ahead = [int]$matches[1] }
                if ($track -match 'behind (\d+)') { $behind = [int]$matches[2] }
            }
            elseif ($existsOnRemote) {
                $counts = git -C $RepoPath rev-list --left-right --count "refs/heads/$name...$($remoteInfo.Ref)" 2>&1
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

function Remove-DirRobust {
    # Remove-Item nao deleta arquivos com nomes reservados (nul, con, aux) —
    # cmd rd com prefixo \\?\ lida com eles.
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    try {
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
    }
    catch {
        $abs = [System.IO.Path]::GetFullPath($Path)
        cmd /c rd /s /q "\\?\$abs" 2>$null
    }
}

function Escape-Sq {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    return ($Text -replace "'", "''")
}

function Get-WorktreePorcelainInfo {
    # path normalizado -> @{ Locked; Reason } para cada worktree registrado
    param([string]$RepoPath)
    $info = @{}
    $current = $null
    foreach ($line in @(git -C $RepoPath worktree list --porcelain 2>$null)) {
        if ($line -match '^worktree\s+(.+)$') {
            $current = ($matches[1] -replace '/', '\').TrimEnd('\')
            $info[$current] = @{ Locked = $false; Reason = '' }
        }
        elseif ($line -match '^locked\b\s*(.*)$' -and $current) {
            $info[$current].Locked = $true
            $info[$current].Reason = $matches[1].Trim()
        }
        elseif ($line -eq '') { $current = $null }
    }
    return $info
}

function Get-WorktreeDirtyFiles {
    # alteracoes nao commitadas do worktree; @() se limpo/inexistente/nao-worktree
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return @() }
    if (-not (Test-Path -LiteralPath (Join-Path $Path '.git'))) { return @() }
    $status = @(git -C $Path status --porcelain 2>$null | Where-Object { $_ })
    if ($LASTEXITCODE -ne 0) { return @('(git status falhou)') }
    return $status
}

function Remove-WorktreeSafe {
    # Remove worktree com gates: lock de outra sessao = skip; sujo = confirma.
    # Retorna $true se o diretorio nao existe mais.
    param([string]$RepoPath, [string]$WorktreePath)
    $norm = ($WorktreePath -replace '/', '\').TrimEnd('\')

    $info = Get-WorktreePorcelainInfo -RepoPath $RepoPath
    $entry = $info[$norm]
    if ($entry -and $entry.Locked) {
        if ($entry.Reason -eq "devin-N $PID") {
            $null = git -C $RepoPath worktree unlock "$WorktreePath" 2>&1
        }
        else {
            Write-Host ($M.WorktreeBloqueado -f $WorktreePath, $entry.Reason) -ForegroundColor Yellow
            return $false
        }
    }

    $dirty = Get-WorktreeDirtyFiles -Path $WorktreePath
    if ($dirty.Count -gt 0) {
        Write-Host ($M.WorktreeSujo -f $WorktreePath) -ForegroundColor Yellow
        $dirty | Select-Object -First 10 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
        $resp = Read-Host $M.WorktreeSujoConfirm
        if ($resp -notmatch '^[sS]') {
            Write-Host ($M.WorktreePreservado -f $WorktreePath) -ForegroundColor DarkYellow
            return $false
        }
    }

    $null = git -C $RepoPath worktree remove "$WorktreePath" --force 2>&1
    if (Test-Path -LiteralPath $WorktreePath) {
        if ($entry) {
            Write-Warning "Nao foi possivel remover worktree '$WorktreePath'."
            return $false
        }
        # dir orfao (nao registrado pelo git): seguro apagar
        Remove-DirRobust $WorktreePath
    }
    return -not (Test-Path -LiteralPath $WorktreePath)
}

function Remove-StaleWorktrees {
    # Escopo: so worktrees unlocked com prefixo instancia- (locks "devin-N <pid>"
    # protegem sessoes concorrentes) e dirs orfaos apenas quando nenhuma outra
    # sessao devin-N esta viva (marcador .session-<pid> no .worktrees).
    param([string]$RepoPath)
    try {
        $info = Get-WorktreePorcelainInfo -RepoPath $RepoPath
        foreach ($p in @($info.Keys)) {
            if ($p -notmatch '\\\.worktrees\\instancia-') { continue }
            if ($info[$p].Locked) { continue }
            $null = Remove-WorktreeSafe -RepoPath $RepoPath -WorktreePath $p
        }
        $null = git -C $RepoPath worktree prune 2>&1
        # dirs orfaos: worktree remove falhou antes ou o dir foi recriado sem
        # registro (ex.: checkout abortado); git worktree list nao os ve
        $orphanRoot = Join-Path $RepoPath ".worktrees"
        if (Test-Path -LiteralPath $orphanRoot) {
            $foreignAlive = $false
            $markers = @(Get-ChildItem -LiteralPath $orphanRoot -Filter ".session-*" -Force -ErrorAction SilentlyContinue)
            foreach ($m in $markers) {
                if ($m.Name -match '^\.session-(\d+)$') {
                    $mpid = [int]$matches[1]
                    if ($mpid -ne $PID -and (Get-Process -Id $mpid -ErrorAction SilentlyContinue)) {
                        $foreignAlive = $true
                    }
                }
            }
            if (-not $foreignAlive) {
                Get-ChildItem -LiteralPath $orphanRoot -Directory -Filter "instancia-*" -ErrorAction SilentlyContinue |
                    ForEach-Object {
                        $d = $_.FullName
                        if (Test-Path -LiteralPath (Join-Path $d '.git')) {
                            $null = Remove-WorktreeSafe -RepoPath $RepoPath -WorktreePath $d
                        }
                        else {
                            Remove-DirRobust $d
                        }
                    }
            }
            # limpa marcadores de sessoes mortas
            foreach ($m in $markers) {
                if ($m.Name -match '^\.session-(\d+)$' -and -not (Get-Process -Id $matches[1] -ErrorAction SilentlyContinue)) {
                    Remove-Item -LiteralPath $m.FullName -Force -ErrorAction SilentlyContinue
                }
            }
        }
    }
    catch { Write-Warning "Falha ao remover worktrees antigas: $_" }
}

function Restore-OriginalBranches {
    # Restaura a branch original de todo projeto cujo dir real sofreu switch
    # (instancias sem worktree, em qualquer modo de execucao).
    param([array]$Projetos)
    foreach ($proj in @($Projetos | Where-Object { $_.IsGitRepo -and $_.OriginalBranch })) {
        $current = git -C $proj.Path branch --show-current 2>$null
        if ($current -and $current -ne $proj.OriginalBranch) {
            $null = git -C $proj.Path switch $proj.OriginalBranch 2>&1
            if ($?) { Write-Host ($M.BranchOriginalRestaurada -f $proj.OriginalBranch) -ForegroundColor Green }
            else { Write-Host ($M.BranchOriginalFalha -f $proj.OriginalBranch) -ForegroundColor Yellow }
        }
    }
}

function Remove-CreatedBranches {
    # Deleta branches criadas nesta execucao (merged-only); roda apos o restore.
    param([array]$Projetos)
    foreach ($proj in @($Projetos | Where-Object { $_.CreatedBranches.Count -gt 0 })) {
        Push-Location -LiteralPath $proj.Path
        try {
            foreach ($cb in $proj.CreatedBranches) {
                # preserva branch com commits nao mergeados - merge manual apos a tarefa
                if (git branch --merged HEAD --list $cb 2>$null) {
                    $null = git branch -d $cb 2>&1
                }
                else {
                    Write-Host "  Branch '$cb' tem commits nao mergeados - mantida para merge manual." -ForegroundColor Yellow
                }
            }
        }
        finally { Pop-Location }
    }
}

function Select-BranchTerminal {
    param(
        [array]$Options,
        [hashtable]$MetaMap,
        [hashtable]$PrMap,
        [hashtable]$ProtectedSet,
        [string]$DefaultBranch,
        [string]$Title,
        [string]$Subtitle = ''
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
    $selected = Show-TerminalList -Items $rows -Title $Title -Subtitle $Subtitle -ToString {
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

function Select-BranchesForProject {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [PSCustomObject]$Project,
        [Parameter(Mandatory)]
        [array]$Positions,
        [int]$StartLabelIndex = 0,
        [array]$AllLabels = @('A','B','C','D')
    )

    $projectPath = $Project.Path
    $count = $Project.Count
    $instances = @()
    $selectedBranches = @()
    $selectedBranchNames = @()
    $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'

    Write-Host $M.WorktreeWorkspaceGit -ForegroundColor Magenta
    Remove-StaleWorktrees -RepoPath $projectPath

    $fetchResult = Invoke-WithSpinner -Message $M.SincronizandoReferencias -ScriptBlock {
        $output = git -C $Ctx.projectPath fetch --all --prune 2>&1
        [PSCustomObject]@{ Ok = $?; Output = $output }
    } -ArgumentList @{ projectPath = $projectPath }
    if ($fetchResult -and $fetchResult.Ok) {
        Write-Host $M.ReferenciasAtualizadas -ForegroundColor Green
    }
    else {
        Write-Host $M.ReferenciasFalha -ForegroundColor Yellow
    }

    $getBranchMetadataDef = (Get-Command Get-BranchMetadata).ScriptBlock.ToString()
    $branchMeta = Invoke-WithSpinner -Message $M.MetadadosBranches -ScriptBlock {
        $def = $Ctx.getBranchMetadataDef
        New-Item -Path 'function:global:Get-BranchMetadata' -Value ([scriptblock]::Create($def)) -Force | Out-Null
        Get-BranchMetadata -RepoPath $Ctx.projectPath
    } -ArgumentList @{ getBranchMetadataDef = $getBranchMetadataDef; projectPath = $projectPath }
    # shape defensivo: retorno deve ser hashtable de metadados por branch
    if ($branchMeta -isnot [hashtable]) {
        Write-Warning "Metadados de branches em formato inesperado; usando mapa vazio."
        $branchMeta = @{}
    }

    $ghFnDefs = @(
        @{ Name = 'Get-PullRequestMap'; Body = (Get-Command Get-PullRequestMap).ScriptBlock.ToString() },
        @{ Name = 'Get-ProtectedBranchSet'; Body = (Get-Command Get-ProtectedBranchSet).ScriptBlock.ToString() },
        @{ Name = 'Get-DefaultBranchName'; Body = (Get-Command Get-DefaultBranchName).ScriptBlock.ToString() }
    )
    $ghMeta = Invoke-WithSpinner -Message $M.MetadadosGithub -ScriptBlock {
        foreach ($d in $Ctx.defs) {
            New-Item -Path "function:global:$($d.Name)" -Value ([scriptblock]::Create($d.Body)) -Force | Out-Null
        }
        [PSCustomObject]@{
            PrMap = Get-PullRequestMap -RepoPath $Ctx.projectPath
            ProtectedSet = Get-ProtectedBranchSet -RepoPath $Ctx.projectPath
            DefaultBranch = Get-DefaultBranchName -RepoPath $Ctx.projectPath
        }
    } -ArgumentList @{ defs = $ghFnDefs; projectPath = $projectPath }
    $prMap = $ghMeta.PrMap
    $protectedSet = $ghMeta.ProtectedSet
    $defaultBranch = $ghMeta.DefaultBranch

    Write-Host $M.ListandoBranches -ForegroundColor DarkGray

    $localBranches = @()
    $localBranches += @((git -C $projectPath for-each-ref 'refs/heads' --format='%(refname:short)' 2>$null) | Where-Object { $_ })

    $remoteRefs = [ordered]@{}
    foreach ($line in @(git -C $projectPath for-each-ref 'refs/remotes' --format='%(refname:lstrip=2)|%(refname:lstrip=3)' 2>$null)) {
        $parts = $line -split '\|', 2
        if ($parts.Count -lt 2) { continue }
        $remoteRef = $parts[0]
        $branchName = $parts[1]
        if (-not $branchName -or $branchName -eq 'HEAD') { continue }
        if (-not $remoteRefs.Contains($branchName)) { $remoteRefs[$branchName] = $remoteRef }
    }

    $remoteOnly = @($remoteRefs.Keys | Where-Object { $_ -notin $localBranches -and $_ -ne $defaultBranch })
    $currentBranch = git -C $projectPath branch --show-current 2>$null

    $allOptions = @()
    if ($defaultBranch) {
        $localDefault = [bool](git -C $projectPath rev-parse --verify --quiet $defaultBranch 2>$null)
        $remoteDefaultRef = $remoteRefs[$defaultBranch]
        if ($localDefault -or $remoteDefaultRef) {
            $allOptions += @{
                Name = $defaultBranch
                Type = if ($localDefault) { "local" } else { "remote" }
                IsCurrent = ($defaultBranch -eq $currentBranch)
                RemoteRef = $remoteDefaultRef
            }
        }
    }

    if ($localBranches.Count -gt 0) {
        foreach ($b in $localBranches) {
            if ($b -eq $defaultBranch) { continue }
            $allOptions += @{ Name = $b; Type = "local"; IsCurrent = ($b -eq $currentBranch) }
        }
    }

    if ($remoteOnly.Count -gt 0) {
        foreach ($b in $remoteOnly) {
            $allOptions += @{ Name = $b; Type = "remote"; IsCurrent = $false; RemoteRef = $remoteRefs[$b] }
        }
    }

    if ($allOptions.Count -eq 0) {
        Write-Host $M.NenhumBranch -ForegroundColor DarkGray
    }

    $newBranchOption = @{ Name = $script:NewBranchSentinel; Type = "new"; IsCurrent = $false }

    for ($i = 0; $i -lt $count; $i++) {
        $labelIndex = $StartLabelIndex + $i
        $pos = $Positions[$labelIndex]
        $titulo = if ($pos) { "Selecione a branch - Instancia $($AllLabels[$labelIndex]) ($pos)" } else { "Selecione a branch - Instancia $($AllLabels[$labelIndex])" }

        $selected = $null
        while (-not $selected) {
            $selectedNames = @($selectedBranches | ForEach-Object { $_.Name })
            $available = @($allOptions | Where-Object { $_.Name -notin $selectedNames })
            $available += $newBranchOption

            $selected = Select-BranchTerminal -Options $available -MetaMap $branchMeta -PrMap $prMap -ProtectedSet $protectedSet -DefaultBranch $defaultBranch -Title $titulo -Subtitle $projectPath
            if (-not $selected) {
                return [PSCustomObject]@{ Success = $false; Instances = @(); Project = $Project }
            }

            if ($selected.Type -ne 'new' -and $selected.Name -in $selectedBranchNames) {
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
                $baseOptions = @($baseOptions | Where-Object { $_.Name } | Sort-Object Name -Unique)
                $baseSelected = Select-BranchTerminal -Options $baseOptions -MetaMap $branchMeta -PrMap $prMap -ProtectedSet $protectedSet -DefaultBranch $defaultBranch -Title ($M.BranchBaseSelecione -f $projectPath) -Subtitle $projectPath
                if (-not $baseSelected) {
                    $selectedBranches = @($selectedBranches | Where-Object { $_ -ne $selected })
                    $i--
                    continue
                }
                $baseBranch = $baseSelected.Name
            }
            else {
                $baseBranch = $currentBranch
            }

            $defaultBranchName = "devin-$timestamp-$($AllLabels[$labelIndex].ToLower())"
            $initialProjectLabelIdx = $labelIndex - $i
            $reservedAutoNames = @()
            for ($k = 0; $k -lt $count; $k++) {
                $reservedAutoNames += "devin-$timestamp-$($AllLabels[$initialProjectLabelIdx + $k].ToLower())"
            }

            $nameCancelled = $false
            while ($true) {
                Write-Host ($M.BranchNomePersonalizado -f $defaultBranchName) -ForegroundColor Cyan
                $customName = Read-EditableLine -Initial $defaultBranchName
                if ($null -eq $customName) { $nameCancelled = $true; break }
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
            if ($nameCancelled) {
                $selectedBranches = @($selectedBranches | Where-Object { $_ -ne $selected })
                $i--
                continue
            }
        }

        $selectedBranchNames += $branch

        $instances += [PSCustomObject]@{
            Label = $AllLabels[$labelIndex]
            Project = $Project
            ProjectPath = $projectPath
            BranchInfo = $selected
            Branch = $branch
            BaseBranch = $baseBranch
            WorktreePath = $null
            Position = $pos
            IsMain = ($labelIndex -eq 0)
        }
    }

    $Project.OriginalBranch = $currentBranch
    $Project.CurrentBranch = $currentBranch

    return [PSCustomObject]@{ Success = $true; Instances = $instances; Project = $Project }
}

function Get-InstanceTotal {
    param([array]$Items)
    $sum = 0
    foreach ($i in $Items) { $sum += $i.Count }
    return $sum
}

function Start-Wizard {
    $projetos = @()
    $instancias = @()
    $labels = @('A','B','C','D')
    $state = 'PROJECT'
    $currentProjectIndex = 0
    $instancesMode = 'new'
    $instancesReturn = 'BRANCH_PREP'

    while ($state -ne 'EXECUTE' -and $state -ne 'CANCEL') {
        switch ($state) {
            'PROJECT' {
                $total = Get-InstanceTotal $projetos
                $vagas = 4 - $total
                if ($vagas -le 0) { $state = 'BRANCH_PREP'; continue }

                $title = if ($projetos.Count -eq 0) {
                    "Selecione o projeto 1 ($vagas vagas)"
                } else {
                    "Selecione outro projeto ou cancele ($vagas vagas)"
                }
                $initial = if ($projetos.Count -gt 0) { $projetos[-1].Path } else { $diretorioOriginal.Path }

                $projectPath = Select-FolderTerminal -InitialPath $initial -AllowCancel
                if (-not $projectPath) {
                    if ($projetos.Count -eq 0) { $state = 'CANCEL'; continue }
                    $state = 'BRANCH_PREP'; continue
                }

                $already = $projetos | Where-Object { $_.Path -eq $projectPath } | Select-Object -First 1
                if ($already) {
                    Write-Host $M.ProjetoJaSelecionado -ForegroundColor Yellow
                    continue
                }

                $isGitRepo = Test-Path -LiteralPath (Join-Path $projectPath ".git")
                if (-not $isGitRepo) {
                    Write-Host ($M.NaoGitRepo -f $projectPath) -ForegroundColor DarkYellow
                }

                $projetos += [PSCustomObject]@{
                    Path = $projectPath
                    Count = 1
                    IsGitRepo = $isGitRepo
                    WorktreesRoot = $null
                    CreatedWorktrees = @()
                    CreatedBranches = @()
                    OriginalBranch = $null
                    CurrentBranch = $null
                }

                $currentProjectIndex = $projetos.Count - 1
                $instancesMode = 'new'
                $state = 'INSTANCES'
                continue
            }

            'INSTANCES' {
                $proj = $projetos[$currentProjectIndex]
                $otherTotal = Get-InstanceTotal @($projetos | Where-Object { $_.Path -ne $proj.Path })
                $vagas = 4 - $otherTotal
                $maxForProject = if ($proj.IsGitRepo) { $vagas } else { 1 }

                $opcoesQuantidade = @()
                for ($i = 1; $i -le $maxForProject; $i++) {
                    $opcoesQuantidade += [PSCustomObject]@{ Numero = $i; Label = "$i instancia(s)" }
                }

                $defaultIdx = [Math]::Max(0, [Math]::Min($proj.Count - 1, $maxForProject - 1))
                $escolhaQuantidade = Show-TerminalList -Items $opcoesQuantidade -Title ($M.QuantasInstancias -f $proj.Path) -ToString { param($x) $x.Label } -DefaultIndex $defaultIdx
                if (-not $escolhaQuantidade) {
                    if ($instancesMode -eq 'new') {
                        $projetos = @($projetos | Where-Object { $_.Path -ne $proj.Path })
                        if ($projetos.Count -eq 0) { $state = 'CANCEL'; continue }
                        $state = 'PROJECT'; continue
                    }
                    else {
                        $projetos = @($projetos | Where-Object { $_.Path -ne $proj.Path })
                        $instancias = @($instancias | Where-Object { $_.Project -ne $proj })
                        $instancesMode = 'new'
                        if ($projetos.Count -eq 0) { $state = 'CANCEL'; continue }
                        $state = 'PROJECT'; continue
                    }
                }

                $proj.Count = $escolhaQuantidade.Numero
                if ($instancesMode -eq 'new') { $state = 'MORE' }
                else { $state = $instancesReturn }
                continue
            }

            'MORE' {
                $total = Get-InstanceTotal $projetos
                if ($total -ge 4) { $state = 'BRANCH_PREP'; continue }

                $simNao = @(
                    [PSCustomObject]@{ Resposta = $true; Label = 'Sim, adicionar outro projeto' },
                    [PSCustomObject]@{ Resposta = $false; Label = 'Nao, concluir selecao' }
                )
                $continuar = Show-TerminalList -Items $simNao -Title ($M.AdicionarProjeto + " (total: $total)") -ToString { param($x) $x.Label } -DefaultIndex 1
                if (-not $continuar) {
                    $currentProjectIndex = $projetos.Count - 1
                    $instancesMode = 'edit'
                    $instancesReturn = 'MORE'
                    $state = 'INSTANCES'
                    continue
                }
                if (-not $continuar.Resposta) { $state = 'BRANCH_PREP'; continue }
                $state = 'PROJECT'
                continue
            }

            'BRANCH_PREP' {
                $total = Get-InstanceTotal $projetos
                if ($total -eq 0) { $state = 'CANCEL'; continue }

                $positions = switch ($total) {
                    2 { @('esquerda','direita','','') }
                    3 { @('esquerda','superior-direita','inferior-direita','') }
                    4 { @('superior-esquerda','superior-direita','inferior-esquerda','inferior-direita') }
                    default { @('','','','') }
                }

                $instancias = @($instancias | Where-Object {
                    $p = $_.Project
                    ($projetos -contains $p) -and (@($instancias | Where-Object { $_.Project -eq $p }).Count -eq $p.Count)
                })

                $labelIdx = 0
                foreach ($p in $projetos) {
                    foreach ($inst in @($instancias | Where-Object { $_.Project -eq $p })) {
                        $inst.Label = $labels[$labelIdx]
                        $inst.Position = $positions[$labelIdx]
                        $inst.IsMain = ($labelIdx -eq 0)
                        $labelIdx++
                    }
                }

                $currentProjectIndex = 0
                $state = 'BRANCH'
                continue
            }

            'BRANCH' {
                $proj = $projetos[$currentProjectIndex]
                $startLabelIndex = Get-InstanceTotal @($projetos | Select-Object -First $currentProjectIndex)

                if (@($instancias | Where-Object { $_.Project -eq $proj }).Count -gt 0) {
                    $currentProjectIndex++
                    if ($currentProjectIndex -ge $projetos.Count) { $state = 'SUMMARY'; continue }
                    continue
                }

                if (-not $proj.IsGitRepo) {
                    $instancias += [PSCustomObject]@{
                        Label = $labels[$startLabelIndex]
                        Project = $proj
                        ProjectPath = $proj.Path
                        BranchInfo = $null
                        Branch = $null
                        BaseBranch = $null
                        WorktreePath = $null
                        Position = $positions[$startLabelIndex]
                        IsMain = ($startLabelIndex -eq 0)
                    }
                }
                else {
                    $result = Select-BranchesForProject -Project $proj -Positions $positions -StartLabelIndex $startLabelIndex -AllLabels $labels
                    if (-not $result.Success) {
                        $instancias = @($instancias | Where-Object { $_.Project -ne $proj })
                        $instancesMode = 'edit'
                        $instancesReturn = 'BRANCH_PREP'
                        $state = 'INSTANCES'
                        continue
                    }
                    $instancias += $result.Instances
                }

                $currentProjectIndex++
                if ($currentProjectIndex -ge $projetos.Count) { $state = 'SUMMARY'; continue }
                continue
            }

            'SUMMARY' {
                $confirm = Show-Summary -Instances $instancias
                if ($confirm) { $state = 'EXECUTE'; continue }

                # Esc: escolher QUALQUER projeto para reconfigurar (era so o ultimo)
                $projPick = Show-TerminalList -Items @($projetos) -Title $M.EscolhaReconfigurar -ToString { param($x) $x.Path }
                if (-not $projPick) { $state = 'SUMMARY'; continue }
                $instancias = @($instancias | Where-Object { $_.Project -ne $projPick })
                $currentProjectIndex = [array]::IndexOf($projetos, $projPick)
                $instancesMode = 'edit'
                $instancesReturn = 'BRANCH_PREP'
                $state = 'INSTANCES'
                continue
            }
        }
    }

    if ($state -eq 'CANCEL') { return $null }
    return [PSCustomObject]@{ Projetos = $projetos; Instances = $instancias }
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

        public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

        [DllImport("user32.dll")]
        public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);

        [DllImport("user32.dll")]
        public static extern bool IsWindowVisible(IntPtr hWnd);

        [DllImport("user32.dll")]
        public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);

        public const uint WM_CLOSE = 0x0010;

        public static IntPtr FindWindowByTitle(string needle) {
            IntPtr found = IntPtr.Zero;
            EnumWindows(delegate(IntPtr h, IntPtr l) {
                if (!IsWindowVisible(h)) { return true; }
                var sb = new System.Text.StringBuilder(512);
                GetWindowText(h, sb, sb.Capacity);
                if (sb.ToString().IndexOf(needle, StringComparison.Ordinal) >= 0) { found = h; return false; }
                return true;
            }, IntPtr.Zero);
            return found;
        }
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

# 4. Wizard de escolha de projetos/instancias/branches
$wizardResult = Start-Wizard
if (-not $wizardResult) {
    Write-Host ($M.SelecaoCancelada -f 'projetos') -ForegroundColor Yellow
    exit
}
$projetos = $wizardResult.Projetos
$instancias = $wizardResult.Instances
$totalInstancias = $instancias.Count

Write-Host ($M.ConfigurandoInstancias -f $totalInstancias, $projetos.Count) -ForegroundColor Cyan

# 5. Prepara variaveis de execucao
$numInstancias = $totalInstancias
# Cria worktrees por projeto conforme necessario

foreach ($proj in $projetos | Where-Object { $_.IsGitRepo -and $_.Count -gt 1 }) {
    Write-Host $M.WorktreeCriando -ForegroundColor Magenta
    $projectPath = $proj.Path
    $worktreesRoot = Join-Path $projectPath ".worktrees"
    if (-not (Test-Path -LiteralPath $worktreesRoot)) { New-Item -ItemType Directory -LiteralPath $worktreesRoot -Force | Out-Null }
    $proj.WorktreesRoot = $worktreesRoot
    # marcador de sessao: outras execucoes nao varrem dirs orfaos enquanto este PID vive
    New-Item -ItemType File -Path (Join-Path $worktreesRoot ".session-$PID") -Force | Out-Null

    try {
        $projInstances = @($instancias | Where-Object { $_.Project -eq $proj })
        foreach ($inst in $projInstances) {
            $worktree = Join-Path $worktreesRoot "instancia-$($inst.Label.ToLower())"

            if (-not (Remove-WorktreeSafe -RepoPath $projectPath -WorktreePath $worktree)) {
                throw "Worktree '$worktree' preservado (alteracoes ou bloqueio de outra sessao). Encerrando."
            }

            $info = $inst.BranchInfo
            $branch = $inst.Branch

            $spinnerMessage = ($M.WorktreeInstancia -f $inst.Label, $worktree)
            $worktreeAddOk = $true
            $createdBranch = $false
            if ($info.Type -eq "new" -or $info.Type -eq "remote") {
                $baseRef = if ($info.Type -eq "new") {
                    if ($inst.BaseBranch) { $inst.BaseBranch } else { $proj.CurrentBranch }
                } else {
                    if ($info.RemoteRef) { $info.RemoteRef } else { "origin/$($inst.Branch)" }
                }
                $result = Invoke-WithSpinner -Message $spinnerMessage -ScriptBlock {
                    $output = git -C $Ctx.projectPath worktree add "$($Ctx.worktree)" -b $Ctx.branch $Ctx.baseRef 2>&1
                    [PSCustomObject]@{ Ok = $?; Output = $output }
                } -ArgumentList @{ projectPath = $projectPath; worktree = $worktree; branch = $branch; baseRef = $baseRef }
                if (-not ($result -and $result.Ok) -and (git -C $projectPath branch --list $branch)) {
                    # branch ja existe (rerun, local de remota, resto de crash): anexa em vez de recriar
                    $result = Invoke-WithSpinner -Message $spinnerMessage -ScriptBlock {
                        $output = git -C $Ctx.projectPath worktree add "$($Ctx.worktree)" $Ctx.branch 2>&1
                        [PSCustomObject]@{ Ok = $?; Output = $output }
                    } -ArgumentList @{ projectPath = $projectPath; worktree = $worktree; branch = $branch }
                    if ($result -and $result.Ok) {
                        Write-Host ($M.WorktreeBranch -f $branch, " (existente - anexada)") -ForegroundColor DarkGray
                    }
                }
                else {
                    $createdBranch = ($info.Type -eq "new") -and ($result -and $result.Ok)
                }
                $worktreeAddOk = $result -and $result.Ok
            }
            else {
                $result = Invoke-WithSpinner -Message $spinnerMessage -ScriptBlock {
                    $output = git -C $Ctx.projectPath worktree add "$($Ctx.worktree)" $Ctx.branch 2>&1
                    [PSCustomObject]@{ Ok = $?; Output = $output }
                } -ArgumentList @{ projectPath = $projectPath; worktree = $worktree; branch = $branch }
                $worktreeAddOk = $result -and $result.Ok
            }

            if (-not $worktreeAddOk) {
                $gitErr = ($result.Output | Out-String).Trim()
                throw "git worktree add falhou para '$worktree' (branch '$branch'): $gitErr"
            }

            $inst.WorktreePath = $worktree
            $proj.CreatedWorktrees += $worktree
            $null = git -C $projectPath worktree lock "$worktree" --reason "devin-N $PID" 2>&1
            if ($createdBranch) {
                $proj.CreatedBranches += $branch
            }

            $typeLabel = switch ($info.Type) { "new" { " (nova)" } "remote" { " (remota -> local)" } default { "" } }
            Write-Host ($M.WorktreeInstancia -f $inst.Label, $worktree) -ForegroundColor DarkCyan
            Write-Verbose "Worktree OK para $($inst.Label) em $worktree"
            Write-Host ($M.WorktreeBranch -f $branch, $typeLabel) -ForegroundColor DarkGray
        }

        Write-Host $M.WorktreeMerge -ForegroundColor DarkGray
    }
    catch {
        Write-Host ($M.WorktreeFalha -f $_.Exception.Message) -ForegroundColor Yellow
        foreach ($wt in $proj.CreatedWorktrees) {
            $null = Remove-WorktreeSafe -RepoPath $projectPath -WorktreePath $wt
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
        # branch nova criada no dir real (filho via switch -c ou main): registra p/ cleanup
        if ($inst.Project.IsGitRepo -and $inst.BranchInfo -and $inst.BranchInfo.Type -eq 'new') {
            $inst.Project.CreatedBranches += $inst.Branch
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
$janelasAdicionais = @()

function Get-InstanceCommand {
    param([PSCustomObject]$Inst)
    $workingDir = Escape-Sq $Inst.WorkingDirectory
    $branch = Escape-Sq $Inst.Branch
    $baseBranch = Escape-Sq $Inst.BaseBranch
    $isGitRepo = $Inst.Project.IsGitRepo
    $branchInfo = $Inst.BranchInfo
    $bundlePath = Escape-Sq $bundleRoot
    $doneFlagEsc = Escape-Sq $doneFlag

    $preCommands = @()
    $preCommands += "Set-Location -LiteralPath '$workingDir'"

    if ($isGitRepo -and $branch) {
        if ($branchInfo.Type -eq 'new') {
            $base = if ($baseBranch) { $baseBranch } else { Escape-Sq $Inst.Project.CurrentBranch }
            $preCommands += "git -C '$workingDir' switch -c '$branch' '$base' 2>`$null"
        }
        elseif (-not $Inst.WorktreePath) {
            $preCommands += "git -C '$workingDir' switch '$branch' 2>`$null"
        }
    }

    $preCommands += ". '$bundlePath\devin-session-launcher.ps1'; Start-DevinSession; Write-Host 'Instancia principal ainda ativa - aguardando encerrar...'; while ((Get-Process -Id $scriptPid -ErrorAction SilentlyContinue) -and -not (Test-Path -LiteralPath '$doneFlagEsc')) { Start-Sleep 2 }; exit"
    return ($preCommands -join "; ")
}

function ConvertTo-EncodedCommand {
    param([string]$Script)
    $bytes = [System.Text.Encoding]::Unicode.GetBytes($Script)
    return [Convert]::ToBase64String($bytes)
}

# 5. Abre as instancias adicionais
if ($numInstancias -gt 1) {
    $scriptPid = $PID
    $doneFlag = Join-Path $env:TEMP "devin-N-$scriptPid.done"
    Remove-Item -LiteralPath $doneFlag -Force -ErrorAction SilentlyContinue

    # devin ls compartilhado: 1 chamada no pai; filhos leem via DEVIN_N_SESSIONS_FILE
    $sessionsFile = Join-Path $env:TEMP "devin-N-$scriptPid-sessions.json"
    $lsOut = devin ls --format json 2>$null
    if ($LASTEXITCODE -eq 0 -and $lsOut) {
        [System.IO.File]::WriteAllText($sessionsFile, ($lsOut | Out-String))
        $env:DEVIN_N_SESSIONS_FILE = $sessionsFile
        Write-Verbose "devin ls compartilhado gravado em $sessionsFile"
    }

    if ($insideWT -and $wtPath) {
        Write-Host $M.PaineisDivididos -ForegroundColor Cyan

        $subcommands = @()
        if ($numInstancias -eq 2) {
            $subcommands += "split-pane -V -d `"$($instancias[1].WorkingDirectory)`" $psExecutable -NoExit -EncodedCommand $(ConvertTo-EncodedCommand (Get-InstanceCommand -Inst $instancias[1]))"
            $subcommands += "move-focus left"
        }
        elseif ($numInstancias -eq 3) {
            $subcommands += "split-pane -V -d `"$($instancias[1].WorkingDirectory)`" $psExecutable -NoExit -EncodedCommand $(ConvertTo-EncodedCommand (Get-InstanceCommand -Inst $instancias[1]))"
            $subcommands += "split-pane -H -d `"$($instancias[2].WorkingDirectory)`" $psExecutable -NoExit -EncodedCommand $(ConvertTo-EncodedCommand (Get-InstanceCommand -Inst $instancias[2]))"
            $subcommands += "move-focus left"
        }
        elseif ($numInstancias -eq 4) {
            $subcommands += "split-pane -H -d `"$($instancias[2].WorkingDirectory)`" $psExecutable -NoExit -EncodedCommand $(ConvertTo-EncodedCommand (Get-InstanceCommand -Inst $instancias[2]))"
            $subcommands += "move-focus up"
            $subcommands += "split-pane -V -d `"$($instancias[1].WorkingDirectory)`" $psExecutable -NoExit -EncodedCommand $(ConvertTo-EncodedCommand (Get-InstanceCommand -Inst $instancias[1]))"
            $subcommands += "split-pane -H -d `"$($instancias[3].WorkingDirectory)`" $psExecutable -NoExit -EncodedCommand $(ConvertTo-EncodedCommand (Get-InstanceCommand -Inst $instancias[3]))"
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

        # wt -w <id>: id unico por janela (derivado do PID); marcador de titulo
        # resolve o hwnd sem diff de processo (glomming tornaria o diff racy)
        $wtWinIdBase = ($PID % 200000) * 10
        for ($i = 1; $i -lt $numInstancias; $i++) {
            $inst = $instancias[$i]
            $wtWinId = $wtWinIdBase + $i
            $titleMarker = "devin-N-wt$wtWinId"
            $cmd = "[Console]::Title = '$titleMarker'; " + (Get-InstanceCommand -Inst $inst)

            $argsWT = "-w $wtWinId -d `"$($inst.WorkingDirectory)`" $psExecutable -NoExit -EncodedCommand $(ConvertTo-EncodedCommand $cmd)"
            $proc = Start-Process -FilePath $wtPath -ArgumentList $argsWT -PassThru
            if (-not $proc) { Write-Warning "Nao foi possivel abrir a janela $($inst.Label) via wt.exe."; continue }

            $timeout = 0
            $hWndFilho = [IntPtr]::Zero

            Write-Host ($M.JanelaGeracao -f $inst.Label) -ForegroundColor DarkGray
            while ($timeout -lt 60) {
                Start-Sleep -Milliseconds 200
                $hWndFilho = [WindowUtil]::FindWindowByTitle($titleMarker)
                if ($hWndFilho -ne [IntPtr]::Zero) {
                    $janelasAdicionais += $hWndFilho
                    break
                }
                $timeout++
            }

            if ($hWndFilho -ne [IntPtr]::Zero -and $windowUtilAvailable) {
                [WindowUtil]::SetWindowPos($hWndFilho, [IntPtr]::Zero, [int]$grid[$i].X, [int]$grid[$i].Y, [int]$grid[$i].W, [int]$grid[$i].H, 0x0040) | Out-Null
                Write-Host ($M.JanelaPosicionada -f $inst.Label) -ForegroundColor Green
                Write-Verbose "Janela $($inst.Label): hwnd=$hWndFilho wt-id=$wtWinId"
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

            $proc = Start-Process -FilePath $psExecutable -ArgumentList "-NoExit -EncodedCommand $(ConvertTo-EncodedCommand $cmd)" -PassThru
            if (-not $proc) { Write-Warning "Nao foi possivel abrir a janela $($inst.Label)." }
            else { $processosAdicionais += $proc }
        }
    }

    Write-Host $M.EstabilizacaoCpu -ForegroundColor DarkGray
    # probe curto (era Start-Sleep fixo de 3s): filhos vivos -> segue; teto 10s
    $probeDeadline = (Get-Date).AddSeconds(10)
    do {
        Start-Sleep -Milliseconds 500
        $todosVivos = -not (@($processosAdicionais | Where-Object { $_.HasExited }).Count)
    } while (-not $todosVivos -and (Get-Date) -lt $probeDeadline)
    Write-Verbose "Probe de estabilizacao: todosVivos=$todosVivos"
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
            $switchResult = Invoke-WithSpinner -Message "Criando e ativando branch $targetBranch..." -ScriptBlock {
                $output = git -C $Ctx.mainPath switch -c $Ctx.targetBranch $Ctx.base 2>&1
                [PSCustomObject]@{ Ok = $?; Output = $output }
            } -ArgumentList @{ mainPath = $mainPath; targetBranch = $targetBranch; base = $base }
            if ($switchResult -and $switchResult.Ok) {
                Write-Host ($M.BranchAtiva -f $targetBranch, " (nova)") -ForegroundColor Green
            }
            else {
                Write-Host ($M.BranchTrocarFalha -f $targetBranch) -ForegroundColor Yellow
            }
        }
        elseif (-not $mainInst.WorktreePath) {
            $switchResult = Invoke-WithSpinner -Message "Ativando branch $targetBranch..." -ScriptBlock {
                $output = git -C $Ctx.mainPath switch $Ctx.targetBranch 2>&1
                [PSCustomObject]@{ Ok = $?; Output = $output }
            } -ArgumentList @{ mainPath = $mainPath; targetBranch = $targetBranch }
            if ($switchResult -and $switchResult.Ok) {
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
        # status --porcelain cobre staged+unstaged (diff --quiet perdia staged, DEF-8)
        $diffResult = Invoke-WithSpinner -Message "Verificando estado da working tree..." -ScriptBlock {
            $output = git -C $Ctx.mainPath status --porcelain --untracked-files=no 2>&1
            [PSCustomObject]@{ Ok = ($LASTEXITCODE -eq 0 -and -not (($output | Out-String).Trim())); Output = $output }
        } -ArgumentList @{ mainPath = $mainPath }
        $clean = $diffResult -and $diffResult.Ok
        if ($clean) {
            $pullResult = Invoke-WithSpinner -Message $M.SincronizandoBranch -ScriptBlock {
                $output = git -C $Ctx.mainPath pull --ff-only 2>&1
                [PSCustomObject]@{ Ok = $?; Output = $output }
            } -ArgumentList @{ mainPath = $mainPath }
            if ($pullResult -and $pullResult.Ok) { Write-Host $M.BranchAtualizada -ForegroundColor Green }
            else { Write-Host $M.FastForwardFalha -ForegroundColor Yellow }
        }
        else {
            Write-Host $M.PullIgnorado -ForegroundColor Yellow
        }
    }
}

# Decide entre retomar sessao existente ou iniciar nova
Start-DevinSession

# 8. Finaliza as instancias extras (fallback): WM_CLOSE so nas janelas
# criadas por esta sessao; Stop-Process apenas nos filhos pwsh diretos
if ($processosAdicionais.Count -gt 0 -or $janelasAdicionais.Count -gt 0) {
    Write-Host $M.PrincipalEncerradaTerminais -ForegroundColor Yellow
    foreach ($h in $janelasAdicionais) {
        try { [void][WindowUtil]::PostMessage($h, [WindowUtil]::WM_CLOSE, [IntPtr]::Zero, [IntPtr]::Zero) } catch { Write-Verbose "WM_CLOSE falhou para hwnd $h" }
    }
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

# 5. Limpa worktrees por projeto (gate de sujeira + locks de sessao)
foreach ($proj in $projetos | Where-Object { $_.CreatedWorktrees.Count -gt 0 }) {
    Write-Host ($M.LimpandoWorktrees + " (" + $proj.Path + ")") -ForegroundColor Magenta
    Push-Location -LiteralPath $proj.Path
    try {
        $allRemoved = $true
        foreach ($wt in $proj.CreatedWorktrees) {
            if (-not (Remove-WorktreeSafe -RepoPath $proj.Path -WorktreePath $wt)) { $allRemoved = $false }
        }
    }
    finally { Pop-Location }
    if ($allRemoved -and $proj.WorktreesRoot -and (Test-Path -LiteralPath $proj.WorktreesRoot)) {
        Remove-DirRobust $proj.WorktreesRoot
    }
    Write-Host $M.WorktreesRemovidos -ForegroundColor Green
}

# Restaura a branch original em todo projeto cujo dir real teve switch (1 ou N instancias)
Write-Verbose "Restore: $($projetos.Count) projeto(s) para revisar"
Restore-OriginalBranches -Projetos $projetos

# Deleta branches criadas nesta execucao (merged-only), apos o restore
Remove-CreatedBranches -Projetos $projetos

# Remove o marcador de sessao desta execucao (se o root sobreviveu)
foreach ($proj in $projetos | Where-Object { $_.WorktreesRoot }) {
    Remove-Item -LiteralPath (Join-Path $proj.WorktreesRoot ".session-$PID") -Force -ErrorAction SilentlyContinue
}

# 8. Restora a janela principal ao tamanho/posicao originais
if ($windowUtilAvailable) {
    [WindowUtil]::SetWindowPos($hwndMain, [IntPtr]::Zero, [int]$origX, [int]$origY, [int]$origW, [int]$origH, 0x0040) | Out-Null
    Write-Host $M.TerminalRestaurado -ForegroundColor Cyan
}

# 2. Retorna ao diretorio original
Set-Location -LiteralPath $diretorioOriginal
Write-Host ($M.RetornandoDiretorio -f $diretorioOriginal.Path) -ForegroundColor Gray

# 9. Sinaliza conclusao para os paineis extras (libera o loop de espera)
if ($numInstancias -gt 1 -and $doneFlag) {
    New-Item -ItemType File -Path $doneFlag -Force | Out-Null
}

# Limpa o cache compartilhado de 'devin ls'
if ($sessionsFile) {
    Remove-Item -LiteralPath $sessionsFile -Force -ErrorAction SilentlyContinue
    if ($env:DEVIN_N_SESSIONS_FILE -eq $sessionsFile) { $env:DEVIN_N_SESSIONS_FILE = $null }
}
