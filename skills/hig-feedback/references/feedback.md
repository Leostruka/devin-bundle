# Feedback, Progresso, Notificações, Empty States (checklist 26–32, 47) — HIG seções 10, 16, 17

## Fatia do checklist

| # | Item | PASS |
|---|---|---|
| 26 | Todo loading tem saída (cancelar/timeout/retry) | barra com Cancel; refresh com timeout/retry |
| 27 | Spinner só para não-quantificável; barra para o resto | backup = barra; ações 1–3s = spinner no botão |
| 28 | Nenhum progresso falso | % vem de bytes reais (robocopy) |
| 29 | Sucesso confirmado só para ações significativas | toast discreto; sem confirmação em ações rotineiras |
| 30 | Erros com causa + ação; nunca só "Erro 1234" | painel de erro com retry |
| 31 | Toasts não bloqueiam; auto-dismiss + fechar | `aria-live="polite"`, 4s + fechar |
| 32 | aria-live/aria-busy corretos | updates em `aria-live`; loading com `aria-busy="true"` |
| 47 | Empty states com explicação + ação | ícone + título + texto + CTA |

## Seção 10 — Feedback & Progress **(oficial)**

- Casamento importância↔intrusividade; interrupção só para risco de perda.
- **Prefira barra determinada sobre spinner**; spinner só para tarefas não quantificáveis.
- **Nunca minta sobre progresso**; nunca troque spinner↔bar no meio.
- Spinner parado = "travou" — mantenha girando.
- Botão com ação demorada: **activity indicator dentro do botão + label trocado** ("Checkout" → "Checking out…").
- Todo loading precisa de saída: cancelar, timeout com erro, ou retry.
- Timeout recomendado: erro após **10–15s** de spinner sem resposta. **(prática)**

### Aplicação web

- Backup em execução: barra determinada com % + arquivo atual + cancelar.
- Refresh de tabela: spinner inline 16–20px sem bloquear.
- Ações 1–3s: spinner no botão + label ("Validando…"); >3s: barra.
- Sucesso: feedback passivo (linha atualiza, toast 2–3s auto-dismiss).
- Erro: `role="alert"` + ícone + texto + ação (Retry); **nunca só toast**.
- `aria-live="polite"` para updates; `aria-busy="true"` durante loading.

## Lacuna 17 — Progress: File Operations (PARCIAL — ALTA)

HIG oficial (`/progress-indicators`):
- **Determinado quando possível**; progresso **preciso** (ritmo honesto — "90% em 5s e 10% em 5min" parece travado/enganoso).
- Mantenha em movimento; se travar, **feedback do problema + o que fazer**.
- Não troque circular↔barra no meio.
- **Cancel quando viável**; **Pause se cancelar perde progresso**; se cancelar tiver consequência, **alerta de confirmação**.

**BackupEmail**: falta **Pause ao lado do Cancel** para backup de PST grande (cancelar perde progresso), alerta de confirmação ao cancelar, ritmo honesto na barra. É o core do app.

## Seção 16 — Notifications

- Erro = alerta; notificação = banner/badge (componentes diferentes).
- App em primeiro plano não "notifica" — insira dados na view atual.
- Badge atualiza imediatamente; zero = limpa.
- Canal por urgência: passivo → banner → alerta.
- Web: toast não-bloqueante `aria-live="polite"`, auto-dismiss 4s + fechar. **Nunca `alert()` nativo para info não-crítica.**

## Seção 17 — Empty States & Search

- Empty state: título + explicação + próximo passo acionável.
- Search: placeholder descritivo, "sem resultados" com sugestões.
- Valores: ícone 48–64pt, cor secondary; título Title2/3; texto Subheadline secondary; CTA primário.
- Search field: altura 36/28pt; radius 8px; lupa à esquerda; × à direita.
- Web: tabela vazia — ícone + título ("Nenhum backup") + texto + botão ("Executar Backup").
- Search com debounce **250–300ms**; `aria-label`; "Nenhum resultado para 'x'".

## Fontes

HIG Feedback, Progress Indicators, Notifications, Empty States; lacuna 17.
