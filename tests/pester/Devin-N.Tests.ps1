# Pester: importa funcoes REAIS de devin-N.ps1 / devin-session-launcher.ps1 via AST.
# Nao executa o corpo interativo dos scripts.
BeforeAll {
    . (Join-Path $PSScriptRoot 'Import-DevinFunctions.ps1')
    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
    Import-DevinFunctions -Path (Join-Path $repoRoot 'devin-session-launcher.ps1') `
        -Names @('Test-FuzzyMatch', 'Get-DevinSessionData', 'Invoke-WithSpinner', 'Get-PathSuggestions')
    Import-DevinFunctions -Path (Join-Path $repoRoot 'devin-N.ps1') `
        -Names @('Escape-Sq', 'ConvertTo-EncodedCommand', 'Get-InstanceCommand')
}

Describe 'Test-FuzzyMatch (launcher)' {
    It 'query vazia casa tudo' {
        Test-FuzzyMatch -Text 'qualquer' -Query '' | Should -BeTrue
    }
    It 'subsequencia em ordem casa' {
        Test-FuzzyMatch -Text 'abcdef' -Query 'ace' | Should -BeTrue
    }
    It 'fora de ordem nao casa' {
        Test-FuzzyMatch -Text 'abcdef' -Query 'aec' | Should -BeFalse
    }
    It 'case-insensitive' {
        Test-FuzzyMatch -Text 'ProjetoX' -Query 'projetox' | Should -BeTrue
    }
    It 'char ausente nao casa' {
        Test-FuzzyMatch -Text 'abc' -Query 'z' | Should -BeFalse
    }
}

Describe 'Escape-Sq (devin-N)' {
    It 'dobra aspas simples' {
        Escape-Sq "a'b" | Should -Be "a''b"
    }
    It 'null vira string vazia' {
        Escape-Sq $null | Should -Be ''
    }
    It 'texto sem aspa fica igual' {
        Escape-Sq 'plain' | Should -Be 'plain'
    }
}

Describe 'ConvertTo-EncodedCommand (devin-N)' {
    It 'round-trip decodifica para o script original' {
        $script = "Write-Host 'oi'; `$x = 1"
        $enc = ConvertTo-EncodedCommand $script
        [System.Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($enc)) | Should -Be $script
    }
    It 'preserva aspas simples no payload' {
        $script = "Set-Location -LiteralPath 'C:\a''b'"
        $enc = ConvertTo-EncodedCommand $script
        [System.Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($enc)) | Should -Be $script
    }
}

Describe 'Get-InstanceCommand (devin-N)' {
    BeforeAll {
        $script:bundleRoot = "C:\fake'root"
        $script:doneFlag = 'C:\x.done'
        $script:scriptPid = 4242
        $inst = [PSCustomObject]@{
            WorkingDirectory = "C:\proj'ect"
            Branch = "feat/o'neil"
            BaseBranch = 'main'
            WorktreePath = $null
            Label = 'Inst 2'
            Project = [PSCustomObject]@{ IsGitRepo = $true; CurrentBranch = 'main' }
            BranchInfo = [PSCustomObject]@{ Type = 'new' }
        }
        $cmd = Get-InstanceCommand -Inst $inst
    }
    It 'escapa apostrofo no diretorio' {
        $cmd | Should -Match ([regex]::Escape("C:\proj''ect"))
    }
    It 'escapa apostrofo na branch' {
        $cmd | Should -Match ([regex]::Escape("feat/o''neil"))
    }
    It 'escapa apostrofo no bundleRoot' {
        $cmd | Should -Match ([regex]::Escape("C:\fake''root"))
    }
    It 'decodifica via ConvertTo-EncodedCommand sem erro de parse' {
        $enc = ConvertTo-EncodedCommand $cmd
        $decoded = [System.Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($enc))
        $e = $null; $t = $null
        [void][System.Management.Automation.Language.Parser]::ParseInput($decoded, [ref]$t, [ref]$e)
        @($e).Count | Should -Be 0
    }
}

