# Plano: Melhoria de UX dos seletores de terminal

> **Para agentes de implementacao:** usar `/dispatching-parallel-agents` (recomendado) ou `/executing-plans`. Tarefas usam checkbox (`- [ ]`).
> **Ledger unlazy:** `docs/plans/2026-08-26-melhoria-ux-seletores-ledger.md` (`.devin/ledgers` esta gitignored no projeto).

**Objetivo:** Deixar a selecao de branchs, numero de instancias e demais listas no `devin-N.ps1` visualmente organizada em colunas, consistente (mesmo seletor `Show-TerminalList`) e agradavel de usar (filtro fuzzy, atalhos rapidos, ajuda e indicadores).

**Arquitetura:** Manter `Show-TerminalList` generico em `devin-session-launcher.ps1`, estendendo-o com recursos de UX, e reutiliza-lo para a escolha do numero de instancias no `devin-N.ps1`. Refatorar a formatacao de branchs para gerar linhas em colunas alinhadas sem perder a capacidade de filtro.

**Tech Stack:** PowerShell 7+, API nativa do console (`[Console]::ReadKey`, `[Console]::SetCursorPosition`), sem novas dependencias.

## Restricoes globais

- Nao reintroduzir `Out-ConsoleGridView` nem `ConsoleGuiTools`.
- Manter o fallback para console redirecionado (`Read-Host`).
- Garantir que `pytest` continue passando antes de qualquer push.
- Nao alterar o fluxo de abertura de janelas/worktrees.
- Preservar os atalhos atuais (setas, Enter, Esc, Backspace, Delete, Home, End, PageUp, PageDown).

## Pesquisa (context7 + fontes)

- `Terminal.Gui` / `ListView`: listas rolateis com setas, Enter, Space; recomenda mostrar contador e barra de rolagem.
- `fzf`: fuzzy matching em tempo real, `Esc`/"!"/`|` e `Tab`; digitos `1-9` podem pular-para-selecionar em listas curtas.
- `Ink` / `enhanced-select-input`: `?` para ajuda, `Backspace` apaga filtro, `Esc` limpa e depois cancela, indicadores de rolagem.
- `terminal-menus.sh`: `filtermenu` com contador de resultados, `Tab` alterna foco e `?` mostra atalhos.

Aprendizado aplicado:
1. Adicionar **fuzzy matching** (subconjunto de caracteres em ordem) no filtro.
2. Permitir **digitos 1-9** como atalho de selecao quando nao ha filtro e a lista tem <= 9 itens.
3. Mostrar **contador** (`X/Y`) na barra de filtro e **indicadores de rolagem** quando a lista exceder a janela.
4. Tecla `?` mostra uma **linha de ajuda** temporaria com os controles.
5. `Ctrl+C` cancela de forma segura sem matar o script.

---

## Task 1: Padronizar selecao de numero de instancias

**Arquivos:**
- Modificar: `devin-N.ps1:530-548` (bloco `PromptForChoice`).
- Modificar: `devin-session-launcher.ps1:5-155` (adicionar `DefaultIndex` a `Show-TerminalList`).

**Interfaces:**
- `Show-TerminalList` ganha parametro opcional `[int]$DefaultIndex = 0`.
- Em console redirecionado, `DefaultIndex` afeta apenas o destaque; a entrada ainda e numerica.

### Passos

- [ ] **Step 1.1: Adicionar `-DefaultIndex` a `Show-TerminalList`**

```powershell
param(
    [Parameter(Mandatory)]
    [array]$Items,
    [string]$Title = 'Selecione',
    [scriptblock]$ToString = { param($x) $x.ToString() },
    [int]$DefaultIndex = 0
)
```

No inicio do laco interativo, clampar `$selected = [Math]::Max(0, [Math]::Min($DefaultIndex, $Items.Count - 1))`.

- [ ] **Step 1.2: Substituir `PromptForChoice` por `Show-TerminalList`**

Substituir o bloco em `devin-N.ps1`:

```powershell
$titulo = "Quantidade de Janelas"
$opcoes = @(
    [PSCustomObject]@{ Numero = 1; Label = '1 - Uma instancia (Tela inteira)' },
    [PSCustomObject]@{ Numero = 2; Label = '2 - Duas instancias com Worktree isolado (Lado a Lado)' },
    [PSCustomObject]@{ Numero = 3; Label = '3 - Tres instancias com Worktree isolado' },
    [PSCustomObject]@{ Numero = 4; Label = '4 - Quatro instancias com Worktree isolado (2x2)' }
)
$escolha = Show-TerminalList -Items $opcoes -Title $titulo -ToString { param($x) $x.Label } -DefaultIndex 0
$numInstancias = if ($escolha) { $escolha.Numero } else { 1 }
```

