# Settings, Navegação, Botões, Menus, Toolbars (checklist 44–48) — HIG seções 11–15 + lacunas 2, 3, 7, 18

## Fatia do checklist

| # | Item | PASS |
|---|---|---|
| 44 | Settings por atalho (Ctrl+,) + botão; último pane restaurado | atalho presente; pane persistido |
| 45 | Navegação com estado atual (`aria-current`) | item ativo marcado |
| 46 | Salvar explícito OU automático, nunca ambos | um só esquema |
| 48 | Atalhos documentados | tooltips/ajuda |
| (47) | Empty states — co-dono `hig-feedback` | referência apenas |

## Seção 11 — Settings **(oficial)**

- Prefs em janela separada; atalho **⌘,** (Ctrl+, no Windows).
- Toolbar fixo com panes; pane ativo indicado; janela redimensiona por pane.
- **Restaurar o último pane**.
- Formulário: rótulo + controle em colunas; descreva o propósito de cada config.
- Salvar explícito OU automático — nunca ambos.
- Valores: gap label→controle 8pt; largura ~500–600pt; sidebar de settings min 225, max 400pt.
- Web: sidebar 240px + panes; `grid-template-columns: 180px 1fr`; labels com `for`; destrutivos separados por `<hr>`; desabilitados com `disabled` + `aria-disabled` + explicação.

## Seção 12 — Navigation

- Navegação invisível; sempre caminho claro; sidebar persiste seleção; `aria-current` no ativo.
- Modais só para tarefa focada; **não empilhe modais**; modal com input: Cancel com alterações → confirmação.
- Divisor 1pt; sidebar 225–275/350–400pt; transições 200–300ms fade/slide + reduced-motion.

## Seção 13 — Buttons

- **1–2 botões proeminentes por view**; primary no mais provável; Enter aciona.
- Botão com delay: spinner interno + label trocado.
- Rótulo começa com verbo; "…" quando abre outra janela.
- Alturas: touch ~44px; desktop ~32px; espaçamento macOS ≥12pt (regular)/≥10pt (small)/≥8pt (mini). **(oficial-legado)**
- Web: primário accent + `:focus-visible` ring ≥2px; height ≥36px desktop / ≥44px touch; `type="button"` por padrão, primário `type="submit"`.

## Seção 14 — Menus & Keyboard

- Todo comando acessível por menu/atalho; atalhos padrão: ⌘C/V/X/Z/A/S/P/W/Q/, (Windows: Ctrl).
- Rótulo = ação que executa ("Excluir", não "Apagar registro").
- Itens show/hide refletem estado atual.
- **Lacuna 7 (Context Menus)**: itens frequentes primeiro; **desabilitados aparecem, não somem**. BackupEmail: menu na tabela — "Executar backup", "Copiar caminho", "Abrir destino".

## Seção 15 — Toolbars & Status Bars

- Toolbar 3 zonas: leading (navegação) | centro (controles) | trailing (ações importantes + primária).
- Trailing permanece visível; centro colapsa para overflow.
- Status: **passivo, próximo ao conteúdo**; nada de popup para status normal.
- Web: header fixo 3 zonas; status do backup na própria view (chip na linha) com `aria-live="polite"`; footer com contagem/último backup; ações críticas nunca no footer.

## Lacuna 2 — Lists & Tables (REAL)

HIG oficial (`/lists-and-tables`):
- Prefira **texto** em listas; seleção: navegação hierárquica = **highlight persistente**; lista de opções = highlight breve + checkmark.
- macOS: clique no cabeçalho **ordena** (reordena inverso se já ordenada); permita **redimensionar colunas**; linhas alternadas em tabela larga.
- Texto sucinto; "…" central se houver truncamento.

**BackupEmail**: tabela de PCs — ordenação por coluna clicável, redimensionamento, highlight persistente da linha, row alternada.

## Lacuna 3 — Split Views (PARCIAL)

- **Prefira split view a nova janela** para info suplementar — mantém contexto.
- Panes com divisores redimensionáveis; defina **min/max razoáveis** de pane.
- Sidebar: lado líder; considere tab bar quando espaço é limitado.

## Lacuna 18 — Undo/Redo & Destructive (PARCIAL)

- Pessoas esperam **desfazer ações recentes** — undo é rede de segurança.
- Destrutivas: confirmar intenção; vermelho; Cancel disponível.
- **BackupEmail**: "desfazer alterações não salvas" no settings (restaurar configuração anterior antes de salvar).

## Fontes

HIG Settings, Navigation, Buttons, Menus, Toolbars, Status Bars, Lists & Tables, Split Views, Undo & Redo, Context Menus; lacunas 2, 3, 7, 18.
