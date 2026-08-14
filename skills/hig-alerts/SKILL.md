---
name: hig-alerts
description: Use quando o usuário pedir para revisar ou implementar alertas, modais, sheets, popovers e tooltips da UI WebView2 (dashboard/settings do BackupEmail) seguindo Apple HIG. WHAT: audita a fatia 33–38 do checklist com evidência arquivo:linha — alerta só para crítico/acionável (nunca no startup, nunca pura informação), título ≤2 linhas com botões de verbo, destrutivo com Cancel e estilo de perigo, Enter default / Esc cancela / foco capturado, um sheet por vez. WHEN: triggers "alerta", "modal", "confirmação", "destrutivo", "sheet", "tooltip", "diálogo". NÃO use para: feedback/progresso/toast — use hig-feedback; copy dos rótulos — use hig-writing; foco/leitor de tela — use hig-accessibility; posicionamento/botões genéricos — use hig-settings-navigation.
version: 1.0.0
family: apple-hig
target: wpf-webview2
---

# HIG Alerts — Alertas, Sheets, Tooltips

Alertas e superfícies sobrepostas (checklist 33–38). Erro = alerta; informação = feedback no contexto (não alerta).

## Quando usar

- Criar/revisar alerta modal, confirmação destrutiva, sheet, popover ou tooltip.
- Validar que nenhum alerta aparece no startup ou para pura informação.
- Revisar ordem de botões, foco e teclado de modais.

## Quando NÃO usar

- Loading/progresso/toast/notificação → `hig-feedback`.
- Texto dos rótulos (verbos, capitalização) → `hig-writing`.
- Alvos, foco-visible, leitor de tela → `hig-accessibility`.
- Botões/padrões gerais de toolbar → `hig-settings-navigation`.

## Contexto obrigatório

Leia **references/app-context.md** (erros do app = painel com lista + retry; alerta modal só para destrutivas irreversíveis). Leia **references/alerts.md** (seção 9 + lacuna 4) — valores e estrutura; este corpo só tem princípios.

## Domínios

| Domínio | Reference | Fatia do checklist |
|---|---|---|
| Alertas | `references/alerts.md` | 33–38 |
| Sheets & alterações não salvas | `references/alerts.md` | lacuna 4 |
| Popovers & tooltips | `references/alerts.md` | lacuna 4 |

## Princípios

- Use alertas com moderação; **nunca só para informar** — feedback no contexto.
- **Nunca alerta no startup**.
- Alerta = título + texto opcional + **até 3 botões**.
- **Erro = alerta, não notificação**.
- Destrutivas: sempre com Cancel; destrutivo em vermelho; não é default.
- Botão único default: use "Done/Concluir", nunca "Cancel".
- Sheet = tarefa pequena e focada; **um sheet por vez**.
- Tooltip = view transiente que descreve como usar um componente; **aparece no hover**.

## Guardrails

- NUNCA `alert()`/`confirm()`/`prompt()` nativo (o `audit-design.mjs` marca como CRÍTICO).
- NUNCA modal sobre modal (item 38).
- NUNCA alerta de pura informação (item 52 é do orquestrador, mas depende desta skill).
- NUNCA `"OK"` em ação destrutiva — use verbo + objeto.
- NUNCA `<div onclick>` para diálogo — use `<dialog>`/`<button>`.
- NUNCA dispensar sheet com alterações não salvas sem confirmação (lacuna 4).

## Exemplos

- **Bom**: confirmação de cancelamento do backup — `role="alertdialog"`, título `"Cancelar o backup?"`, texto `"O progresso será perdido."`, botões `[Cancelar] [Cancelar backup]` (vermelho, à direita), Enter = default, Esc = cancela.
- **Ruim**: `alert("Backup concluído")` — informação que deveria ser feedback passivo no contexto (item 33/52).
- **Bom**: tooltip no hover do botão só-ícone: `"Executar backup (Ctrl+Shift+R)"`.
- **Ruim**: tooltip que cobre o elemento que o revelou (lacuna 4).

## Checklist do domínio

- **[33] Alertas só para crítico/acionável; nada no startup** — PASS: nenhum `alert()`/`<dialog>` automático na carga → verificação: `audit-design.mjs` + leitura do fluxo de boot. Fonte: HIG Alerts.
- **[34] Título ≤2 linhas; botões 1–2 palavras com verbo** — PASS: título curto; botões "Cancelar"/"Excluir" → verificação: leitura do modal. Fonte: HIG Alerts (+ copy `hig-writing`).
- **[35] Nenhum "OK" em ação destrutiva** — PASS: rótulo destrutivo é verbo+objeto → verificação: grep `OK` no contexto de modais. Fonte: HIG Alerts.
- **[36] Destrutivo com Cancel; estilo de perigo** — PASS: botão vermelho com "Cancelar" à esquerda → verificação: leitura do alerta. Fonte: HIG Alerts.
- **[37] Enter default; Esc cancela; foco capturado** — PASS: `<dialog>` com `showModal()`, focus trap, Enter/Esc → verificação: interação. Fonte: HIG Alerts.
- **[38] Nenhum modal sobre modal** — PASS: um `<dialog>` aberto por vez → verificação: leitura do fluxo. Fonte: HIG Alerts.

## Failure modes

- Sheet/popover abrindo outro modal (item 38).
- Tooltip inacessível por hover só (sem foco/`aria-describedby`).
- Confirmação de cancelamento sumindo após o app ter "Pause" (ver `hig-feedback` lacuna 17).

## Related Skills

- `hig-feedback` — erro = alerta vs toast; lacuna 17 exige alerta de confirmação ao cancelar backup.
- `hig-writing` — fornece o copy dos rótulos (34).
- `hig-accessibility` — valida `role="alertdialog"`, `aria-labelledby/describedby`, focus trap.
- `apple-hig` — consolida 33–38 e o item transversal 52.
