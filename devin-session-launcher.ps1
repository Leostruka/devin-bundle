# devin-session-launcher.ps1
# Utilitarios de UI full-terminal para o launcher do Devin.
# Sem caixas de dialogo externas; todo o fluxo acontece no console.

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Get-TuiWidth {
    $w = [Console]::WindowWidth
    if ($w -le 0) { $w = 120 }
    return $w
}

function Show-TerminalList {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [array]$Items,
        [string]$Title = 'Selecione',
        [string]$Subtitle = '',
        [scriptblock]$ToString = { param($x) $x.ToString() },
        [int]$DefaultIndex = 0,
        [scriptblock]$OnCtrlL = $null
    )

    function Get-Label {
        param($Item)
        $label = &$ToString $Item
        if ($null -eq $label) { return '' }
        return "$label"
    }

    function Test-FuzzyMatch {
        param([string]$Text, [string]$Query)
        if ([string]::IsNullOrEmpty($Query)) { return $true }
        $t = $Text.ToLowerInvariant()
        $q = $Query.ToLowerInvariant()
        $pos = -1
        foreach ($c in $q.ToCharArray()) {
            $pos = $t.IndexOf($c, $pos + 1)
            if ($pos -lt 0) { return $false }
        }
        return $true
    }

    # Fallback nao interativo: listagem simples com filtro e numeros
    if ([Console]::IsInputRedirected -or [Console]::IsOutputRedirected) {
        Write-Host $Title -ForegroundColor Cyan
        if ($Subtitle) { Write-Host $Subtitle -ForegroundColor DarkGray }
        $filter = Read-Host "Filtro (Enter para mostrar tudo)"
        $filtered = @($Items | Where-Object { Test-FuzzyMatch -Text (Get-Label $_) -Query $filter })
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
    $oldTreatCtrlC = [Console]::TreatControlCAsInput
    [Console]::CursorVisible = $false
    [Console]::TreatControlCAsInput = $true
    $selected = [Math]::Max(0, [Math]::Min($DefaultIndex, $Items.Count - 1))
    $filterText = ''
    $showHelp = $false
    $firstDraw = $true
    $lastTotalLines = 0

    try {
        while ($true) {
            $filtered = @($Items | Where-Object { Test-FuzzyMatch -Text (Get-Label $_) -Query $filterText })
            if ($selected -ge $filtered.Count) { $selected = [Math]::Max(0, $filtered.Count - 1) }

            $w = Get-TuiWidth
            $inner = $w - 4

            $winHeight = [Console]::WindowHeight
            $reserved = 10 + (if ($Subtitle) { 1 } else { 0 }) + (if ($showHelp) { 1 } else { 0 })
            $windowSize = if ($winHeight -gt $reserved) { $winHeight - $reserved } else { 10 }

            $start = 0
            if ($filtered.Count -gt $windowSize) {
                $half = [Math]::Floor($windowSize / 2)
                $start = [Math]::Max(0, [Math]::Min($selected - $half, $filtered.Count - $windowSize))
            }
            $end = [Math]::Min($filtered.Count - 1, $start + $windowSize - 1)

            $listLines = if ($filtered.Count -eq 0) { 1 } else { $end - $start + 1 }
            $scrollLines = 0
            if ($filtered.Count -gt $windowSize) {
                if ($start -gt 0) { $scrollLines++ }
                if ($end -lt $filtered.Count - 1) { $scrollLines++ }
            }

            $totalLines = 1 + 1 + (if ($Subtitle) { 1 } else { 0 }) + 1 + (if ($showHelp) { 1 } else { 0 }) + $scrollLines + $listLines + 1 + 1 + 1
            # topo, titulo, subtitulo?, separador, ajuda?, scrolls, lista, separador, rodape, base

            if ($firstDraw) {
                Clear-Host
                $firstDraw = $false
            }
            else {
                [Console]::SetCursorPosition(0, 0)
            }

            $border = 'Cyan'

            # Topo
            Write-Host ('┌' + ('─' * ($w - 2)) + '┐') -ForegroundColor $border

            # Titulo
            $t = $Title
            if ($t.Length -gt $inner) { $t = $t.Substring(0, $inner) }
            $t = $t.PadRight($inner)
            Write-Host -NoNewline '│ ' -ForegroundColor $border
            Write-Host -NoNewline $t -ForegroundColor 'Cyan'
            Write-Host ' │' -ForegroundColor $border

            # Subtitulo (breadcrumb)
            if ($Subtitle) {
                $s = $Subtitle
                if ($s.Length -gt $inner) { $s = $s.Substring(0, $inner) }
                $s = $s.PadRight($inner)
                Write-Host -NoNewline '│ ' -ForegroundColor $border
                Write-Host -NoNewline $s -ForegroundColor 'DarkGray'
                Write-Host ' │' -ForegroundColor $border
            }

            # Separador cabecalho
            Write-Host ('├' + ('─' * ($w - 2)) + '┤') -ForegroundColor $border

            # Ajuda
            if ($showHelp) {
                $h = if ($OnCtrlL) {
                    "Setas = mover  Enter = selecionar  Esc = voltar  Ctrl+L = editar caminho  Backspace/Delete = filtro  ? = ajuda  1-9 = atalho"
                } else {
                    "Setas = mover  Enter = selecionar  Esc = voltar  Backspace/Delete = filtro  ? = ajuda  1-9 = atalho"
                }
                if ($h.Length -gt $inner) { $h = $h.Substring(0, $inner) }
                $h = $h.PadRight($inner)
                Write-Host -NoNewline '│ ' -ForegroundColor $border
                Write-Host -NoNewline $h -ForegroundColor 'DarkGray'
                Write-Host ' │' -ForegroundColor $border
            }

            # Scroll para cima
            if ($filtered.Count -gt $windowSize -and $start -gt 0) {
                $u = "^ $($start) anteriores"
                $u = $u.PadRight($inner)
                Write-Host -NoNewline '│ ' -ForegroundColor $border
                Write-Host -NoNewline $u -ForegroundColor 'DarkGray'
                Write-Host ' │' -ForegroundColor $border
            }

            # Lista
            if ($filtered.Count -eq 0) {
                $none = "Nenhum item encontrado."
                $none = $none.PadRight($inner)
                Write-Host -NoNewline '│ ' -ForegroundColor $border
                Write-Host -NoNewline $none -ForegroundColor 'Red'
                Write-Host ' │' -ForegroundColor $border
            }
            else {
                for ($i = $start; $i -le $end; $i++) {
                    $label = Get-Label $filtered[$i]
                    $prefix = if ($i -eq $selected) { '>' } else { ' ' }
                    $fg = if ($i -eq $selected) { 'Yellow' } else { 'White' }
                    $bg = if ($i -eq $selected) { 'DarkBlue' } else { $null }
                    $line = "$prefix [$($i+1)] $label"
                    if ($line.Length -gt $inner) { $line = $line.Substring(0, $inner) }
                    $line = $line.PadRight($inner)

                    Write-Host -NoNewline '│ ' -ForegroundColor $border
                    if ($bg) {
                        Write-Host -NoNewline $line -ForegroundColor $fg -BackgroundColor $bg
                    }
                    else {
                        Write-Host -NoNewline $line -ForegroundColor $fg
                    }
                    Write-Host ' │' -ForegroundColor $border
                }
            }

            # Scroll para baixo
            if ($filtered.Count -gt $windowSize -and $end -lt $filtered.Count - 1) {
                $d = "v $($filtered.Count - $end - 1) seguintes"
                $d = $d.PadRight($inner)
                Write-Host -NoNewline '│ ' -ForegroundColor $border
                Write-Host -NoNewline $d -ForegroundColor 'DarkGray'
                Write-Host ' │' -ForegroundColor $border
            }

            # Separador rodape
            Write-Host ('├' + ('─' * ($w - 2)) + '┤') -ForegroundColor $border

            # Rodape: filtro e atalhos
            $filterDisplay = if ($filterText) { $filterText } else { '' }
            $ctrlLHint = if ($OnCtrlL) { '  Ctrl+L edita caminho' } else { '' }
            $footer = "Filtro: $filterDisplay`_ ($($filtered.Count)/$($Items.Count))  |  Enter seleciona  Esc volta$ctrlLHint  ? ajuda"
            if ($footer.Length -gt $inner) { $footer = $footer.Substring(0, $inner) }
            $footer = $footer.PadRight($inner)
            Write-Host -NoNewline '│ ' -ForegroundColor $border
            Write-Host -NoNewline $footer -ForegroundColor 'Cyan'
            Write-Host ' │' -ForegroundColor $border

            # Base
            Write-Host ('└' + ('─' * ($w - 2)) + '┘') -ForegroundColor $border

            # Limpa linhas anteriores que sobraram
            if ($lastTotalLines -gt $totalLines) {
                for ($line = $totalLines; $line -lt $lastTotalLines; $line++) {
                    [Console]::SetCursorPosition(0, $line)
                    Write-Host -NoNewline (' ' * $w)
                    Write-Host
                }
                [Console]::SetCursorPosition(0, 0)
            }
            $lastTotalLines = $totalLines

            $keyInfo = [Console]::ReadKey($true)
            $key = $keyInfo.Key
            $char = $keyInfo.KeyChar

            if ($char -eq '?' -or $key -in @('Oem2','OemQuestion')) {
                $showHelp = -not $showHelp
                continue
            }

            if ([string]::IsNullOrEmpty($filterText) -and $Items.Count -le 9 -and $char -ge '1' -and $char -le '9') {
                $digitIndex = [int]$char.ToString() - 1
                if ($digitIndex -ge 0 -and $digitIndex -lt $filtered.Count) {
                    return $filtered[$digitIndex]
                }
                if ($char -eq '0') {
                    if ($filtered.Count -gt 0) { return $filtered[0] }
                }
                continue
            }

            if ([string]::IsNullOrEmpty($filterText) -and $Items.Count -le 9 -and $char -eq '0' -and $filtered.Count -gt 0) {
                return $filtered[0]
            }

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
                'L' {
                    if ($keyInfo.Modifiers -band [ConsoleModifiers]::Control -and $OnCtrlL) {
                        $result = &$OnCtrlL
                        if ($null -ne $result) { return $result }
                    }
                }
                'C' {
                    if ($keyInfo.Modifiers -band [ConsoleModifiers]::Control) {
                        return $null
                    }
                }
            }
        }
    }
    finally {
        [Console]::CursorVisible = $cursorWasVisible
        [Console]::TreatControlCAsInput = $oldTreatCtrlC
    }
}

