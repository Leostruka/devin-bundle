# Ícones (checklist 20–21) — HIG seção 6

## Fatia do checklist

| # | Item | PASS |
|---|---|---|
| 20 | Ícones mesmo stroke (1.5–2px) | todas as bibliotecas com `stroke-width: 1.5–2` consistente |
| 21 | Botões de ícone com aria-label/tooltip | todo `<button>` só-ícone tem `aria-label` (e tooltip de hover) |

## Princípios

- Simples, reconhecíveis, universais; consistência total (mesmo peso de stroke).
- Combine peso do ícone com texto adjacente.
- Outline em toolbars/listas; **fill para seleção com accent**.
- Vetor, **nunca PNG**.

## Valores

- 9 pesos: 100–900. 3 escalas: small/medium/large.
- Ícone mínimo legível: **16×16px**.

## Aplicação web

- Biblioteca stroke único (Lucide/Feather, `stroke-width: 1.5–2`).
- Grid 24px toolbar; 16px inline; 32px empty states.
- Ícones decorativos: `aria-hidden="true"`; ícones informativos: `aria-label` ou texto adjacente.

## Lacuna aplicável

- **Lacuna 4 (Tooltips)**: tooltip no hover descreve o controle só-ícone (atalhos) — regra completa em `hig-alerts/references/alerts.md`; aqui só a exigência de `aria-label`.
