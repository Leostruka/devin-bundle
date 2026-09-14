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
    $lastFilterText = $null
    $filtered = $null
    $showHelp = $false
    $firstDraw = $true
    $needsRedraw = $true
    $lastTotalLines = 0
    $lastW = [Console]::WindowWidth
    $lastH = [Console]::WindowHeight

    try {
        while ($true) {
            if ($null -eq $filtered -or $filterText -ne $lastFilterText) {
                $filtered = @($Items | Where-Object { Test-FuzzyMatch -Text (Get-Label $_) -Query $filterText })
                $lastFilterText = $filterText
                if ($selected -ge $filtered.Count) { $selected = [Math]::Max(0, $filtered.Count - 1) }
            }

            $w = Get-TuiWidth
            $winHeight = [Console]::WindowHeight
            if ($w -ne $lastW -or $winHeight -ne $lastH) {
                $lastW = $w
                $lastH = $winHeight
                $firstDraw = $true
                $needsRedraw = $true
            }

            if (-not $needsRedraw) {
                if ([Console]::KeyAvailable) {
                    $keyInfo = [Console]::ReadKey($true)
                    $key = $keyInfo.Key
                    $char = $keyInfo.KeyChar
                }
                else {
                    [System.Threading.Thread]::Sleep(50)
                    continue
                }
            }
            else {
                $key = $null
                $char = $null
            }

            if ($null -ne $key) {
                if ($char -eq '?' -or $key -in @('Oem2','OemQuestion')) {
                    $showHelp = -not $showHelp
                    $needsRedraw = $true
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
                    $needsRedraw = $true
                    continue
                }

                if ([string]::IsNullOrEmpty($filterText) -and $Items.Count -le 9 -and $char -eq '0' -and $filtered.Count -gt 0) {
                    return $filtered[0]
                }

                if ($char -ge ' ' -and -not [char]::IsControl($char)) {
                    $filterText += $char
                    $selected = 0
                    $needsRedraw = $true
                    continue
                }

                # Drena e agrega eventos de navegacao repetidos no buffer
                $navDelta = 0
                $jumpHome = $false
                $jumpEnd = $false
                $drainKey = $key
                $drainChar = $char
                $lastKeyInfo = $keyInfo
                $drain = $true
                while ($drain) {
                    switch ($drainKey) {
                        'UpArrow' { $navDelta-- }
                        'DownArrow' { $navDelta++ }
                        'PageUp' { $navDelta -= $windowSize }
                        'PageDown' { $navDelta += $windowSize }
                        'Home' { $jumpHome = $true; $jumpEnd = $false; $navDelta = 0 }
                        'End' { $jumpEnd = $true; $jumpHome = $false; $navDelta = 0 }
                        default { $drain = $false }
                    }
                    if ($drain -and [Console]::KeyAvailable) {
                        $nextInfo = [Console]::ReadKey($true)
                        $drainKey = $nextInfo.Key
                        $drainChar = $nextInfo.KeyChar
                        $lastKeyInfo = $nextInfo
                    }
                    else {
                        $drain = $false
                    }
                }

                if ($jumpHome) {
                    $selected = 0
                }
                elseif ($jumpEnd) {
                    $selected = [Math]::Max(0, $filtered.Count - 1)
                }
                elseif ($navDelta -ne 0) {
                    $selected = [Math]::Max(0, [Math]::Min($filtered.Count - 1, $selected + $navDelta))
                }

                if ($drainChar -ge ' ' -and -not [char]::IsControl($drainChar)) {
                    $filterText += $drainChar
                    $selected = 0
                    $needsRedraw = $true
                    continue
                }

                switch ($drainKey) {
                    'Home' { $selected = 0 }
                    'End' { $selected = [Math]::Max(0, $filtered.Count - 1) }
                    'Backspace' { if ($filterText.Length -gt 0) { $filterText = $filterText.Substring(0, $filterText.Length - 1); $selected = 0 } }
                    'Delete' { $filterText = ''; $selected = 0 }
                    'Enter' { if ($filtered.Count -gt 0) { return $filtered[$selected] } }
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
                        if ($lastKeyInfo.Modifiers -band [ConsoleModifiers]::Control -and $OnCtrlL) {
                            $result = &$OnCtrlL
                            if ($null -ne $result) { return $result }
                        }
                    }
                    'C' {
                        if ($lastKeyInfo.Modifiers -band [ConsoleModifiers]::Control) {
                            return $null
                        }
                    }
                }
                $needsRedraw = $true
                continue
            }

            $needsRedraw = $false

            $inner = $w - 4

            $reserved = 10
            if ($Subtitle) { $reserved++ }
            if ($showHelp) { $reserved++ }
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

            $totalLines = 1 + 1 + 1 + $scrollLines + $listLines + 1 + 1 + 1
            if ($Subtitle) { $totalLines++ }
            if ($showHelp) { $totalLines++ }
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
            if ($lastTotalLines -gt $totalLines -and $totalLines -lt [Console]::WindowHeight) {
                $maxLine = [Math]::Min($lastTotalLines, [Console]::WindowHeight)
                for ($line = $totalLines; $line -lt $maxLine; $line++) {
                    [Console]::SetCursorPosition(0, $line)
                    Write-Host -NoNewline (' ' * $w)
                    Write-Host
                }
                [Console]::SetCursorPosition(0, 0)
            }
            $lastTotalLines = $totalLines
        }
    }
    finally {
        [Console]::CursorVisible = $cursorWasVisible
        [Console]::TreatControlCAsInput = $oldTreatCtrlC
    }
}