function Read-EditableLine {
    [CmdletBinding()]
    param([string]$Initial = '')

    if ([Console]::IsInputRedirected) { return $null }

    $old = [Console]::CursorVisible
    [Console]::CursorVisible = $true
    $startLeft = [Console]::CursorLeft
    $startTop = [Console]::CursorTop
    $sb = [System.Text.StringBuilder]::new($Initial)
    $pos = $Initial.Length
    [Console]::Write($Initial)

    try {
        while ($true) {
            [Console]::SetCursorPosition($startLeft + $pos, $startTop)
            $key = [Console]::ReadKey($true)

            switch ($key.Key) {
                'Enter' { return $sb.ToString() }
                'Escape' { return $null }
                'Backspace' {
                    if ($pos -gt 0) {
                        $sb.Remove($pos - 1, 1) | Out-Null
                        $pos--
                        [Console]::SetCursorPosition($startLeft, $startTop)
                        [Console]::Write($sb.ToString())
                        $pad = [Console]::WindowWidth - $startLeft - $sb.Length
                        if ($pad -gt 0) { [Console]::Write(' ' * $pad) }
                        [Console]::SetCursorPosition($startLeft + $pos, $startTop)
                    }
                }
                'Delete' {
                    if ($pos -lt $sb.Length) {
                        $sb.Remove($pos, 1) | Out-Null
                        [Console]::SetCursorPosition($startLeft, $startTop)
                        [Console]::Write($sb.ToString())
                        $pad = [Console]::WindowWidth - $startLeft - $sb.Length
                        if ($pad -gt 0) { [Console]::Write(' ' * $pad) }
                        [Console]::SetCursorPosition($startLeft + $pos, $startTop)
                    }
                }
                'LeftArrow' { if ($pos -gt 0) { $pos-- } }
                'RightArrow' { if ($pos -lt $sb.Length) { $pos++ } }
                'Home' { $pos = 0 }
                'End' { $pos = $sb.Length }
                default {
                    if ($key.KeyChar -ge ' ' -and -not [char]::IsControl($key.KeyChar)) {
                        $sb.Insert($pos, $key.KeyChar) | Out-Null
                        $pos++
                        [Console]::SetCursorPosition($startLeft, $startTop)
                        [Console]::Write($sb.ToString())
                        $pad = [Console]::WindowWidth - $startLeft - $sb.Length
                        if ($pad -gt 0) { [Console]::Write(' ' * $pad) }
                        [Console]::SetCursorPosition($startLeft + $pos, $startTop)
                    }
                }
            }
        }
    }
    finally {
        [Console]::CursorVisible = $old
    }
}

