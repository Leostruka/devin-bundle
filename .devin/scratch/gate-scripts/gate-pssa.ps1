$files = 'devin-N.ps1', 'devin-session-launcher.ps1'
$results = foreach ($f in $files) { Invoke-ScriptAnalyzer -Path (Join-Path $PSScriptRoot "..\..\$f") -Severity Error }
$results | Format-Table RuleName, Line, Message -AutoSize | Out-String | Write-Host
"ERRORS: $(@($results).Count)"
