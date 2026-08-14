# Spacing & Layout (checklist 12–18) — HIG seção 3

## Fatia do checklist

| # | Item | PASS |
|---|---|---|
| 12 | Grade 4/8px; sem valores arbitrários | todo `padding/margin/gap` usa `--space-*` (múltiplos de 4/8) |
| 13 | Margens de página ≥20px | padding do container principal ≥20px |
| 14 | Forms com label/controle em colunas; gap 8px | `grid-template-columns` + gap 8px label→controle |
| 15 | Seções ≥12px | separação entre seções 12–24px |
| 16 | Texto descritivo ~60ch | descrições com `max-width: 60ch` |
| 17 | Responsivo ~800px e ~400px | layout testado nas duas larguras; sidebar colapsa |
| 18 | Nada crítico no rodapé | ações importantes nunca no footer |

## Valores

- **Grade base 8pt** (múltiplos de 4). **(oficial/community)**
- Margens de janela macOS: **20pt** L/R/B; topo 14pt (sem tab) / 12pt (com tab). **(community)**
- Padding interno GroupBox: **16pt**; separação de seções: **12–24pt**. **(community)**
- Label→controle: **8pt**; controles empilhados ≥6pt. **(community)**
- Sidebar: min **225–275pt**, max **350–400pt**. **(community)**
- Divisor split view: **1pt**. **(oficial)**
- Linha de texto ideal: **~40–60 caracteres**.

## Aplicação web — tokens

- `--space-1: 4px` · `--space-2: 8px` · `--space-3: 12px` · `--space-4: 16px` · `--space-5: 20px` · `--space-6: 24px` · `--space-8: 32px` · `--space-12: 48px`.
- Settings: padding 20px; seções separadas 12–24px; gap 8px label→controle.
- Dashboard: sidebar 240–280px; dividers 1px; `max-width: 60ch` para descritivos.

## Guardrails de layout

- NUNCA valor de espaço fora da grade (ex.: 7px, 13px, 21px).
- NUNCA informação crítica no rodapé da janela.
- NUNCA `maximum-scale`/`user-scalable=no` (item 6 acessível por zoom).

## Lacuna aplicável

- **Lacuna 3 (Split Views)**: panes com divisores redimensionáveis e min/max de pane — regra completa em `hig-settings-navigation/references/settings-navigation.md` (aqui fica só o valor 1pt de divisor e larguras de sidebar).
