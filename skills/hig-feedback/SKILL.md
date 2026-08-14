---
name: hig-feedback
description: Use quando o usuário pedir para revisar ou implementar feedback de progresso, loading, notificações e empty states da UI WebView2 (dashboard/settings do BackupEmail) seguindo Apple HIG. WHAT: audita a fatia 26–32 e 47 do checklist com evidência arquivo:linha — todo loading tem saída (cancelar/timeout/retry), barra determinada para progresso quantificável (spinner só para o resto), ritmo honesto na barra (lacuna 17 ALTA), Pause ao lado do Cancel quando cancelar perde progresso, toasts não-bloqueantes com auto-dismiss, aria-live/aria-busy corretos, empty states com explicação + ação. WHEN: triggers "feedback", "progresso", "loading", "spinner", "barra de progresso", "toast", "notificação", "pause", "cancelamento", "empty state". NÃO use para: estrutura de alerta modal — use hig-alerts; copy das mensagens — use hig-writing; cores/tokens de estado — use hig-foundations.
version: 1.0.0
family: apple-hig
target: wpf-webview2
---

# HIG Feedback — Progresso, Notificações, Empty States

Feedback da UI (checklist 26–32, 47). Núcleo do BackupEmail: a barra de progresso do backup é o ponto mais crítico.

## Quando usar

- Revisar/implementar barra de progresso, spinner, botão com loading, toast, notificação, empty state.
- Adicionar Pause/confirmação de cancelamento ao backup (lacuna 17 ALTA).
- Validar `aria-live`/`aria-busy` e ritmo honesto do progresso.

## Quando NÃO usar

- Alerta modal de confirmação destrutiva → `hig-alerts`.
- Copy de toasts/erros → `hig-writing`.
- Cores e motion dos estados → `hig-foundations`.
- Posicionamento da barra na toolbar/footer → `hig-settings-navigation`.

## Contexto obrigatório

Leia **references/app-context.md** (backup usa barra determinada com % + arquivo + Cancelar; estado Azul pulsando = running). Leia **references/feedback.md** (seções 10, 16, 17 + lacuna 17) — valores; este corpo só tem princípios.

## Domínios

| Domínio | Reference | Fatia do checklist |
|---|---|---|
| Progresso & loading | `references/feedback.md` | 26–28 |
| Confirmação de sucesso | `references/feedback.md` | 29 |
| Erros | `references/feedback.md` | 30 |
| Notificações (toasts) | `references/feedback.md` | 31–32 |
| Empty states & search | `references/feedback.md` | 47 |
| File operations (Pause/Cancel) | `references/feedback.md` | lacuna 17 (ALTA) |

## Princípios

- Casamento importância↔intrusividade; interrupção só para risco de perda.
- Confirme apenas ações significativas; ações que normalmente dão certo não precisam de confirmação de sucesso.
- **Prefira barra determinada sobre spinner**; spinner só para tarefas não quantificáveis.
- **Nunca minta sobre progresso**; nunca troque spinner↔bar no meio; mantenha em movimento.
- Botão com ação demorada: **activity indicator dentro do botão + label trocado** ("Executar" → "Executando…").
- Todo loading precisa de saída: cancelar, timeout com erro, ou retry.
- **Cancel quando viável; Pause se cancelar perde progresso; se cancelar tiver consequência, alerta de confirmação.**
- Erro = alerta; notificação = banner/badge; app em primeiro plano não "notifica" — insere dados na view.

## Guardrails

- NUNCA `alert()`/`confirm()` para progresso ou sucesso (o `audit-design.mjs` marca CRÍTICO).
- NUNCA barra de progresso falsa (ex.: sempre 90%).
- NUNCA trocar spinner↔barra no meio da tarefa.
- NUNCA mostrar estado só com cor (item 8/51).
- NUNCA toast sem auto-dismiss nem botão fechar.
- NUNCA empty state sem explicação + próximo passo.

## Exemplos

- **Bom**: backup em execução — barra determinada com % + arquivo atual + `[Pausar] [Cancelar]`; ao cancelar, `"Cancelar o backup?"` + `"O progresso será perdido."`. Fonte: lacuna 17.
- **Ruim**: botão "Executar" vira spinner sem cancelar nem % (sem saída, sem ritmo honesto).
- **Bom**: toast `"Backup concluído"`, `aria-live="polite"`, auto-dismiss 4s + fechar.
- **Ruim**: `alert("Backup concluído")` — interrupção para informação não-crítica (item 52).
- **Bom**: tabela vazia — ícone + `"Nenhum backup ainda"` + botão `"Executar Backup"`.
- **Ruim**: tabela vazia — linha em branco sem texto.

## Checklist do domínio

- **[26] Todo loading tem saída (cancelar/timeout/retry)** — PASS: barra de backup tem Cancel; refresh tem retry/timeout → verificação: leitura dos fluxos de loading. Fonte: HIG Feedback.
- **[27] Spinner só para não-quantificável; barra para o resto** — PASS: backup usa barra determinada; spinner só em ações 1–3s → verificação: leitura. Fonte: HIG Progress.
- **[28] Nenhum progresso falso** — PASS: % reflete bytes copiados (robocopy real) → verificação: fonte do valor no `BackupEngine`. Fonte: HIG Progress.
- **[30] Erros com causa + ação; nunca só "Erro 1234"** — PASS: painel de erro com lista + badge + retry → verificação: leitura. Fonte: HIG Feedback.
- **[31] Toasts não bloqueiam; auto-dismiss + fechar** — PASS: toast `aria-live="polite"`, 4s + botão fechar → verificação: leitura. Fonte: HIG Notifications.
- **[47] Empty states com explicação + ação** — PASS: toda lista vazia tem ícone+título+texto+CTA → verificação: leitura. Fonte: HIG Empty States.

## Failure modes

- Barra "sempre 90%" ou % que não anda — parece travada (lacuna 17).
- Cancelar sem Pause em backup longo → perde progresso sem aviso.
- Toast virando "o único feedback de erro" (item 30: erro precisa de ação/retry).
- Spinner parado (travou) mantido em loop sem texto — deve girar sempre ou mostrar erro.

## Related Skills

- `hig-alerts` — erro = alerta; lacuna 17 exige alerta de confirmação ao cancelar.
- `hig-writing` — copy de toasts, erros e empty states.
- `hig-foundations` — tokens de cor/motion dos estados (item 8/51 nunca só cor).
- `hig-settings-navigation` — posição da barra de status/controles.
- `apple-hig` — consolida 26–32 e 47 no relatório 52/52.
