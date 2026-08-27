# GATES: Melhoria de UX dos seletores de terminal

> Ledger unlazy para o plano `docs/plans/2026-08-26-melhoria-ux-seletores.md`.

- [ ] **G1: Numero de instancias usa `Show-TerminalList`**
  - **CHECK:** `pwsh -NoProfile -Command "if (Get-Content 'devin-N.ps1' | Select-String -Pattern 'PromptForChoice' -SimpleMatch) { exit 1 } else { exit 0 }"`
  - **EXPECT:** exit code `0`
  - **EVIDENCE:** pending

- [ ] **G2: `Show-TerminalList` suporta `-DefaultIndex`**
  - **CHECK:** `pwsh -NoProfile -Command "if (Get-Content 'devin-session-launcher.ps1' | Select-String -Pattern '\[int\]\$DefaultIndex' -SimpleMatch) { exit 0 } else { exit 1 }"`
  - **EXPECT:** exit code `0`
  - **EVIDENCE:** pending

- [ ] **G3: Branch exibido em colunas alinhadas**
  - **CHECK:** `pwsh -NoProfile -Command "if ((Get-Content 'devin-N.ps1' | Select-String -Pattern 'PadRight' -SimpleMatch) -and (Get-Content 'devin-N.ps1' | Select-String -Pattern 'Select-BranchTerminal' -SimpleMatch)) { exit 0 } else { exit 1 }"`
  - **EXPECT:** exit code `0`
  - **EVIDENCE:** pending

- [ ] **G4: Filtro fuzzy implementado**
  - **CHECK:** `pwsh -NoProfile -Command "if (Get-Content 'devin-session-launcher.ps1' | Select-String -Pattern 'Test-FuzzyMatch|fuzzy|IndexOf.*pos' -SimpleMatch) { exit 0 } else { exit 1 }"`
  - **EXPECT:** exit code `0`
  - **EVIDENCE:** pending

- [ ] **G5: Atalhos de digitos para listas curtas**
  - **CHECK:** `pwsh -NoProfile -Command "if (Get-Content 'devin-session-launcher.ps1' | Select-String -Pattern 'ConsoleKey\.D[1-9]' -SimpleMatch) { exit 0 } else { exit 1 }"`
  - **EXPECT:** exit code `0`
  - **EVIDENCE:** pending

- [ ] **G6: Ajuda (`?`) e `Ctrl+C` seguro**
  - **CHECK:** `pwsh -NoProfile -Command "$c = Get-Content 'devin-session-launcher.ps1'; if (($c | Select-String -Pattern '\?' -SimpleMatch) -and ($c | Select-String -Pattern 'TreatControlCAsInput' -SimpleMatch)) { exit 0 } else { exit 1 }"`
  - **EXPECT:** exit code `0`
  - **EVIDENCE:** pending

- [ ] **G7: Parser sem erros**
  - **CHECK:** `pwsh -NoProfile -File .\tmp_parse_final.ps1`
  - **EXPECT:** output contains `OK devin-N.ps1` and `OK devin-session-launcher.ps1`
  - **EVIDENCE:** pending

- [ ] **G8: Suite de validacao passa**
  - **CHECK:** `pytest`
  - **EXPECT:** output contains `139 passed`
  - **EVIDENCE:** pending
