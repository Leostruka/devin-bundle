# Cor & Contraste (checklist 7–11) — HIG seções 2 e 5

> Dark Mode (lacuna 15) já coberta nesta skill: cores semânticas, fundos base/elevated, variantes dark, dark ≠ inversão.

## Fatia do checklist

| # | Item | PASS |
|---|---|---|
| 7 | Textos ≥4.5:1 (AA) em light e dark; grande/bold ≥3:1 | menor par `--text-*`/`--bg-*` do tema ≥4.5:1 (ou ≥3:1 se ≥18pt/bold) |
| 8 | Nenhum feedback só com cor | todo estado tem texto/ícone/forma além da cor |
| 9 | Cores semânticas com variantes dark | `--bg-primary` etc. redefinidas em `@media (prefers-color-scheme: dark)` |
| 10 | Dark testado com Increase Contrast/Reduce Transparency | tema dark + `prefers-contrast: more` não quebra leitura |
| 11 | Destrutiva usa vermelho + rótulo explícito, nunca só cor | "Excluir" em vermelho; nunca só um ponto vermelho |

## Valores **(oficial)**

- Contraste: ≤17pt → **4.5:1**; ≥18pt/bold → **3:1**; recomendado **7:1** para texto pequeno.
- Hierarquia de label: primary → secondary → tertiary → quaternary.
- Fundos: **base** (dim) para interface; **elevated** (brilhante) para modais/popovers.
- 6 grays opacos (systemGray…6) para grids/linhas.
- Tint/accent: mais clara em Dark, mais escura em Light.
- **Nunca dependa só de cor** para estado (cor + ícone + texto).

## Aplicação web

- Tokens: `--bg-primary`, `--bg-elevated`, `--bg-secondary`, `--text-primary/secondary/tertiary`, `--separator`, `--accent` + variantes `*-dark` via `prefers-color-scheme`.
- Rows alternadas = `--bg-secondary`; modal = `--bg-elevated` + sombra.
- `@media (prefers-contrast: more)` para reforçar separação.

## Materiais / Glass (HIG seção 5)

- Translucidez em vez de opacidade; espessura = grau de separação (thin→thick).
- Web: `backdrop-filter: blur(20px) saturate(180%)` + `rgba(255,255,255,0.6)` light / `rgba(28,28,30,0.6)` dark; fallback sólido.
- **Nunca** adicione background custom a barras "para dar peso".

## Lacunas aplicáveis

- **Lacuna 15 (Dark Mode)**: já coberta — validar na prática com Increase Contrast/Reduce Transparency.
- **Lacuna 11 (App Icons)**: ícone do launcher/tray com camadas e borda definida — tratada em `apple-hig/references/app-context.md` (não é UI web).