Describe 'Invoke-WithSpinner (launcher, runspace)' {
    It 'retorna valor unico' {
        (Invoke-WithSpinner -Message 't' -ScriptBlock { 42 }) | Should -Be 42
    }
    It 'recebe ArgumentList via $Ctx' {
        (Invoke-WithSpinner -Message 't' -ScriptBlock { $Ctx.v * 2 } -ArgumentList @{ v = 21 }) | Should -Be 42
    }
    It 'retorna hashtable intacta (sem degradacao CliXml)' {
        $r = Invoke-WithSpinner -Message 't' -ScriptBlock { @{ a = @{ b = 1 } } }
        $r | Should -BeOfType [hashtable]
        $r.a.b | Should -Be 1
    }
    It 'retorna null em saida vazia' {
        $r = Invoke-WithSpinner -Message 't' -ScriptBlock { }
        $r | Should -BeNullOrEmpty
    }
    It 'propaga falha do scriptblock' {
        { Invoke-WithSpinner -Message 't' -ScriptBlock { throw 'boom' } } | Should -Throw '*boom*'
    }
}

Describe 'Get-DevinSessionData (launcher)' {
    BeforeEach {
        $script:envBackup = $env:DEVIN_N_SESSIONS_FILE
    }
    AfterEach {
        $env:DEVIN_N_SESSIONS_FILE = $script:envBackup
    }
    It 'le cache fresco sem chamar devin' {
        $f = Join-Path $TestDrive 'sessions.json'
        '[{"id":"abc"}]' | Set-Content -LiteralPath $f
        $env:DEVIN_N_SESSIONS_FILE = $f
        function devin-fake-should-not-run { throw 'nao deveria executar devin' }
        $r = Get-DevinSessionData -DevinCmd (Get-Command devin-fake-should-not-run)
        $r.Ok | Should -BeTrue
        $r.Cached | Should -BeTrue
        $r.Json | Should -Match 'abc'
    }
    It 'chama devin quando cache ausente' {
        $env:DEVIN_N_SESSIONS_FILE = $null
        function global:devin-fake { '[{"id":"xyz"}]'; $global:LASTEXITCODE = 0 }
        $r = Get-DevinSessionData -DevinCmd (Get-Command devin-fake)
        $r.Ok | Should -BeTrue
        $r.Cached | Should -BeFalse
        $r.Json | Should -Match 'xyz'
        Remove-Item function:global:devin-fake
    }
    It 'cache expirado volta a chamar devin' {
        $f = Join-Path $TestDrive 'old.json'
        '[]' | Set-Content -LiteralPath $f
        (Get-Item -LiteralPath $f).LastWriteTime = (Get-Date).AddMinutes(-5)
        $env:DEVIN_N_SESSIONS_FILE = $f
        function global:devin-fake2 { '[{"id":"fresh"}]'; $global:LASTEXITCODE = 0 }
        $r = Get-DevinSessionData -DevinCmd (Get-Command devin-fake2)
        $r.Cached | Should -BeFalse
        Remove-Item function:global:devin-fake2
    }
}

Describe 'Get-PathSuggestions (launcher, cache TTL)' {
    It 'sugere nomes com prefixo' {
        $d = Join-Path $TestDrive 'dirA'
        New-Item -ItemType Directory -Path $d | Out-Null
        New-Item -ItemType File -Path (Join-Path $d 'alfa.txt') | Out-Null
        New-Item -ItemType File -Path (Join-Path $d 'beta.txt') | Out-Null
        $script:DevinPathSuggestCache = $null
        $r = Get-PathSuggestions -Text "$d\a"
        $r.Suggestions | Should -Contain (Join-Path $d 'alfa.txt')
        $r.Suggestions | Should -Not -Contain (Join-Path $d 'beta.txt')
    }
    It 'popula cache de diretorio' {
        $d = Join-Path $TestDrive 'dirB'
        New-Item -ItemType Directory -Path $d | Out-Null
        New-Item -ItemType File -Path (Join-Path $d 'x1.txt') | Out-Null
        $script:DevinPathSuggestCache = $null
        $null = Get-PathSuggestions -Text "$d\x"
        $script:DevinPathSuggestCache.Path.TrimEnd('\') | Should -Be $d
    }
}
