# app-context — BackupEmail (mapeamento atual)

Estado reconstruído em 2026-08-03, pós-remediação HIG 52/52 (26 PASS · 20 FAIL · 6 N/A → corrigidos os 20 FAIL + 1 N/A aplicável, itens 22–25 e 51–52 reavaliados). Sempre validar contra o código atual antes de auditar (este arquivo é a linha de base, não a verdade viva).

## Stack (IMPORTANTE — mudou de WPF+WebView2 para Avalonia)
- **Avalonia 12.1.1** (FluentTheme, XAML `.axaml`, DIPs — sem rem/CSS, sem `prefers-color-scheme`).
- **.NET 10**, solução `BackupEmail.slnx` (projetos: Core, Agent, Dashboard), `<SupportedOSPlatform>windows</SupportedOSPlatform>`.
- Nada de HTML/CSS/JS, WebView2, sidebar 240px ou fontes 13px/15px/17px/22px do WebView2 — TUDO abaixo é o modelo novo.

## Arquivos de UI (D:\Envio\Project\BackupEmail\src\BackupEmail.Dashboard\)
| Arquivo | Papel |
|---|---|
| `App.axaml` | Tokens: cores (ThemeDictionaries Light/Dark), fontes (`TextCaption` 11, `TextBody` 12, `TextBodyMedium` 13, `TextEmphasis` 15, `TextTitle` 17, `TextTitleLarge` 22), pincéis `ButtonPrimaryTextBrush`, `TextSecondaryBrush`, `ErrorBrush`, `ErrorSurfaceBrush`, `OkBrush`, `SurfaceBorderBrush` |
| `App.axaml.cs` | `ShareRoot`/`MachineFilter` estáticos + cascata `--share` → dashboard-settings → default `\\192.168.1.200\Email` |
| `Views\MainWindow.axaml` | Cards de máquina (badge cor+ícone+texto via `badgeIcon.ok/warning/error/offline/unknown`), empty state, rodapé `FooterText` (LiveSetting=Polite), dot de PST com `pstName.fail` |
| `Views\SettingsWindow.axaml` | Panes Geral/Máquinas (Ctrl+, abre, Esc fecha, último pane restaurado), `Button.pane.selected` p/ estado ativo, `Button.destructive` (Remover ≥28px), TextBox raio 8, Enter salva, Cancelar tooltip "Fechar sem salvar (Esc)" |
| `ViewModels\DashboardViewModel.cs` | Refresh com timeout 15s + try/catch, filtro `--machine`, `EmptyStateMessage`, pluralização real, `OpenShare` sem `ex.Message` cru |
| `ViewModels\SettingsViewModel.cs` / `MachineSettingsViewModel.cs` | Restaura "Geral" explicitamente; validação com mensagens acionáveis |
| `ViewModels\MachineCardViewModel.cs` | `Plural()` (1 dia / 2 dias, 1 mês / 2 meses), `FormatAge` |

## Design system (alvo pós-remediação)
- Grade: 4/8px via tokens `--space-*`; margens de janela 20px; header 28,20; corpo 20,20; linhas 0,4; padding listas 12,8; badge 8,4; card interno Spacing 12.
- Raios: 8 (botões/TextBox), 10 (cards), 20, 999. Ícones: stroke 1.5–2.
- Motion: 120/200/300ms, só transform/opacity, `prefers-reduced-motion` → `ReduceMotion`/matchMedia equivalente.
- Tipografia: mínimo 11px (Caption), corpo 12px, LineHeight ≥1.4 em textos com wrap.
- Contraste: body-text ≥4.5:1. Cores-chave: `OkBrush` #1B7F3B; erro dark `#FF6961` sobre `ErrorSurfaceColor` dark `#3A1A18` (light `#B3261E` sobre `#14B3261E`); footer/badge `#0066CC` (light) / `#3BA1FF` (dark); botão primário (verde): texto Light `#FFFFFF`, **Dark `#1C1C1E`** (branco sobre #34C759 falha 4.5:1); texto secundário `#636366` (light) / `#98989D` (dark).

## HIG — estado conhecido (auditado; NÃO re-auditar por inteiro sem motivo)
- 1–21 Foundations: corrigidos (tokens de fonte substituíram literais; contraste do botão primário dark; grade/raios/motion conforme acima).
- 26–32 Feedback: refresh tem timeout/catch; erros com ação/retry; empty states com explicação + ação; LiveSetting=Polite no footer/status.
- 33–38 Alerts: alerta só crítico/acionável; destrutivo com Cancel + estilo; Enter default/Esc cancela/foco capturado; um sheet por vez.
- 39–43 A11y: alvos ≥28px (mouse) / ≥44px (touch); foco visível via FocusAdorner do Fluent (nada desabilita); tab order lógico; `AutomationProperties.Name` em todos os TextBoxes; ícones decorativos aria-hidden.
- 44–48 Settings/Nav: pane "Geral" restaura; `aria-current`/classe `selected`; salvar explícito (botão Salvar) — NUNCA misturar com auto-save; empty states; atalhos documentados (Ctrl+, / Esc / Enter).
- 49–50 Writing: botões com verbo ("Executar Backup", "Salvar", "Cancelar" ok; nunca "OK"); capitalização consistente; erros com causa + como corrigir.
- 51–52 Estado: badge usa cor + ícone + texto (tríade completa); sincronização/agendamento exibidos.

## Contratos / limites (não violar)
- Designer edita SOMENTE `.axaml` + estilos visuais; NÃO altera handlers C# que mudam comportamento de salvar/validação nem o formato dos JSON (configs camelCase com comentários; status via `AtomicJsonWriter`).
- Config por máquina: `configs\<maquina>.json`; agente `run --config` (default `config.json` no CWD, mas o agendamento passa o caminho real).
- Status: `\\<share>\status\<MachineName>.json`; offline = `LastSeen` > 9 dias (`StatusReader.OfflineThreshold`).
- Agendamento: semanal sexta 16:40 (`install-schedule.ps1`); defaults pós-instalação Inno: `C:\Program Files\BackupEmail\Agent\BackupEmail.Agent.exe` + `configs\<MachineName>.json`.
