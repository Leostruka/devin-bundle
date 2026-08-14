---
name: apple-hig
description: Use quando o usuário pedir design review, auditoria ou redesenho da UI de um app desktop WPF + WebView2 (dashboard/settings) seguindo Apple HIG. WHAT: orquestra o pipeline — carrega references/app-context.md, roda as 6 skills na ordem (hig-foundations → hig-writing → hig-alerts → hig-feedback → hig-settings-navigation → hig-accessibility), executa scripts/audit-design.mjs e consolida relatório 52/52 com score por categoria e evidência arquivo:linha. WHEN: triggers "design review", "auditoria de UI", "refazer o dashboard", "refazer as settings", "revisão de interface", "está seguindo o HIG?", "está nos padrões da Apple?", "relatório HIG", "52 itens". NÃO use para: corrigir problema pontual e isolado (tipografia, cor, grade 8px, radius, motion, alerta, feedback, progresso, settings, navegação, atalho, acessibilidade, contraste, copy) — use a skill específica da família; nem para UI nova do zero sem revisão — comece pela skill do domínio.
version: 1.0.0
family: apple-hig
target: wpf-webview2
---

# Apple HIG — Design Review Orquestrador

Pipeline completo de design review da UI do BackupEmail (dashboard + settings, WPF + WebView2) contra Apple HIG, consolidando as 6 skills da família em um relatório **52/52** com score por categoria e evidência rastreável.

## Quando usar

- Revisão/auditoria da UI inteira ou de uma tela (dashboard, settings).
- Usuário pede "design review", "auditoria de UI", "refazer o dashboard", "relatório HIG", "está nos padrões da Apple?".
- Antes de marcar a UI como pronta/entregável.
- Comparação entre duas versões da UI.

## Quando NÃO usar

- Problema pontual e isolado → use a skill do domínio (ver tabela de roteamento abaixo). NÃO rode o pipeline inteiro para trocar um radius.
- Ajuste de copy de um único botão → `hig-writing`.
- Decisão de negócio/arquitetura que não toca UI.

## Contexto obrigatório

Leia **references/app-context.md primeiro** (mapeamento BackupEmail, seção 20 + lacunas específicas do app: ícone/tray, launch state). Leia **references/checklist-master.md** — índice canônico dos 52 itens com o dono de cada fatia. Nunca rode as skills sem esse contexto.

## Domínios e roteamento (progressive disclosure)

| Domínio | Skill | Fatia do checklist | Quando usar a skill sozinha |
|---|---|---|---|
| Tipografia, Cor, Layout, Shapes, Ícones, Motion | `hig-foundations` | itens 1–25 | "tipografia", "cor", "grade 8px", "radius", "motion" |
| Copy/UX Writing, erros de campo, secure fields | `hig-writing` | itens 49–50 (+ copy de 34, 47) | "copy", "texto de botão", "mensagem de erro" |
| Alertas, sheets, tooltips, destrutivas | `hig-alerts` | itens 33–38 | "alerta", "modal", "confirmação", "destrutivo" |
| Feedback, Progresso, Notificações, Empty states | `hig-feedback` | itens 26–32, 47 | "feedback", "progresso", "loading", "toast", "pause" |
| Settings, Navegação, Botões, Menus/Teclado, Toolbars | `hig-settings-navigation` | itens 44–48 | "settings", "atalho", "navegação", "tabela", "undo" |
| Acessibilidade, Plataforma desktop, Privacy, Onboarding, Help | `hig-accessibility` | itens 39–43 | "acessibilidade", "contraste", "focus", "privacy" |

Instrução de leitura: dentro de cada skill, leia **apenas o reference do domínio afetado** — os references carregam o peso; o corpo da skill tem só princípios.

## Processo: 6 etapas

