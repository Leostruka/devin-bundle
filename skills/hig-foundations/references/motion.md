# Motion (checklist 22–25) — HIG seção 7

## Fatia do checklist

| # | Item | PASS |
|---|---|---|
| 22 | Durações 120/200/300ms; nada >500ms sem propósito | durações via `--dur-fast/base/slow`; raras exceções documentadas |
| 23 | Reduced-motion desativa zoom/scale/spin (mantém fades) | `@media (prefers-reduced-motion)` troca transform por fade/color shift |
| 24 | Nada piscando em loop sem controle | nenhuma animação infinita sem `prefers-reduced-motion` e sem controle |
| 25 | Transições transform/opacity | nenhum `transition: all` |

## Princípios

- **Springs** (não easing linear); bounce 0 = versátil; 15% = brisk; 30% perceptível; >0.4 exagerado.
- Consistência de caráter (app sério → sem bounce).
- **Reduce Motion**: reduza zoom/scale/movimento periférico; NÃO remova animação que carrega significado — troque por fade/color shift.
- Evite animações rápidas e repetitivas.

## Valores **(community)**

- Micro **100–200ms**; transições **200–300ms**; contexto **300–500ms**; modais ~300ms; hover/focus **100–150ms**.
- Easing: `cubic-bezier(0.25, 0.1, 0.25, 1)`.

## Aplicação web — tokens

- `--dur-fast: 120ms` · `--dur-base: 200ms` · `--dur-slow: 300ms`.
- Transições por propriedade (`transform`/`opacity`), **nunca `transition: all`**.
- Reduced motion: `*{animation-duration:0.01ms!important;transition-duration:0.01ms!important}`; spinner → texto estático.

## Guardrail

- NUNCA `transition: all` (o `audit-design.mjs` marca como CRÍTICO).
