# Plano: corrigir resolução do `wt` em `devin-N.ps1` para split pane

> **Para agentes de implementação:** usar `/executing-plans` ou `/implement` após aprovação. Tarefas usam checkbox (`- [ ]`).

## Goal

Garantir que `devin-N.ps1` use um `wt.exe` funcional, de modo que a janela atual do Windows Terminal seja dividida em 2, 3 ou 4 painéis conforme o número de instâncias escolhido.

## Architecture

- A lógica de split pane (`split-pane`, `move-focus`, posições A/B/C/D) já está correta e foi verificada.
- O problema está na resolução de `$wtPath`: `Get-Command wt` retorna o primeiro `wt` no PATH, que pode ser um shim do Scoop quebrado.
- A correção introduz um helper `Find-WorkingWt` que percorre todos os candidatos `wt` no PATH e valida se o executável/shim realmente funciona.

## Tech Stack

- PowerShell 7+ (`pwsh`)
- `where.exe` para listar múltiplos `wt` no PATH
- `UIAutomationClient` para validação de regressão dos splits

## Global Constraints

- `python audit.py` e `python -m pytest` devem continuar passando.
- Não introduzir novas dependências.
- Preservar os fallbacks existentes (janelas separadas, janelas do PowerShell).
- Não alterar o fluxo interativo de seleção de projetos/branches.

## Proposed Modules and Interfaces

- **Modify:** `devin-N.ps1:78-81` — substituir `Get-Command wt` por `$wtPath = Find-WorkingWt`.
- **Create (living):** função `Find-WorkingWt` dentro de `devin-N.ps1` (inserida antes da resolução atual).
- **Create (prototype / disposable):** `tmp_test_split_234.ps1` — valida a resolução do `wt` e os splits 2/3/4 via UI Automation. Remover na Task 4.

---

### Task 1: Implementar `Find-WorkingWt` e usá-lo como `$wtPath`

**Files:**
- Modify: `devin-N.ps1:78-81`
- Modify: `devin-N.ps1` (adicionar função antes da resolução de `$wtPath`)

**Interfaces:**
- Consumes: nenhuma (função pura de resolução).
- Produces: `$wtPath` (string com caminho funcional para `wt` ou `$null`).

**Step 1.1: Adicionar `Find-WorkingWt`**

Inserir a função no início do bloco de utilitários de `devin-N.ps1`, antes da linha que define `$diretorioOriginal`:

```powershell
function Find-WorkingWt {
    $candidates = @()
    try {
        $candidates = (& where.exe 'wt' 2>$null) -split '\r?\n' |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ }
    } catch {}

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
```

**Step 1.2: Substituir resolução de `$wtPath`**

Substituir as linhas 78-81 de `devin-N.ps1` por:

```powershell
# Localiza o Windows Terminal (wt.exe) para abrir paineis/janelas extras
$wtPath = Find-WorkingWt
if (-not $wtPath) { Write-Host $M.WtNaoEncontrado -ForegroundColor DarkYellow }
```

**Step 1.3: Verificar parser do script**

Run:
```powershell
$err = @(); [void]([System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw .\devin-N.ps1), [ref]$err)); if ($err.Count -gt 0) { throw "Parser error" }
```

Expected: nenhum erro.

---

### Task 2: Criar e rodar teste de regressão dos splits 2/3/4

**Files:**
- Create (prototype / disposable): `tmp_test_split_234.ps1`

**Interfaces:**
- Consumes: `$wtPath` (resolvido pelo script) e UI Automation.
- Produces: relatório de contagem de painéis `TermControl` para 2, 3 e 4 splits.

**Step 2.1: Criar `tmp_test_split_234.ps1` (cópia da lógica de resolução)**

O script temporário duplica `Find-WorkingWt` para isolar a validação, sem dot-sourcar `devin-N.ps1` (que executaria o fluxo interativo). Ele abre novas janelas `-w new` para evitar interferir na sessão atual e conta painéis `TermControl`.