1. **Carregar contexto** — ler `apple-hig/references/app-context.md` + `checklist-master.md`.
2. **Rodar as 6 skills na ordem fixa**: foundations → writing → alerts → feedback → settings-navigation → accessibility. Cada uma produz seu slice com evidência **PASS/FAIL + arquivo:linha + valor**.
3. **Rodar o script determinístico** `scripts/audit-design.mjs <caminhos dos arquivos HTML/CSS/JS>` (quando os arquivos existirem) e anexar a saída.
4. **Consolidar** os slices em 52/52 — itens co-ocupados (47, pertencente a `hig-feedback` e referenciado por `hig-settings-navigation`) contam uma única vez com evidência combinada.
5. **Score por categoria** (Tipografia, Cor, Layout, Shapes, Motion, Feedback, Alertas, A11y, Settings, Consistência).
6. **Relatório final**: tabela item × status × evidência × fonte HIG + resumo executivo.

## Princípios orquestradores

- Evidência obrigatória: todo FAIL cita `arquivo:linha` e o valor encontrado. "Está bom" não é review.
- O script reporta, nunca corrige — a correção é feita depois, skill por skill.
- A fatia de cada skill é a única autoridade do item; não re-auditar o que já foi auditado.

## Guardrails

- NUNCA despejar o bloco de 52 itens inteiro dentro de uma skill — sempre fatiado (3–8 por skill).
- NUNCA pular o `app-context.md` — sem contexto o review fica genérico e fora do domínio do app.
- NUNCA corrigir dentro do `audit-design.mjs` (não altera arquivos) nem inventar tokens não definidos no contrato.
- NUNCA contar item 47 duas vezes no total.

## Exemplos

- **Bom**: `FAIL · item 7 (contraste) · dashboard.html:214 · texto #8A8A8A sobre #F5F5F5 = 3.2:1 (precisa ≥4.5:1) · fonte HIG Color.`
- **Ruim**: `item 7 — contraste está ok.` (sem linha, sem valor, sem fonte — inverificável).

## Checklist do orquestrador (itens transversais + gates de processo)

- **[O1 · item 51] Estado do backup sempre cor+ícone+texto** — PASS: nenhum indicador de status usa só cor → verificação: procurar classes `.ok/.error/.running/.warning` e confirmar ícone+texto adjacente. Fonte: HIG Color.
- **[O2 · item 52] Alertas nunca para pura informação** — PASS: todo `alert()`/`<dialog>` tem ação ou erro crítico → verificação: grep e leitura do contexto. Fonte: HIG Alerts.
- **[O3] Contexto aplicado** — PASS: evidências citam o app (pane de settings, tabela de PCs, barra de backup) → verificação: leitura do relatório.
- **[O4] 6 skills executadas em ordem** — PASS: cada fatia tem resultado registrado → verificação: checklist de execução.
- **[O5] Evidência rastreável** — PASS: todo FAIL tem `arquivo:linha` + valor → verificação: amostra de 5 Fails.
- **[O6] Script executado (se aplicável)** — PASS: saída do `audit-design.mjs` anexada quando existirem HTML/CSS/JS → verificação: log.

## Failure modes

- Skills rodadas fora de ordem → evidências conflitantes (ex.: acessibilidade auditada antes de foundations muda os tokens).
- Evidência vaga ("está bom") → relatório não reproduzível; replique exigindo arquivo:linha.
- Script sem arquivos → erro de uso; passe os caminhos dos recursos do dashboard.
- Item 47 contado 2× → total >52; dedupe com o checklist-master.

## Related Skills

- `hig-foundations` — base visual; rode primeiro (define os tokens que as demais verificam).
- `hig-writing` — copy; alimenta os exemplos de erro de 30, 34, 47.
- `hig-alerts` — modal/confirmação; dialoga com feedback (lacuna 17 exige alerta de confirmação).
- `hig-feedback` — progresso/estados; dialoga com alerts (erro = alerta, não toast).
- `hig-settings-navigation` — estrutura de panes/botões; dialoga com writing (labels) e alerts (destrutivas).
- `hig-accessibility` — validação final de foco/contraste; consome as decisões das anteriores.
