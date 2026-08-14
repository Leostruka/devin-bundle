---
name: hig-accessibility
description: Use quando o usuário pedir para revisar ou implementar acessibilidade, plataforma desktop, privacidade, onboarding e ajuda da UI WebView2 (dashboard/settings do BackupEmail) seguindo Apple HIG. WHAT: audita a fatia 39–43 do checklist com evidência arquivo:linha — alvos ≥44px touch/≥28px mouse, foco visível em tudo (:focus-visible), tab order lógico + teclado completo, labels associados, ícones decorativos aria-hidden e tabelas com cabeçalhos; aplica lacunas 5 (focus model), 8 (onboarding), 9 (privacy), 10 (i18n) e 14 (help). WHEN: triggers "acessibilidade", "contraste", "focus", "foco", "screen reader", "leitor de tela", "teclado", "privacy", "privacidade", "onboarding", "help", "ajuda", "i18n". NÃO use para: contraste como problema de cor/tokens — use hig-foundations; copy — use hig-writing; estrutura de alerta — use hig-alerts.
version: 1.0.0
family: apple-hig
target: wpf-webview2
---

# HIG Accessibility & Platform — Acessibilidade, Desktop, Privacy, Onboarding, Help

Validação final (checklist 39–43 + lacunas 5, 8, 9, 10, 14). Consome as decisões das outras skills.

## Quando usar

- Auditar foco, teclado, leitor de tela, alvos de clique, contrastes e labels.
- Validar foco de linha em listas (lacuna 5) e foco-visible em controles.
- Revisar privacy (o que o app coleta/pede), onboarding de primeiro uso, help in-context e preparação i18n.

## Quando NÃO usar

- Contraste/cores como problema de tokens → `hig-foundations`.
- Copy de labels/erros → `hig-writing`.
- Estrutura de modal (focus trap) → `hig-alerts`.
- Tabela ordenável/context menu → `hig-settings-navigation`.

## Contexto obrigatório

Leia **references/app-context.md** (app é pt-BR, desktop Windows, WebView2; docs externos de manual existem mas falta ajuda in-app). Leia **references/accessibility.md** (seções 18–19 + lacunas 5,8,9,10,14) — valores; este corpo só tem princípios.

## Domínios

| Domínio | Reference | Fatia do checklist |
|---|---|---|
| Acessibilidade base | `references/accessibility.md` | 39–43 |
| Focus model & teclado | `references/accessibility.md` | lacuna 5 |
| Plataforma desktop (janela/sheets) | `references/accessibility.md` | seção 19 |
| Privacy | `references/accessibility.md` | lacuna 9 |
| Onboarding | `references/accessibility.md` | lacuna 8 |
| Help & documentation | `references/accessibility.md` | lacuna 14 |
| Localização / RTL | `references/accessibility.md` | lacuna 10 |

## Princípios

- Contraste AA em light E dark (com Increase Contrast e Reduce Transparency).
- **Nunca só cor** — texto/ícone/forma como redundância.
- Suporte aumento ≥200% sem quebrar layout; **não desabilite zoom**.
- Screen readers: tudo legível; labels + hints; teclado completo; foco visível.
- **Focus ring em text/search fields; highlight na linha inteira em listas/coleções** — não anel em volta de célula (lacuna 5).
- Focar um item geralmente **também o seleciona** (exceção: ações que trocariam contexto).
- Privacy: solicite **apenas o que o app precisa**; permissões específicas no momento certo; transparência sobre coleta/uso.
- Onboarding: **depois do launch**, rápido, opcional; ensine por interatividade, não por texto.
- Help: disponível **quando e onde a pessoa precisa** — dicas contextuais, não manual à parte.

## Guardrails

- NUNCA `maximum-scale`/`user-scalable=no` (o `audit-design.mjs` marca CRÍTICO).
- NUNCA ocultar foco (`outline: none` sem `:focus-visible`).
- NUNCA `aria-hidden` em conteúdo focado/interativo.
- NUNCA alvo <24px (WCAG 2.2); ideal ≥44px touch / ≥28px mouse.
- NUNCA onboarding no launch (deve ser pós-launch e opcional).
- NUNCA pedir permissão/coletar antes do interesse do usuário (lacuna 9).

## Exemplos

- **Bom**: foco de linha na tabela de PCs — `:focus-visible` na `<tr>` com highlight de linha inteira (lacuna 5), sem ring em volta da célula.
- **Ruim**: `outline: none` com ring apenas no clique do mouse (mouse-only focus).
- **Bom**: dica contextual no primeiro uso: `"Primeiro backup — execute para proteger seus PSTs"` com botão "Pular" (lacuna 8).
- **Ruim**: carrossel de onboarding obrigatório antes de qualquer tela.
- **Bom**: settings com link "O que este app armazena?" explicando config/status/logs (lacuna 9).
- **Ruim**: pedir acesso à rede no primeiro segundo, sem contexto.

## Checklist do domínio

- **[39] Alvos ≥44px (touch)/≥28px (mouse)** — PASS: botões/rows ≥36px desktop e ≥44px touch → verificação: medição + CSS. Fonte: HIG Accessibility.
- **[40] Foco visível em tudo** — PASS: `:focus-visible` ring 2px + offset 2px em todos os controles → verificação: `audit-design.mjs` + tabulação. Fonte: HIG Accessibility.
- **[41] Tab order lógico; teclado completo** — PASS: tab percorre labels→controles→ações; Esc fecha modais → verificação: tabulação manual. Fonte: HIG Accessibility.
- **[42] `<label>` associado; obrigatórios indicados** — PASS: todo input com `for`/`id`; obrigatório sinalizado → verificação: grep + leitura. Fonte: HIG Accessibility.
- **[43] Ícones decorativos aria-hidden; tabelas com cabeçalhos** — PASS: `aria-hidden="true"` em decorativos; `<th>` nas tabelas → verificação: leitura. Fonte: HIG Accessibility.
- **[L5] Focus de lista = highlight de linha, não ring** — PASS: foco em lista/tabela realça a linha inteira → verificação: tabulação. Fonte: lacuna 5.

## Failure modes

- Foco visível só no mouse (não no teclado) — item 40 falha.
- `aria-hidden` acidental em elemento com foco — leitor entra em loop.
- Onboarding obrigatório dentro do launch (lacuna 8).
- Help só em manual externo, sem dica in-context (lacuna 14).

## Related Skills

- `hig-foundations` — tokens de cor/contraste (itens 7–10) e motion reduced-motion (23).
- `hig-alerts` — focus trap e `role="alertdialog"` dos modais.
- `hig-settings-navigation` — tabelas (cabeçalhos/ordenação) e menus por teclado.
- `hig-feedback` — `aria-live`/`aria-busy` dos estados.
- `apple-hig` — consolida 39–43 no relatório 52/52.