- [ ] **Step 1.3: Testar parser e fallback redirecionado**

Criar `tmp_test_instancias.ps1`:

```powershell
. C:\Users\Fingertech\Desktop\scripts\devin-bundle\devin-session-launcher.ps1
$opcoes = @(
    [PSCustomObject]@{ Numero = 1; Label = '1 - Uma' },
    [PSCustomObject]@{ Numero = 2; Label = '2 - Duas' }
)
$sel = Show-TerminalList -Items $opcoes -Title 'Teste instancias' -ToString { param($x) $x.Label } -DefaultIndex 1
Write-Output "INSTANCIA: $($sel.Numero)"
```

Rodar: `echo "2" | pwsh -NoProfile -File tmp_test_instancias.ps1`.

**Esperado:** `INSTANCIA: 2`.

---

## Task 2: Refatorar exibicao de branchs em colunas

**Arquivos:**
- Modificar: `devin-N.ps1:340-418` (`Format-BranchStatus`), `devin-N.ps1:454-477` (`Select-BranchTerminal`).

**Interfaces:**
- `Format-BranchStatus` passa a devolver um `PSCustomObject` com campos pre-formatados.
- `Select-BranchTerminal` calcula larguras e monta uma string em colunas com `PadRight`.
- A label exibida continua a ser uma string unica para nao quebrar `Show-TerminalList`.

### Passos

- [ ] **Step 2.1: Transformar `Format-BranchStatus` em gerador de colunas**

Exemplo de retorno:

```powershell
[PSCustomObject]@{
    Type        = $branchType
    Name        = $BranchName
    CurrentMark = if ($BranchOption.IsCurrent) { '*' } else { '' }
    Sync        = $syncToken
    PrNumber    = $prNumber
    PrState     = $prState
    Author      = $author
    Review      = $review
    Ci          = $ci
    Activity    = $activity
    Flags       = $flags
}
```

Os campos devem ser strings curtas (`'n/a'`, `'-'`, `'MERGED'`, etc.).

- [ ] **Step 2.2: Criar formatador de linha em colunas em `Select-BranchTerminal`**

Depois de gerar `$rows`, calcular:

```powershell
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
```

Montar a label no `ToString`:

```powershell
$selected = Show-TerminalList -Items $rows -Title $Title -ToString {
    param($x)
    $line = "[$($x.Type.PadRight($wType))] $($x.Name.PadRight($wName)) "
    if ($x.CurrentMark) { $line += "$(($x.CurrentMark).PadRight($wCur)) " }
    $line += "$($x.Sync.PadRight($wSync)) | "
    $line += "#$($x.PrNumber.PadRight($wPr)) $($x.PrState.PadRight($wState)) "
    $line += "autor:$($x.Author.PadRight($wAuth)) "
    $line += "rev:$($x.Review.PadRight($wRev)) "
    $line += "CI:$($x.Ci.PadRight($wCi)) "
    $line += "$($x.Activity.PadRight($wAct))"
    if ($x.Flags) { $line += " [$($x.Flags)]" }
    $line
}
```

Truncar a linha ao tamanho do console para evitar quebra: `.Substring(0, [Math]::Min($line.Length, [Console]::WindowWidth - 1))`.

- [ ] **Step 2.3: Testar com dados sinteticos**

Criar `tmp_test_branch.ps1` que chama `Select-BranchTerminal` com um `MetaMap`, `PrMap` e `Options` de mentira. O teste deve validar que a label gerada contem colunas com alinhamento visual (verificar que `PadRight` produziu multiplos espacos consecutivos antes das barras).

---

## Task 3: Melhorar UX do `Show-TerminalList`

**Arquivo:** `devin-session-launcher.ps1:5-155`.

### Passos

- [ ] **Step 3.1: Implementar fuzzy matching no filtro**

Trocar a condicao de filtro para uma funcao `Test-FuzzyMatch`:

```powershell
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
```

Aplicar no filtro:

```powershell
$filtered = @($Items | Where-Object { Test-FuzzyMatch -Text (Get-Label $_) -Query $filterText })
```

- [ ] **Step 3.2: Atalhos de digitos 1-9 para listas curtas**

