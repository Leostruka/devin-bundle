# Shapes (checklist 19) — HIG seção 4

## Fatia do checklist

| # | Item | PASS |
|---|---|---|
| 19 | Raios consistentes (8/10/10px) | controles 8px, cards 10px, badges 6px, large 20px; sem valores soltos |

## Princípios

- Cantos **contínuos** (superellipse); cápsulas para ações de destaque; rounded rect para controles densos.
- Cantos concêntricos: filho = pai − padding (cascata).
- Botão isolado: prefira cápsula.

## Valores **(community)**

- Controles **8px**; cards/sheets **10px**; "continuous large" **20px**.
- Capsule: radius = 50% da altura (botão 32px → 16px).

## Aplicação web — tokens

- `--radius-controls: 8px` · `--radius-cards: 10px` · `--radius-large: 20px` · `--radius-capsule: 999px`.
- Cascata: card 10px → botão 8px → badge 6px.

## Guardrail

- NUNCA `border-radius` solto (ex.: 12px, 6px de propósito próprio) sem justificativa e sem token.