function Invoke-WithSpinner {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Message,
        [Parameter(Mandatory)]
        [scriptblock]$ScriptBlock
    )

    $frames = @('⢿','⣻','⣽','⣾','⣷','⣯','⣟','⡿')
    $job = $null
    try {
        $job = Start-Job -ScriptBlock $ScriptBlock
        $i = 0
        while ($job.JobStateInfo.State -in 'NotStarted','Running') {
            Write-Host -NoNewline "`r$($frames[$i % $frames.Count]) $Message" -ForegroundColor Cyan
            Start-Sleep -Milliseconds 80
            $i++
        }
        # Limpa a linha do spinner
        Write-Host -NoNewline "`r"
        Write-Host -NoNewline (' ' * ($Message.Length + 4))
        Write-Host -NoNewline "`r"

        if ($job.JobStateInfo.State -eq 'Failed') {
            $err = $job.ChildJobs[0].JobStateInfo.Reason
            if (-not $err) { $err = "Falha na operacao." }
            throw $err
        }

        $result = Receive-Job -Job $job
        return $result
    }
    finally {
        if ($job) {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
            Remove-Job -Job $job -ErrorAction SilentlyContinue
        }
    }
}

function Show-Summary {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [array]$Instances
    )

    if ([Console]::IsInputRedirected -or [Console]::IsOutputRedirected) {
        Write-Host 'Resumo da configuracao (modo nao interativo):' -ForegroundColor Cyan
        $Instances | Select-Object Label, @{N='Projeto';E={$_.Project.Path}}, Branch, @{N='Tipo';E={if ($_.BranchInfo -and $_.BranchInfo.Type) { $_.BranchInfo.Type } else { '-' }}}, @{N='Posicao';E={if ($_.Position) { $_.Position } else { '-' }}} | Format-Table -AutoSize | Out-String | Write-Host
        return $true
    }

    $w = Get-TuiWidth
    $inner = $w - 4
    $border = 'Cyan'

    $rows = $Instances | ForEach-Object {
        $proj = $_.Project.Path
        $maxProj = [Math]::Max(10, $w - 70)
        if ($proj.Length -gt $maxProj) { $proj = '...' + $proj.Substring($proj.Length - ($maxProj - 3)) }
        [PSCustomObject]@{
            Label = $_.Label
            Projeto = $proj
            Branch = if ($_.Branch) { $_.Branch } else { '-' }
            Tipo = if ($_.BranchInfo -and $_.BranchInfo.Type) { $_.BranchInfo.Type } else { '-' }
            Posicao = if ($_.Position) { $_.Position } else { '-' }
        }
    }

    $col = @(
        @{ Name='Ins'; W=[Math]::Max(3,($rows.Label | Measure-Object -Maximum Length).Maximum) }
        @{ Name='Projeto'; W=[Math]::Max(7,($rows.Projeto | Measure-Object -Maximum Length).Maximum) }
        @{ Name='Branch'; W=[Math]::Max(6,($rows.Branch | Measure-Object -Maximum Length).Maximum) }
        @{ Name='Tipo'; W=[Math]::Max(4,($rows.Tipo | Measure-Object -Maximum Length).Maximum) }
        @{ Name='Posicao'; W=[Math]::Max(7,($rows.Posicao | Measure-Object -Maximum Length).Maximum) }
    )

    function Cell($text, $width) { ' ' + $text.PadRight($width) + ' ' }
    function SepLine($left, $mid, $right) {
        $parts = foreach ($c in $col) { '─' * ($c.W + 2) }
        $left + ($parts -join $mid) + $right
    }

    $tableTop = SepLine '┌' '┬' '┐'
    $tableSep = SepLine '├' '┼' '┤'
    $tableBottom = SepLine '└' '┴' '┘'
    $tableWidth = $tableTop.Length

    $header = foreach ($c in $col) { Cell $c.Name $c.W }
    $headerLine = '│' + ($header -join '│') + '│'

    Clear-Host

    # Moldura externa
    Write-Host ('┌' + ('─' * ($w - 2)) + '┐') -ForegroundColor $border
    $title = 'Resumo da configuracao — Enter inicia · Esc reconfigurar'
    if ($title.Length -gt $inner) { $title = $title.Substring(0, $inner) }
    $title = $title.PadRight($inner)
    Write-Host -NoNewline '│ ' -ForegroundColor $border
    Write-Host -NoNewline $title -ForegroundColor 'Cyan'
    Write-Host ' │' -ForegroundColor $border

    Write-Host '├' + ('─' * ($w - 2)) + '┤' -ForegroundColor $border

    # Tabela
    Write-Host -NoNewline '│ ' -ForegroundColor $border
    Write-Host -NoNewline $tableTop -ForegroundColor $border
    Write-Host ' │' -ForegroundColor $border

    Write-Host -NoNewline '│ ' -ForegroundColor $border
    Write-Host -NoNewline $headerLine -ForegroundColor 'White'
    Write-Host ' │' -ForegroundColor $border

    Write-Host -NoNewline '│ ' -ForegroundColor $border
    Write-Host -NoNewline $tableSep -ForegroundColor $border
    Write-Host ' │' -ForegroundColor $border

    foreach ($r in $rows) {
        $cells = @(
            Cell $r.Label $col[0].W
            Cell $r.Projeto $col[1].W
            Cell $r.Branch $col[2].W
            Cell $r.Tipo $col[3].W
            Cell $r.Posicao $col[4].W
        )
        $rowLine = '│' + ($cells -join '│') + '│'
        Write-Host -NoNewline '│ ' -ForegroundColor $border
        Write-Host -NoNewline $rowLine -ForegroundColor 'White'
        Write-Host ' │' -ForegroundColor $border
    }

    Write-Host -NoNewline '│ ' -ForegroundColor $border
    Write-Host -NoNewline $tableBottom -ForegroundColor $border
    Write-Host ' │' -ForegroundColor $border

    # Rodape
    $projetosUnicos = @($rows | Select-Object -Property Projeto -Unique).Count
    $footer = "Total: $($Instances.Count) instancia(s) em $projetosUnicos projeto(s)"
    if ($footer.Length -gt $inner) { $footer = $footer.Substring(0, $inner) }
    $footer = $footer.PadRight($inner)
    Write-Host '├' + ('─' * ($w - 2)) + '┤' -ForegroundColor $border
    Write-Host -NoNewline '│ ' -ForegroundColor $border
    Write-Host -NoNewline $footer -ForegroundColor 'Cyan'
    Write-Host ' │' -ForegroundColor $border
    Write-Host '└' + ('─' * ($w - 2)) + '┘' -ForegroundColor $border

    $old = [Console]::CursorVisible
    [Console]::CursorVisible = $false
    try {
        while ($true) {
            $key = [Console]::ReadKey($true)
            if ($key.Key -eq 'Enter') { return $true }
            if ($key.Key -eq 'Escape') { return $false }
        }
    }
    finally {
        [Console]::CursorVisible = $old
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
