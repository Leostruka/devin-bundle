# devin-session-launcher.ps1
# Decide entre iniciar uma nova sessao do Devin ou retomar uma existente
# via menu interativo full-terminal (sem Out-ConsoleGridView).

function Show-TerminalList {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [array]$Items,
        [string]$Title = 'Selecione',
        [scriptblock]$ToString = { param($x) $x.ToString() }
    )

    if ($Items.Count -eq 0) { return $null }

    # Se o console nao for interativo (redirecionado), usa Read-Host numerado.
    if ([Console]::IsInputRedirected -or [Console]::IsOutputRedirected) {
        Write-Host $Title -ForegroundColor Cyan
        for ($i = 0; $i -lt $Items.Count; $i++) {
            Write-Host "  [$($i+1)] $((&$ToString $Items[$i]))" -ForegroundColor White
        }
        $choice = Read-Host "Digite o numero (Enter para cancelar)"
        if ([string]::IsNullOrWhiteSpace($choice)) { return $null }
        if (-not [int]::TryParse($choice, [ref]$null)) { return $null }
        $idx = [int]$choice - 1
        if ($idx -lt 0 -or $idx -ge $Items.Count) { return $null }
        return $Items[$idx]
    }

    $cursorWasVisible = [Console]::CursorVisible
    [Console]::CursorVisible = $false
    $selected = 0

    try {
        while ($true) {
            Clear-Host
            Write-Host $Title -ForegroundColor Cyan
            Write-Host "(Setas para navegar, Enter para selecionar, Esc para cancelar)`n" -ForegroundColor DarkGray

            $winHeight = [Console]::WindowHeight
            $windowSize = if ($winHeight -gt 5) { $winHeight - 5 } else { 20 }

            $start = 0
            if ($Items.Count -gt $windowSize) {
                $half = [Math]::Floor($windowSize / 2)
                $start = [Math]::Max(0, [Math]::Min($selected - $half, $Items.Count - $windowSize))
            }
            $end = [Math]::Min($Items.Count - 1, $start + $windowSize - 1)

            for ($i = $start; $i -le $end; $i++) {
                $label = &$ToString $Items[$i]
                $prefix = if ($i -eq $selected) { '>' } else { ' ' }
                $color = if ($i -eq $selected) { 'Yellow' } else { 'White' }
                Write-Host " $prefix [$($i+1)] $label" -ForegroundColor $color
            }

            $key = [Console]::ReadKey($true).Key
            switch ($key) {
                'UpArrow' { if ($selected -gt 0) { $selected-- } }
                'DownArrow' { if ($selected -lt ($Items.Count - 1)) { $selected++ } }
                'Home' { $selected = 0 }
                'End' { $selected = $Items.Count - 1 }
                'PageUp' { $selected = [Math]::Max(0, $selected - $windowSize) }
                'PageDown' { $selected = [Math]::Min($Items.Count - 1, $selected + $windowSize) }
                'Enter' { return $Items[$selected] }
                'Escape' { return $null }
            }
        }
    }
    finally {
        [Console]::CursorVisible = $cursorWasVisible
    }
}

function Start-DevinSession {
    $devinCmd = Get-Command devin -ErrorAction SilentlyContinue
    if (-not $devinCmd) {
        Write-Host "Aviso: comando 'devin' nao encontrado no PATH. Iniciando nova sessao diretamente nao e possivel." -ForegroundColor Red
        return
    }

    $allOutput = & $devinCmd ls --format json 2>&1
    $stderr = $allOutput | Where-Object { $_ -is [System.Management.Automation.ErrorRecord] } | ForEach-Object { $_.ToString() }
    $sessionsJson = $allOutput | Where-Object { $_ -is [string] } | Out-String
    $devinLsOk = $LASTEXITCODE -eq 0

    if (-not $devinLsOk) {
        if ($stderr) { Write-Host "Aviso: nao foi possivel listar sessoes: $stderr" -ForegroundColor Yellow }
        else { Write-Host "Aviso: nao foi possivel listar sessoes. Iniciando nova sessao..." -ForegroundColor Yellow }
        & $devinCmd
        return
    }

    $sessions = $sessionsJson | ConvertFrom-Json -ErrorAction SilentlyContinue
    if (-not $sessions -or $sessions.Count -eq 0) {
        Write-Host "Nenhuma sessao encontrada. Iniciando nova..." -ForegroundColor Cyan
        & $devinCmd
        return
    }

    $choices = [System.Collections.ArrayList]::new()
    [void]$choices.Add([PSCustomObject]@{
        Name = '[Nova sessao]'
        Id = ''
    })

    foreach ($s in $sessions) {
        [void]$choices.Add([PSCustomObject]@{
            Name = "$($s.short_id) - $($s.title) ($($s.last_activity_ago))"
            Id = $s.id
        })
    }

    $selected = Show-TerminalList -Items $choices -Title "Sessoes encontradas - escolha uma ou inicie nova" -ToString { param($x) $x.Name }

    if ($null -eq $selected) {
        Write-Host "Selecao cancelada. Nenhuma sessao sera iniciada." -ForegroundColor DarkGray
        return
    }

    if ([string]::IsNullOrWhiteSpace($selected.Id)) {
        Write-Host "Iniciando nova sessao..." -ForegroundColor Cyan
        & $devinCmd
    }
    else {
        Write-Host "Retomando sessao $($selected.Id)..." -ForegroundColor Cyan
        & $devinCmd -r $selected.Id
    }
}
