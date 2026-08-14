# Alerts (checklist 33–38) — HIG seção 9 + lacuna 4

> Aplica-se também a sheets, popovers e tooltips (lacuna 4).

## Fatia do checklist

| # | Item | PASS |
|---|---|---|
| 33 | Alertas só para crítico/acionável; nada no startup | nenhum diálogo automático na carga |
| 34 | Título ≤2 linhas; botões 1–2 palavras com verbo | rótulos curtos, sem pontuação |
| 35 | Nenhum "OK" em ação destrutiva | rótulo destrutivo = verbo + objeto |
| 36 | Destrutivo com Cancel; estilo de perigo | "Cancelar" presente; botão perigo em vermelho |
| 37 | Enter default; Esc cancela; foco capturado | `<dialog>` + `showModal()`, focus trap |
| 38 | Nenhum modal sobre modal | um diálogo por vez |

## Valores **(oficial)**

- Use com moderação; **nunca só para informar** — feedback no contexto.
- **Nunca alerta no startup**.
- Alerta = título + texto opcional + **até 3 botões**.
- **Erro = alerta, não notificação**.
- Destrutivas: sempre com Cancel; destrutivo em vermelho.
- Botão único default: use "Done/Concluir", nunca "Cancel".
- Evite "Yes"/"No"; evite "OK" exceto informativo puro.
- Botão mais provável **à direita**; Cancel à esquerda; destrutivo **não é default**.

## Aplicação web

- `role="alertdialog"`, `aria-labelledby`, `aria-describedby`; primário à direita; Enter = default; Esc = cancela.
- Use `<dialog>`/`<button>`, **nunca `<div onclick>`**.

## Lacuna 4 — Sheets / Popovers / Tooltips (PARCIAL)

HIG oficial (`/sheets`, `/popovers`, `/offering-help`):
- Sheet = tarefa pequena e focada; **um sheet por vez** (feche o primeiro antes de abrir outro).
- Com alterações não salvas → **confirmação** ao dispensar.
- Popover: seta aponta para a origem; **não cubra o elemento que o revelou**.
- Tooltip (help tag) = view transiente que descreve como usar um componente; **aparece no hover**.

**BackupEmail**: tooltips de hover (atalhos/controles do dashboard), confirmação de alterações não salvas ao dispensar modal de settings.

## Exemplos pt-BR

- Cancelamento de backup: título `"Cancelar o backup?"`; texto `"O progresso será perdido."`; botões `[Cancelar]` (esquerda) `[Cancelar backup]` (vermelho, direita, não-default). Ruim: `[OK]` sozinho.
- Alterações não salvas: `"Descartar alterações?"` com `[Continuar editando]` / `[Descartar]`.

## Fontes

HIG Alerts, Sheets, Popovers, Offering Help; lacuna 4.
