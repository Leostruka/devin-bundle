# Importa funcoes reais de um .ps1 sem executar o corpo do script (via AST).
# Define em escopo global: chamadores devem setar dependencias via $global:.
# Uso: . .\Import-DevinFunctions.ps1; Import-DevinFunctions -Path ..\devin-N.ps1 -Names @('Foo','Bar')
function Import-DevinFunctions {
    param(
        [Parameter(Mandatory)][string]$Path,
        [string[]]$Names
    )
    $tokens = $null; $errors = $null
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    $ast = [System.Management.Automation.Language.Parser]::ParseFile($resolved, [ref]$tokens, [ref]$errors)
    if ($errors -and $errors.Count -gt 0) {
        throw "Parse errors em ${resolved}: $($errors[0].Message)"
    }
    $funcs = $ast.FindAll({ param($a) $a -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $false)
    foreach ($fd in $funcs) {
        if (-not $Names -or $Names -contains $fd.Name) {
            Set-Item -Path "function:global:$($fd.Name)" -Value $fd.Body.GetScriptBlock()
        }
    }
}
