# ADR 004: TUI manual no devin launcher (sem Terminal.Gui/ConsoleGuiTools)

## Status

Accepted

## Context

`devin-session-launcher.ps1` implementa uma TUI manual com
`[Console]::ReadKey`, redesenho de buffer e fuzzy filter proprios
(MEL-14 do audit devin-N). A alternativa avaliada foi adotar uma
biblioteca de TUI:

- **Terminal.Gui v2**: churn de API relevante entre major versions e gaps
  de compatibilidade com PowerShell (host, runspace, threading).
- **ConsoleGuiTools / Out-ConsoleGridView**: projeto arquivado; tambem
  exigiria dependencia externa nova.
- **fzf/gum**: binarios externos novos, fora do escopo de dependencias.

## Decision

Manter a TUI manual existente. Nenhuma dependencia externa de UI e
adicionada; melhorias de UX (debounce de filesystem, cache de sugestoes,
spinner via runspace) sao feitas dentro da implementacao atual.

## Consequences

- Codigo de UI permanece verboso e manual, porem sem deps externas.
- Novos recursos de UI devem preferir helpers existentes
  (`Show-TerminalList`, `Read-EditableLine`, `Test-FuzzyMatch`).
- Revisitar apenas se Terminal.Gui estabilizar API sob pwsh.