function Get-PathSuggestions {
    [CmdletBinding()]
    param([string]$Text)

    $result = @{
        Suggestions = @()
        Ghost = ''
    }

    if ([string]::IsNullOrWhiteSpace($Text)) { return $result }

    $dir = ''
    $prefix = ''
    if ($Text -match '^(.*[\\/:])([^\\/:]*)$') {
        $dir = $Matches[1]
        $prefix = $Matches[2]
    }
    else {
        $dir = '.'
        $prefix = $Text
    }

    $resolved = $null
    if ($dir -eq '.') {
        if ($prefix -match '^[a-zA-Z]:?$') {
            $drives = [System.IO.DriveInfo]::GetDrives() | Where-Object { $_.Name -like "$prefix*" }
            $result.Suggestions = @($drives | ForEach-Object { $_.Name })
            return $result
        }
    }

    try { $resolved = Resolve-Path -LiteralPath $dir -ErrorAction SilentlyContinue } catch {}
    if (-not $resolved) { return $result }

    $items = Get-ChildItem -LiteralPath $resolved.ProviderPath -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "$prefix*" } |
        Sort-Object { $_.PSIsContainer -eq $false }, { $_.Name }

    if ($items) {
        $result.Suggestions = @($items | ForEach-Object { $_.FullName })
        $names = @($items | ForEach-Object { $_.Name })

        $commonName = ''
        $first = $names[0]
        for ($i = 0; $i -lt $first.Length; $i++) {
            $c = $first[$i]
            $allMatch = $true
            foreach ($n in $names) {
                if ($i -ge $n.Length -or $n[$i] -ne $c) { $allMatch = $false; break }
            }
            if ($allMatch) { $commonName += $c } else { break }
        }

        if ($commonName.Length -gt $prefix.Length) {
            $result.Ghost = $commonName.Substring($prefix.Length)
        }
        elseif ($items.Count -eq 1 -and $items[0].PSIsContainer) {
            $result.Ghost = '\\'
        }
    }

    return $result
}

