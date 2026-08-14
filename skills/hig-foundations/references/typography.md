# Tipografia (checklist 1–6) — HIG seção 1

> Valores marcados **(oficial)** do HIG/WWDC; **(community)** a validar. WebView2 em Windows: 1pt ≈ 1px em DPI 96.

## Fatia do checklist

| # | Item | PASS |
|---|---|---|
| 1 | Nenhum texto < 11px em conteúdo normal | nenhum `font-size` < 11px fora de tokens |
| 2 | Escala limitada a 5–7 estilos em tokens; nenhum font-size arbitrário inline | todo `font-size` via `var(--text-*)` |
| 3 | Corpo line-height ≥1.4; títulos ≥1.2 | `--text-body: 13px/16px`; títulos `line-height: 1.2` |
| 4 | Hierarquia por peso+tamanho, não só cor | tamanhos/pesos distintos entre níveis |
| 5 | Títulos grandes no topo; metadata 11–12px | header usa `--text-title1`; metadados `--text-footnote` |
| 6 | Zoom escalável (rem), sem maximum-scale restritivo | tamanhos em `rem`; sem `user-scalable=no` |

## Mínimos **(oficial)**

- Texto ≥ **11 pt** (iOS) / **10 pt** (macOS) — abaixo fica ilegível.
- Corpo (Body): **17 pt** iOS / **13 pt** macOS. **Nunca use tamanho iOS em UI desktop.**

## Escala macOS **(oficial)**

| Estilo | Peso | Tamanho (pt) | Line height (pt) |
|---|---|---|---|
| Large Title | Regular | 26 | 32 |
| Title 1 | Regular | 22 | 26 |
| Title 2 | Regular | 17 | 22 |
| Title 3 | Regular | 15 | 20 |
| Headline | Bold | 13 | 16 |
| Body | Regular | 13 | 16 |
| Callout | Regular | 12 | 15 |
| Subheadline | Regular | 11 | 14 |
| Footnote | Regular | 10 | 13 |
| Caption 1 | Regular | 10 | 13 |
| Caption 2 | Medium | 10 | 13 |

## Aplicação web (WebView2) — tokens

- `--text-title1: 22px` · `--text-title2: 17px` · `--text-title3: 15px` · `--text-headline: 13px/16px` · `--text-body: 13px/16px` · `--text-callout: 12px/15px` · `--text-subheadline: 11px/14px` · `--text-footnote: 10px` · `--text-caption1/2: 10px` (escala macOS).
- `font-size` em `rem`; suporte a `prefers-reduced-motion` e `prefers-contrast: more`.
- Peso: Regular 400, Medium 500, Semibold 600, Bold 700, Heavy 800.
- Letter-spacing: 17px → −0.43px; 13px → −0.08px; 11px → +0.06px.
- line-height: 1.2–1.3 títulos; 1.4–1.5 corpo.
- Dynamic Type: UI deve suportar ≥200% de aumento sem quebrar.

## Lacuna aplicável

- **Lacuna 10 (Localization)**: strings centralizadas (i18n) para pt-BR, sem texto hardcoded — afeta largura/tamanho dos rótulos ao traduzir.
