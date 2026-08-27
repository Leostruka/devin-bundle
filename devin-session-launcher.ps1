# devin-session-launcher.ps1
# Decide entre iniciar uma nova sessao do Devin ou retomar uma existente
# via Out-ConsoleGridView (mesmo grid usado nas selecoes de pasta/branch).

Import-Module Microsoft.PowerShell.ConsoleGuiTools -ErrorAction Stop

function Start-DevinSession {
    $sessionsJson = devin ls --format json 2>$null
    $sessions = $sessionsJson | ConvertFrom-Json -ErrorAction SilentlyContinue
    if ($LASTEXITCODE -ne 0 -or -not $sessions -or $sessions.Count -eq 0) {
        Write-Host "Nenhuma sessao encontrada. Iniciando nova..." -ForegroundColor Cyan
        devin
        return
    }

    $choices = [System.Collections.ArrayList]::new()
    [void]$choices.Add([PSCustomObject]@{
        Name = '[Nova sessao]'
        Id = ''
        Titulo = ''
        Atividade = ''
    })

    foreach ($s in $sessions) {
        [void]$choices.Add([PSCustomObject]@{
            Name = "$($s.short_id) - $($s.title)"
            Id = $s.id
            Titulo = $s.title
            Atividade = $s.last_activity_ago
        })
    }

    $selected = $choices |
        Out-ConsoleGridView -Title "Sessoes encontradas - escolha uma ou inicie nova" -OutputMode Single

    if (-not $selected -or [string]::IsNullOrWhiteSpace($selected.Id)) {
        Write-Host "Iniciando nova sessao..." -ForegroundColor Cyan
        devin
    }
    else {
        Write-Host "Retomando sessao $($selected.Id)..." -ForegroundColor Cyan
        devin -r $selected.Id
    }
}
