---
name: hig-settings-navigation
description: Use quando o usuário pedir para revisar ou implementar settings, navegação, botões, menus/teclado e toolbars da UI WebView2 (dashboard/settings do BackupEmail) seguindo Apple HIG. WHAT: audita a fatia 44–48 do checklist com evidência arquivo:linha — settings por atalho Ctrl+, com último pane restaurado, navegação com aria-current, salvar explícito OU automático (nunca ambos), empty states, atalhos documentados; aplica lacunas 2 (listas/tabelas ordenáveis), 3 (split views), 7 (context menus) e 18 (undo de settings). WHEN: triggers "settings", "atalho", "navegação", "botões", "menu", "teclado", "toolbar", "tabela", "sidebar", "undo". NÃO use para: alertas/confirmações — use hig-alerts; progresso/loading — use hig-feedback; copy — use hig-writing; layout/grade — use hig-foundations.
version: 1.0.0
family: apple-hig
target: wpf-webview2
---

# HIG Settings & Navigation — Settings, Navegação, Botões, Menus, Toolbars

Estrutura e comandos da UI (checklist 44–48 + lacunas 2, 3, 7, 18).

## Quando usar

- Revisar/implementar painel de settings (panes, salvar, undo), navegação (sidebar/aria-current).
- Revisar botões (primário, delay), menus/atalhos e toolbars (3 zonas).
- Revisar tabela do dashboard (ordenação, redimensionamento, seleção) e context menus.

## Quando NÃO usar

- Alerta modal/confirmação → `hig-alerts`.
- Barra de progresso/loading/toast → `hig-feedback`.
- Texto de rótulos → `hig-writing`.
- Grade/espaçamento/radius → `hig-foundations`.

## Contexto obrigatório

Leia **references/app-context.md** (settings = panes à esquerda, colunas `180px 1fr`, "Salvar Alterações" + toast; atalhos Ctrl+, e Ctrl+Shift+R). Leia **references/settings-navigation.md** (seções 11–15 + lacunas 2,3,7,18) — valores; este corpo só tem princípios.

## Domínios

| Domínio | Reference | Fatia do checklist |
|---|---|---|
| Settings & panes | `references/settings-navigation.md` | 44, 46 |
| Navegação & sidebar | `references/settings-navigation.md` | 45 |
| Listas & tabelas | `references/settings-navigation.md` | lacuna 2 |
| Split views | `references/settings-navigation.md` | lacuna 3 |
| Botões | `references/settings-navigation.md` | 13 (apoio) |
| Menus & teclado | `references/settings-navigation.md` | 48 |
| Context menus | `references/settings-navigation.md` | lacuna 7 |
| Undo de settings | `references/settings-navigation.md` | lacuna 18 |

## Princípios

- Prefs em janela separada; atalho **Ctrl+,**; toolbar fixo com panes; **restaurar o último pane**.
- **Salvar explícito OU automático — nunca ambos.**
- Navegação invisível; sempre um caminho claro (onde estou, como voltar); `aria-current` no item ativo.
- **1–2 botões proeminentes por view**; primary no mais provável; Enter aciona.
- Botão com delay: spinner interno + label trocado; rótulo começa com verbo; "…" se abre outra janela.
- Todo comando acessível por menu/atalho; atalhos padrão (Ctrl+C/V/X/Z/A/S/P/W/Q/,).
- Toolbar = 3 zonas (leading navegação | centro controles | trailing ações + primária).
- Prefira **split view a nova janela** para info suplementar (mantém contexto).
- Pessoas esperam **desfazer ações recentes** — undo é rede de segurança.

## Guardrails

- NUNCA salvar automático E explícito ao mesmo tempo (item 46).
- NUNCA esconder itens desabilitados de context menu — mostre desabilitado (lacuna 7).
- NUNCA selecionar ao focar em ações de contexto (lacuna 5 — dono accessibility).
- NUNCA coluna de tabela sem ordenação clicável quando a tabela é ordenável (lacuna 2).
- NUNCA ações críticas no rodapé (item 18 — dono foundations).

## Exemplos

- **Bom**: tabela de PCs — cabeçalho clicável ordena (inverte se já ordenado), colunas redimensionáveis, linha selecionada com highlight persistente (lacuna 2).
- **Ruim**: tabela estática sem ordenação nem seleção visível.
- **Bom**: settings com pane "Geral" persistido; alterações → botão "Salvar Alterações" + toast; "Descartar" restaura a configuração anterior (lacuna 18).
- **Ruim**: settings que salva a cada keystroke E tem botão salvar (item 46).
- **Bom**: context menu da linha — "Executar backup", "Copiar caminho", "Abrir destino" (frequentes primeiro); "Excluir" aparece desabilitado quando não aplicável (lacuna 7).
- **Ruim**: context menu com "Excluir" oculto quando não aplicável.

## Checklist do domínio

- **[44] Settings por atalho (Ctrl+,) + botão; último pane restaurado** — PASS: `Ctrl+,` abre settings; pane ativo persiste → verificação: interação + código. Fonte: HIG Settings.
- **[45] Navegação com estado atual (`aria-current`)** — PASS: item ativo da sidebar tem `aria-current="page"` → verificação: grep. Fonte: HIG Navigation.
- **[46] Salvar explícito OU automático, nunca ambos** — PASS: "Salvar Alterações" explícito; nenhum auto-save simultâneo → verificação: leitura do fluxo. Fonte: HIG Settings.
- **[48] Atalhos documentados** — PASS: `Ctrl+,`/`Ctrl+Shift+R` em tooltips/ajuda → verificação: leitura de tooltips. Fonte: HIG Menus.
- **[L2] Listas/tabelas: ordenação + redimensionamento + seleção** — PASS: cabeçalho ordena; colunas redimensionam; linha selecionada destacada → verificação: interação. Fonte: lacuna 2.
- **[L3] Split view em vez de janela nova; min/max de pane** — PASS: info suplementar na própria view; pane com limites → verificação: leitura do dashboard. Fonte: lacuna 3.

## Failure modes

- Pane de settings não restaurado (item 44).
- Dois esquemas de salvamento conflitantes (item 46).
- Context menu longo e desordenado (lacuna 7).
- Undo inexistente em settings (lacuna 18) e sem confirmação ao descartar.

## Related Skills

- `hig-alerts` — confirmação de alterações não salvas ao dispensar (lacuna 4).
- `hig-feedback` — barra de status na própria view (não popup); co-dono do item 47.
- `hig-writing` — rótulos dos botões e menus.
- `hig-accessibility` — foco/teclado dos menus (lacuna 5) e tabelas (cabeçalhos, item 43).
- `apple-hig` — consolida 44–48 no relatório 52/52.
