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

    function Get-Label {
        param($Item)
        $label = &$ToString $Item
        if ($null -eq $label) { return '' }
        return "$label"
    }

    function Write-MenuLine {
        param([string]$Text, [string]$Color = 'White')
        $w = [Console]::WindowWidth
        if ($w -le 0) { $w = 120 }
        $line = $Text
        if ($line.Length -gt $w) { $line = $line.Substring(0, $w) }
        $line = $line.PadRight($w)
        Write-Host -NoNewline $line -ForegroundColor $Color
        Write-Host
    }

    # Se o console nao for interativo (redirecionado), usa filtro + Read-Host numerado.
    if ([Console]::IsInputRedirected -or [Console]::IsOutputRedirected) {
        Write-Host $Title -ForegroundColor Cyan
        $filter = Read-Host "Filtro (Enter para mostrar tudo)"
        $filtered = @($Items | Where-Object { (Get-Label $_).IndexOf($filter, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 })
        if ($filtered.Count -eq 0) { return $null }
        for ($i = 0; $i -lt $filtered.Count; $i++) {
            Write-Host "  [$($i+1)] $(Get-Label $filtered[$i])" -ForegroundColor White
        }
        $choice = Read-Host "Digite o numero (Enter para cancelar)"
        if ([string]::IsNullOrWhiteSpace($choice)) { return $null }
        if (-not [int]::TryParse($choice, [ref]$null)) { return $null }
        $idx = [int]$choice - 1
        if ($idx -lt 0 -or $idx -ge $filtered.Count) { return $null }
        return $filtered[$idx]
    }

    $cursorWasVisible = [Console]::CursorVisible
    [Console]::CursorVisible = $false
    $selected = 0
    $filterText = ''
    $lastTotalLines = 0
    $firstDraw = $true

    try {
        while ($true) {
            $filtered = @($Items | Where-Object { (Get-Label $_).IndexOf($filterText, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 })
            if ($selected -ge $filtered.Count) { $selected = [Math]::Max(0, $filtered.Count - 1) }

            $winHeight = [Console]::WindowHeight
            $windowSize = if ($winHeight -gt 6) { $winHeight - 6 } else { 20 }

            $start = 0
            if ($filtered.Count -gt $windowSize) {
                $half = [Math]::Floor($windowSize / 2)
                $start = [Math]::Max(0, [Math]::Min($selected - $half, $filtered.Count - $windowSize))
            }
            $end = [Math]::Min($filtered.Count - 1, $start + $windowSize - 1)

            $listLines = if ($filtered.Count -eq 0) { 1 } else { $end - $start + 1 }
            $currentTotalLines = 1 + 2 + $listLines + 1 + 1

            if ($firstDraw) {
                Clear-Host
                $firstDraw = $false
            }
            else {
                [Console]::SetCursorPosition(0, 0)
            }

            Write-MenuLine -Text $Title -Color 'Cyan'

            if ($filterText) {
                Write-MenuLine -Text "(Setas/Enter/Esc | digite para filtrar | Backspace apaga | Delete limpa)" -Color 'DarkGray'
            }
            else {
                Write-MenuLine -Text "(Setas para navegar, Enter para selecionar, Esc para cancelar | digite para filtrar)" -Color 'DarkGray'
            }

            Write-MenuLine -Text ''

            if ($filtered.Count -eq 0) {
                Write-MenuLine -Text " Nenhum item encontrado." -Color 'Red'
            }
            else {
                for ($i = $start; $i -le $end; $i++) {
                    $label = Get-Label $filtered[$i]
                    $prefix = if ($i -eq $selected) { '>' } else { ' ' }
                    $color = if ($i -eq $selected) { 'Yellow' } else { 'White' }
                    Write-MenuLine -Text " $prefix [$($i+1)] $label" -Color $color
                }
            }

            Write-MenuLine -Text ''
            Write-MenuLine -Text ("Filtro: $filterText" + '_') -Color 'Cyan'

            if ($lastTotalLines -gt $currentTotalLines) {
                for ($line = $currentTotalLines; $line -lt $lastTotalLines; $line++) {
                    [Console]::SetCursorPosition(0, $line)
                    Write-MenuLine -Text ''
                }
            }
            $lastTotalLines = $currentTotalLines

            $keyInfo = [Console]::ReadKey($true)
            $key = $keyInfo.Key
            $char = $keyInfo.KeyChar

            if ($char -ge ' ' -and -not [char]::IsControl($char)) {
                $filterText += $char
                $selected = 0
                continue
            }

            switch ($key) {
                'UpArrow' { if ($selected -gt 0) { $selected-- } }
                'DownArrow' { if ($selected -lt ($filtered.Count - 1)) { $selected++ } }
                'Home' { $selected = 0 }
                'End' { $selected = [Math]::Max(0, $filtered.Count - 1) }
                'PageUp' { $selected = [Math]::Max(0, $selected - $windowSize) }
                'PageDown' { $selected = [Math]::Min($filtered.Count - 1, $selected + $windowSize) }
                'Backspace' { if ($filterText.Length -gt 0) { $filterText = $filterText.Substring(0, $filterText.Length - 1); $selected = 0 } }
                'Delete' { $filterText = ''; $selected = 0 }
                'Enter' {
                    if ($filtered.Count -gt 0) { return $filtered[$selected] }
                }
                'Escape' {
                    if ($filterText.Length -gt 0) {
                        $filterText = ''
                        $selected = 0
                    }
                    else {
                        return $null
                    }
                }
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