No laco `ReadKey`, se `filterText` estiver vazio e `$Items.Count -le 9`, interpretar `D0` a `D9` como selecao direta:

```powershell
'D0' { if (-not $filterText -and $Items.Count -le 9 -and $filtered.Count -gt 0) { return $filtered[0] } }
'D1' { if (-not $filterText -and $Items.Count -le 9 -and $filtered.Count -gt 1) { return $filtered[1] } }
'D2' { if (-not $filterText -and $Items.Count -le 9 -and $filtered.Count -gt 2) { return $filtered[2] } }
# ... ate D8
```

Observacao: `ReadKey` retorna `ConsoleKey.D1` quando a tecla `1` e pressionada sem modificadores.

- [ ] **Step 3.3: Adicionar contador e indicadores de rolagem**

Na barra de filtro:

```powershell
$filterInfo = "Filtro: $filterText`_ ($($filtered.Count)/$($Items.Count))"
Write-MenuLine -Text $filterInfo -Color 'Cyan'
```

Indicadores de rolagem acima/abaixo da lista:

```powershell
if ($filtered.Count -gt $windowSize) {
    if ($start -gt 0) { Write-MenuLine -Text "   ^ $($start) anteriores" -Color 'DarkGray' }
    if ($end -lt $filtered.Count -  1) { Write-MenuLine -Text "   v $($filtered.Count - $end - 1) seguintes" -Color 'DarkGray' }
}
```

Ajustar `$currentTotalLines` para incluir essas linhas extras.

- [ ] **Step 3.4: Tecla `?` para ajuda e `Ctrl+C` seguro**

Configurar `TreatControlCAsInput` no inicio do modo interativo:

```powershell
$oldTreatCtrlC = [Console]::TreatControlCAsInput
[Console]::TreatControlCAsInput = $true
```

No `finally`, restaurar. No switch:

```powershell
'F1' { }
'F2' { }
'F3' { }
'F4' { }
'F5' { }
'F6' { }
'F7' { }
'F8' { }
'F9' { }
'F10' { }
'F11' { }
'F12' { }
'C' { if ($keyInfo.Modifiers -band [ConsoleModifiers]::Control) { return $null } }
```

Criar variavel `$showHelp`. Ao pressionar `Oem2`/`?` (ConsoleKey.Oem2), alternar. Na renderizacao, se `$showHelp`:

```powershell
Write-MenuLine -Text " Ajuda: Setas = mover, Enter = selecionar, Esc = cancelar, Backspace/Delete = filtro, ? = alternar ajuda, Ctrl+C = cancelar" -Color 'DarkGray'
```

- [ ] **Step 3.5: Testar parser e atalhos**

Criar `tmp_test_ux.ps1` com multiplas entradas simulando `?`, `Down`, `Enter`, `2`, etc. Validar saida.

---

## Task 4: Validacao e entrega

- [ ] **Step 4.1: Verificar parser de ambos os arquivos**

Criar `tmp_parse_final.ps1`:

```powershell
$paths = @('devin-N.ps1','devin-session-launcher.ps1')
foreach ($path in $paths) {
    $err = @()
    [void]([System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw $path), [ref]$err))
    if ($err.Count -gt 0) { throw "ERRO $path" }
    Write-Output "OK $path"
}
```

- [ ] **Step 4.2: Executar `pytest`**

```bash
pytest
```

Esperado: `139 passed`.

- [ ] **Step 4.3: Commit e push**

```bash
git add -A
git commit -m "feat: seletores com colunas, fuzzy, atalhos e melhorias de UX"
git push
```

---

## Auto-revisao do plano

1. **Cobertura da especificacao:**
   - Colunas em branchs: Task 2.
   - Numero de instancias no mesmo estilo: Task 1.
   - Pesquisa UX aplicada: introducao e Task 3.

2. **Scan de placeholders:** nenhum `TBD`/`TODO` nas tarefas principais. As tarefas 2.3 e 3.5 pedem testes `tmp_` que devem ser criados e depois removidos.

3. **Consistencia de tipos:** `Show-TerminalList` recebe `[array]` e devolve item original; `ToString` e `[scriptblock]`. `Format-BranchStatus` passa a devolver `PSCustomObject` com strings, consumido por `Select-BranchTerminal`.

## Opcoes de execucao

**1. Subagente por tarefa (recomendado):** cada Task e independente (1 e 2 podem ser paralelos; 3 e 4 dependem das anteriores).

**2. Inline:** executar na sessao atual com checkpoints apos cada Task.