function Read-EditableLine {
    [CmdletBinding()]
    param(
        [string]$Initial = '',
        [switch]$PathCompletion
    )

    if ([Console]::IsInputRedirected) { return $null }

    $old = [Console]::CursorVisible
    [Console]::CursorVisible = $true
    $startLeft = [Console]::CursorLeft
    $startTop = [Console]::CursorTop
    $sb = [System.Text.StringBuilder]::new($Initial)
    $pos = $Initial.Length

    $suggestions = @()
    $ghost = ''
    $selectedIndex = -1
    $maxSuggestionLines = [Math]::Max(1, [Console]::WindowHeight - $startTop - 3)

    function Get-MaxSuggestionLines {
        return [Math]::Max(0, [Math]::Min($maxSuggestionLines, [Console]::WindowHeight - $startTop - 1))
    }

    function Update-Display {
        $w = [Console]::WindowWidth
        $h = [Console]::WindowHeight
        $text = $sb.ToString()
        $maxLines = Get-MaxSuggestionLines

        [Console]::SetCursorPosition($startLeft, $startTop)
        [Console]::Write($text)
        $pad = $w - $startLeft - $text.Length
        if ($pad -gt 0) { [Console]::Write(' ' * $pad) }

        if ($PathCompletion -and $pos -eq $text.Length -and $ghost) {
            $ghostLeft = $startLeft + $pos
            if ($ghostLeft -lt $w) {
                [Console]::SetCursorPosition($ghostLeft, $startTop)
                $oldFg = [Console]::ForegroundColor
                [Console]::ForegroundColor = [ConsoleColor]::DarkGray
                $gh = $ghost
                $maxGhost = $w - $ghostLeft
                if ($gh.Length -gt $maxGhost) { $gh = $gh.Substring(0, $maxGhost) }
                [Console]::Write($gh)
                [Console]::ForegroundColor = $oldFg
                $pad = $w - $ghostLeft - $gh.Length
                if ($pad -gt 0) { [Console]::Write(' ' * $pad) }
            }
        }

        $lastSep = $text.LastIndexOf('\')
        if ($lastSep -lt 0) { $lastSep = $text.LastIndexOf('/') }
        $listLeft = $startLeft
        if ($lastSep -ge 0) { $listLeft = $startLeft + $lastSep + 1 }

        for ($i = 1; $i -le $maxLines + 1; $i++) {
            $top = $startTop + $i
            if ($top -ge $h) { break }
            [Console]::SetCursorPosition($startLeft, $top)
            [Console]::Write(' ' * ($w - $startLeft))
        }

        if ($PathCompletion) {
            $suggestions = @($suggestions)
            $oldFg = [Console]::ForegroundColor
            for ($i = 0; $i -lt [Math]::Min($suggestions.Count, $maxLines); $i++) {
                $top = $startTop + 1 + $i
                if ($top -ge $h) { break }
                [Console]::SetCursorPosition($listLeft, $top)
                if ($i -eq $selectedIndex) {
                    [Console]::ForegroundColor = [ConsoleColor]::White
                } else {
                    [Console]::ForegroundColor = [ConsoleColor]::DarkGray
                }
                $sug = $suggestions[$i]
                $name = $sug
                try { $name = Split-Path -Leaf -Path $sug } catch {}
                if ([string]::IsNullOrEmpty($name)) { $name = [string]$sug }
                if ($name.Length -gt ($w - $listLeft)) { $name = $name.Substring(0, $w - $listLeft) }
                [Console]::Write($name)
                [Console]::ForegroundColor = $oldFg
                $pad = $w - $listLeft - $name.Length
                if ($pad -gt 0) { [Console]::Write(' ' * $pad) }
            }
            if ($suggestions.Count -gt $maxLines) {
                $top = $startTop + $maxLines
                if ($top -lt $h) {
                    [Console]::SetCursorPosition($listLeft, $top)
                    if ($selectedIndex -ge $maxLines) {
                        [Console]::ForegroundColor = [ConsoleColor]::White
                    } else {
                        [Console]::ForegroundColor = [ConsoleColor]::DarkGray
                    }
                    [Console]::Write('...')
                    [Console]::ForegroundColor = $oldFg
                    $pad = $w - $listLeft - 3
                    if ($pad -gt 0) { [Console]::Write(' ' * $pad) }
                }
            }
            else {
                $top = $startTop + 1 + $i
                for (; $i -le $maxLines + 1; $i++) {
                    if ($top -ge $h) { break }
                    [Console]::SetCursorPosition($startLeft, $top)
                    [Console]::Write(' ' * ($w - $startLeft))
                    $top++
                }
            }
            [Console]::ForegroundColor = $oldFg
        }

        [Console]::SetCursorPosition($startLeft + $pos, $startTop)
    }

    function Get-CurrentState {
        $info = Get-PathSuggestions -Text ($sb.ToString())
        Set-Variable -Name 'suggestions' -Value ([array]$info.Suggestions) -Scope 1
        Set-Variable -Name 'ghost' -Value ([string]$info.Ghost) -Scope 1
    }

    function Clear-Suggestions {
        $w = [Console]::WindowWidth
        $h = [Console]::WindowHeight
        $maxLines = Get-MaxSuggestionLines
        for ($i = 1; $i -le $maxLines + 1; $i++) {
            $top = $startTop + $i
            if ($top -ge $h) { break }
            [Console]::SetCursorPosition($startLeft, $top)
            [Console]::Write(' ' * ($w - $startLeft))
        }
    }

    if ($PathCompletion) { Get-CurrentState }
    Update-Display

    try {
        while ($true) {
            $text = $sb.ToString()
            $key = [Console]::ReadKey($true)

            switch ($key.Key) {
                'Enter' {
                    Clear-Suggestions
                    if ($selectedIndex -ge 0 -and $suggestions.Count -gt $selectedIndex) {
                        return $suggestions[$selectedIndex]
                    }
                    return $sb.ToString()
                }
                'Escape' {
                    Clear-Suggestions
                    return $null
                }
                'Backspace' {
                    if ($pos -gt 0) {
                        $sb.Remove($pos - 1, 1) | Out-Null
                        $pos--
                    }
                    $selectedIndex = -1
                }
                'Delete' {
                    if ($pos -lt $sb.Length) {
                        $sb.Remove($pos, 1) | Out-Null
                    }
                    $selectedIndex = -1
                }
                'LeftArrow' { if ($pos -gt 0) { $pos-- } }
                'RightArrow' {
                    if ($PathCompletion -and $pos -eq $text.Length -and $ghost) {
                        $sb.Insert($pos, $ghost) | Out-Null
                        $pos += $ghost.Length
                    }
                    elseif ($pos -lt $sb.Length) {
                        $pos++
                    }
                    $selectedIndex = -1
                }
                'UpArrow' {
                    if ($selectedIndex -gt 0) {
                        $selectedIndex--
                    } elseif ($selectedIndex -eq 0) {
                        $selectedIndex = -1
                    } else {
                        $suggestions = @($suggestions)
                        $selectedIndex = $suggestions.Count - 1
                    }
                }
                'DownArrow' {
                    $suggestions = @($suggestions)
                    if ($selectedIndex -lt ($suggestions.Count - 1)) {
                        $selectedIndex++
                    } else {
                        $selectedIndex = -1
                    }
                }
                'Home' { $pos = 0 }
                'End' { $pos = $sb.Length }
                'Tab' {
                    if ($PathCompletion -and $pos -eq $text.Length -and $ghost) {
                        $sb.Insert($pos, $ghost) | Out-Null
                        $pos += $ghost.Length
                    }
                    $selectedIndex = -1
                }
                default {
                    if ($key.KeyChar -ge ' ' -and -not [char]::IsControl($key.KeyChar)) {
                        $sb.Insert($pos, $key.KeyChar) | Out-Null
                        $pos++
                    }
                    $selectedIndex = -1
                }
            }

            if ($PathCompletion) { Get-CurrentState }
            Update-Display
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

    $Message = ($Message -replace '[\r\n]+', ' ').Trim()
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
        $Instances | Select-Object Label, @{N='Projeto';E={$_.Project.Path}}, Branch, @{N='Tipo';E={if (-not $_.Project.IsGitRepo) { 'sem git' } elseif ($_.BranchInfo -and $_.BranchInfo.Type) { $_.BranchInfo.Type } else { '-' }}}, @{N='Posicao';E={if ($_.Position) { $_.Position } else { '-' }}} | Format-Table -AutoSize | Out-String | Write-Host
        return $true
    }

    $old = [Console]::CursorVisible
    [Console]::CursorVisible = $false
    $lastW = [Console]::WindowWidth
    $lastH = [Console]::WindowHeight
    $needsRedraw = $true

    try {
        while ($true) {
            $w = Get-TuiWidth
            $winHeight = [Console]::WindowHeight
            if ($w -ne $lastW -or $winHeight -ne $lastH) {
                $lastW = $w
                $lastH = $winHeight
                $needsRedraw = $true
            }

            if ($needsRedraw) {
                $needsRedraw = $false
                $border = 'Cyan'

                $rows = $Instances | ForEach-Object {
                    $proj = $_.Project.Path
                    $maxProj = [Math]::Max(10, $w - 70)
                    if ($proj.Length -gt $maxProj) { $proj = '...' + $proj.Substring($proj.Length - ($maxProj - 3)) }
                    [PSCustomObject]@{
                        Label = $_.Label
                        Projeto = $proj
                        Branch = if ($_.Branch) { $_.Branch } else { '-' }
                        Tipo = if (-not $_.Project.IsGitRepo) { 'sem git' } elseif ($_.BranchInfo -and $_.BranchInfo.Type) { $_.BranchInfo.Type } else { '-' }
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
                $boxW = [Math]::Max(20, [Math]::Min($w, $tableWidth + 4))
                $inner = $boxW - 4

                $header = foreach ($c in $col) { Cell $c.Name $c.W }
                $headerLine = '│' + ($header -join '│') + '│'

                Clear-Host

                Write-Host ('┌' + ('─' * ($boxW - 2)) + '┐') -ForegroundColor $border
                $title = 'Resumo da configuracao — Enter inicia · Esc reconfigurar'
                if ($title.Length -gt $inner) { $title = $title.Substring(0, $inner) }
                $title = $title.PadRight($inner)
                Write-Host -NoNewline '│ ' -ForegroundColor $border
                Write-Host -NoNewline $title -ForegroundColor 'Cyan'
                Write-Host ' │' -ForegroundColor $border

                Write-Host ('├' + ('─' * ($boxW - 2)) + '┤') -ForegroundColor $border

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

                $projetosUnicos = @($rows | Select-Object -Property Projeto -Unique).Count
                $footer = "Total: $($Instances.Count) instancia(s) em $projetosUnicos projeto(s)"
                if ($footer.Length -gt $inner) { $footer = $footer.Substring(0, $inner) }
                $footer = $footer.PadRight($inner)
                Write-Host ('├' + ('─' * ($boxW - 2)) + '┤') -ForegroundColor $border
                Write-Host -NoNewline '│ ' -ForegroundColor $border
                Write-Host -NoNewline $footer -ForegroundColor 'Cyan'
                Write-Host ' │' -ForegroundColor $border
                Write-Host ('└' + ('─' * ($boxW - 2)) + '┘') -ForegroundColor $border
            }

            if ([Console]::KeyAvailable) {
                $key = [Console]::ReadKey($true)
                if ($key.Key -eq 'Enter') { return $true }
                if ($key.Key -eq 'Escape') { return $false }
            }
            else {
                [System.Threading.Thread]::Sleep(50)
            }
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