```powershell
Add-Type -AssemblyName UIAutomationClient

function Find-WorkingWt {
    $candidates = @()
    try {
        $candidates = (& where.exe 'wt' 2>$null) -split '\r?\n' |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ }
    } catch {}
    foreach ($candidate in $candidates) {
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
        $shimFile = [System.IO.Path]::ChangeExtension($candidate, '.shim')
        if (Test-Path -LiteralPath $shimFile) {
            $content = Get-Content -LiteralPath $shimFile -Raw
            $m = [regex]::Match($content, '^\s*path\s*=\s*"(.+?)"\s*$', [System.Text.RegularExpressions.RegexOptions]::Multiline)
            if ($m.Success) {
                $target = $m.Groups[1].Value
                if (Test-Path -LiteralPath $target -PathType Leaf) { return $candidate }
            }
            continue
        }
        return $candidate
    }
    return $null
}

function Get-WtWindows {
    $desktop = [System.Windows.Automation.AutomationElement]::RootElement
    $cond = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ClassNameProperty,
        'CASCADIA_HOSTING_WINDOW_CLASS'
    )
    $desktop.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)
}

function Count-TermControls($window) {
    $cond = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ClassNameProperty,
        'TermControl'
    )
    $panes = $window.FindAll([System.Windows.Automation.TreeScope]::Descendants, $cond)
    return $panes.Count
}

$wt = Find-WorkingWt
if (-not $wt) { throw 'Find-WorkingWt não encontrou wt funcional' }
Write-Host "Resolved wt: $wt"

function Test-Split($n) {
    $before = Get-WtWindows
    if ($n -eq 2) {
        & $wt -w new `; split-pane -V -d 'C:\Windows\System32' cmd /c '"timeout /t 3 /nobreak"' `; move-focus left
    }
    elseif ($n -eq 3) {
        & $wt -w new `; split-pane -V -d 'C:\Windows\System32' cmd /c '"timeout /t 3 /nobreak"' `; split-pane -H -d 'C:\Windows\System32' cmd /c '"timeout /t 3 /nobreak"' `; move-focus left
    }
    elseif ($n -eq 4) {
        & $wt -w new `; split-pane -H -d 'C:\Windows\System32' cmd /c '"timeout /t 3 /nobreak"' `; move-focus up `; split-pane -V -d 'C:\Windows\System32' cmd /c '"timeout /t 3 /nobreak"' `; split-pane -H -d 'C:\Windows\System32' cmd /c '"timeout /t 3 /nobreak"' `; move-focus left `; move-focus up
    }
    Start-Sleep -Seconds 2
    $after = Get-WtWindows
    $new = $after | Where-Object {
        $rect = $_.Current.BoundingRectangle
        $rect -notin ($before | ForEach-Object { $_.Current.BoundingRectangle })
    } | Select-Object -First 1
    if (-not $new) { $new = $after[$after.Count - 1] }
    $count = Count-TermControls $new
    Write-Host "Split $n -> TermControls: $count"
    if ($count -ne $n) { throw "Esperado $n paineis, encontrado $count" }
}

Test-Split 2
Test-Split 3
Test-Split 4
```

**Step 2.2: Executar o teste**

```powershell
.\tmp_test_split_234.ps1
```

Expected:
```text
Resolved wt: C:\Users\...\AppData\Local\Microsoft\WindowsApps\wt.exe
Split 2 -> TermControls: 2
Split 3 -> TermControls: 3
Split 4 -> TermControls: 4
```

---

### Task 3: Validar com execução manual do `devin-N`

**Step 3.1: Rodar `devin-N.cmd` em um repositório Git pequeno**

- Selecionar 1 projeto.
- Escolher 2 instâncias.
- Verificar visualmente que a janela é dividida em 2 painéis.
- Repetir para 3 e 4 instâncias (com múltiplas branches/worktrees).

**Step 3.2: Confirmar fallback sem `wt`**

- Renomear/quebrar temporariamente todos os `wt` no PATH.
- Verificar que `devin-N.ps1` abre janelas de PowerShell separadas em vez de falhar silenciosamente.

---

### Task 4: Limpar artefatos temporários e rodar baseline

**Files:**
- Delete: `tmp_test_split_234.ps1`

**Step 4.1: Remover arquivos temporários**

```powershell
Remove-Item -Path 'tmp_test_split_234.ps1' -ErrorAction SilentlyContinue
```

**Step 4.2: Rodar baseline**

```bash
python audit.py
python -m pytest
```

Expected: audit 0 erros, 229 passed.

---

### Task 5: Commit

**Step 5.1: Commitar as mudanças**

```bash
git add devin-N.ps1
git commit -m "fix(devin-N): resolve wt funcional e evita shim quebrado"
```

## Self-Review

1. **Spec coverage:** a correção cobre a resolução de `$wtPath` e a verificação de 2/3/4 painéis.
2. **Placeholder scan:** nenhum `TBD`/`TODO`; código concreto nas tasks.
3. **Type consistency:** `$wtPath` continua sendo uma string ou `$null`, preservando os contratos existentes.
4. **Vertical-slice scan:** as tasks entregam comportamento de ponta a ponta: resolver `wt` -> testar split -> commit.
5. **Asset-lifespan scan:** `tmp_*` são removidos na Task 4.

## Execution Handoff

Plano salvo em `docs/plans/2026-09-02-devin-N-corrigir-wt-split.md`.

**Duas opções de execução:**

1. **Execução inline** — executo as tasks nesta sessão, com checkpoints após cada teste.
2. **Subagente por task** — despacho subagentes `/implement` para cada task e reviso no final.

Quer que eu prossiga com a implementação?
