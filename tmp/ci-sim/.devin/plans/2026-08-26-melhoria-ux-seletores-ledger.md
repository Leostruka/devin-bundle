# GATES: Melhoria de UX dos seletores de terminal

> Ledger unlazy para o plano `docs/plans/2026-08-26-melhoria-ux-seletores.md`.

- [x] **G1: Numero de instancias usa `Show-TerminalList`**
  - **CHECK:** `pwsh -NoProfile -Command "if (Get-Content 'devin-N.ps1' | Select-String -Pattern 'PromptForChoice' -SimpleMatch) { exit 1 } else { exit 0 }"`
  - **EXPECT:** exit code `0`
  - **EVIDENCE:** exit code 0; `PromptForChoice` removido de `devin-N.ps1`.

- [x] **G2: `Show-TerminalList` suporta `-DefaultIndex`**
  - **CHECK:** `pwsh -NoProfile -Command "if (Get-Content 'devin-session-launcher.ps1' | Select-String -Pattern 'DefaultIndex' -SimpleMatch) { exit 0 } else { exit 1 }"`
  - **EXPECT:** exit code `0`
  - **EVIDENCE:** exit code 0; parametro `[int]$DefaultIndex = 0` adicionado e `$selected` clampado.

- [x] **G3: Branch exibido em colunas alinhadas**
  - **CHECK:** `pwsh -NoProfile -Command "if ((Get-Content 'devin-N.ps1' | Select-String -Pattern 'PadRight' -SimpleMatch) -and (Get-Content 'devin-N.ps1' | Select-String -Pattern 'Select-BranchTerminal' -SimpleMatch)) { exit 0 } else { exit 1 }"`
  - **EXPECT:** exit code `0`
  - **EVIDENCE:** exit code 0; `Format-BranchStatus` retorna `PSCustomObject`; `Select-BranchTerminal` monta linhas com `PadRight` e marca atual (`*`) junto ao nome via `$displayName`.

- [x] **G4: Filtro fuzzy implementado**
  - **CHECK:** `pwsh -NoProfile -Command "if (Get-Content 'devin-session-launcher.ps1' | Select-String -Pattern 'Test-FuzzyMatch' -SimpleMatch) { exit 0 } else { exit 1 }"`
  - **EXPECT:** exit code `0`
  - **EVIDENCE:** exit code 0; funcao `Test-FuzzyMatch` implementada e usada no filtro; teste `tmp_test_ux.ps1` com `fbr` selecionou `feature-foo-bar`.

- [x] **G5: Atalhos de digitos para listas curtas**
  - **CHECK:** `pwsh -NoProfile -Command "if (Get-Content 'devin-session-launcher.ps1' | Select-String -Pattern 'char -le' -SimpleMatch) { exit 0 } else { exit 1 }"`
  - **EXPECT:** exit code `0`
  - **EVIDENCE:** exit code 0; digitos `0-9` interceptados como atalhos quando `$filterText` vazio e `$Items.Count -le 9`.

- [x] **G6: Ajuda (`?`) e `Ctrl+C` seguro**
  - **CHECK:** `pwsh -NoProfile -Command "if ((Get-Content 'devin-session-launcher.ps1' | Select-String -Pattern 'TreatControlCAsInput' -SimpleMatch) -and (Get-Content 'devin-session-launcher.ps1' | Select-String -Pattern 'showHelp' -SimpleMatch)) { exit 0 } else { exit 1 }"`
  - **EXPECT:** exit code `0`
  - **EVIDENCE:** exit code 0; `TreatControlCAsInput` configurado, `Ctrl+C` interceptado no switch, `showHelp` alternado pela tecla `?`.

- [x] **G7: Parser sem erros**
  - **CHECK:** `pwsh -NoProfile -Command '$paths = @("devin-N.ps1","devin-session-launcher.ps1"); foreach ($p in $paths) { $err = @(); [void]([System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw $p), [ref]$err)); if ($err.Count -gt 0) { throw "ERRO $p" } }'`
  - **EXPECT:** no exception
  - **EVIDENCE:** `tmp_parse_final.ps1` executou sem erros: `OK devin-N.ps1` e `OK devin-session-launcher.ps1`.

- [x] **G8: Suite de validacao passa**
  - **CHECK:** `pytest`
  - **EXPECT:** output contains `139 passed`
  - **EVIDENCE:** output `139 passed in 8.41s`.
