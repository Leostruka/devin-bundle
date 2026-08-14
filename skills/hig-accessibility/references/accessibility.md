# Accessibility & Platform (checklist 39–43) — HIG seções 18–19 + lacunas 5, 8, 9, 10, 14

## Fatia do checklist

| # | Item | PASS |
|---|---|---|
| 39 | Alvos ≥44px (touch)/≥28px (mouse) | targets ≥36px desktop, ≥44px touch |
| 40 | Foco visível em tudo | `:focus-visible` ring 2px + offset 2px |
| 41 | Tab order lógico; teclado completo | tab labels→controles→ações; Esc fecha modais |
| 42 | `<label>` associado; obrigatórios indicados | `for`/`id`; sinalização |
| 43 | Ícones decorativos aria-hidden; tabelas com cabeçalhos | `aria-hidden="true"`; `<th>` |

## Valores **(oficial)**

| Plataforma | Controle default | Mínimo | Texto default | Texto mínimo |
|---|---|---|---|---|
| iOS/iPadOS | 44×44pt | 28×28pt | 17pt | 11pt |
| macOS | 28×28pt | 20×20pt | 13pt | 10pt |

- Contraste: ≤17pt → 4.5:1; 18pt+/bold → 3:1; ideal 7:1.
- Web: targets ≥24px (WCAG 2.2), ideal ≥44px; rows clicáveis com padding.
- `:focus-visible` ring 2px + offset 2px em todos os controles.
- `aria-label` em botões de ícone; `aria-live`/`aria-busy`; tab order lógico; Esc fecha modais.
- **Não desabilite zoom** (`maximum-scale` proibido); fontes em `rem`.

## Seção 19 — macOS Platform (desktop)

- Janela: frame + body; sistema lembra tamanho/posição; defina min/max.
- Preferências em janela própria, panes com toolbar fixo, ⌘, (Ctrl+, no Windows), restaurar último pane.
- Sheets (modais apegados à janela) para tarefas pequenas; não use alerta para info.
- Sidebar full-height; colapsa ao reduzir janela; nada crítico no rodapé.
- Menu bar 24pt; margens 20pt; gap 8pt; seção 12–24pt; divider 1pt.
- Web (WebView2): janela com estado persistente; sidebar colapsável com atalho (Ctrl+Shift+S); `<dialog>` com `showModal()`, Esc fecha, focus trap.

## Lacuna 5 — Focus & Keyboard (PARCIAL)

- **Focus ring em text/search fields; highlight na linha inteira em listas/coleções** — não anel em volta de célula.
- Focar um item geralmente **também o seleciona** (exceção: ações que trocariam contexto de forma distratora).
- Ponteiro altamente visível quando o app exige pointer.
- **BackupEmail**: highlight de linha inteira na tabela (não ring); evitar selecionar ao focar em ações de contexto.

## Lacuna 9 — Privacy (REAL)

- Solicite **apenas os dados que o app realmente precisa**; permissões o mais específicas possíveis.
- Transparência sobre coleta/uso; proteja dados do usuário.
- Pedir demais ou antes do interesse do usuário **corrói a confiança**.
- **BackupEmail**: segurança forte existe (ACL, constant-time auth, senhas nunca logadas) mas falta camada UX: explicar quais dados o app coleta/armazena (config, status, logs) e pedir acesso à rede/destino no momento certo, com texto claro em pt-BR.

## Lacuna 8 — Onboarding (REAL)

- Ocorre **depois do launch**; rápido, opcional (especialistas pulam).
- Ensine **por interatividade**, não por texto; dicas contextuais no momento do uso.
- **Não** faça onboarding parte do launch.
- **BackupEmail**: primeiro-uso não-bloqueante (dica contextual "Primeiro backup" + botão pular), separado do launch. Existe docs/PRIMEIRO-USO.md mas sem onboarding in-app.

## Lacuna 14 — Help & Documentation (REAL)

- Help disponível **quando e onde a pessoa precisa** — dicas contextuais, não manual à parte.
- Tooltip = descrição curta de como usar o componente no hover.
- **BackupEmail**: ajuda in-context no dashboard (tooltips nos controles, link "Como funciona" contextual); docs existem mas são externos.

## Lacuna 10 — Localization / RTL (REAL — baixa)

- Frameworks espelham UI em RTL automaticamente; espelhe controles de direção (sliders, progress, back); **não espelhe logos/checkmarks**.
- Alinhe parágrafo (≥3 linhas) pela **língua do texto**.
- **BackupEmail**: pt-BR (LTR) → RTL baixa prioridade; preparar i18n (strings centralizadas, sem texto hardcoded).

## Fontes

HIG Accessibility, macOS Platform, Focus & Selection, Privacy, Onboarding, Offering Help, Right-to-Left; lacunas 5, 8, 9, 10, 14.
