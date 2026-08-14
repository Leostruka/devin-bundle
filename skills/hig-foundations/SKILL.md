---
name: hig-foundations
description: Use quando o usuário pedir para auditar ou implementar os fundamentos visuais da UI WebView2 (dashboard/settings do BackupEmail) seguindo Apple HIG. WHAT: audita a fatia 1–25 do checklist com evidência arquivo:linha — tipografia (mínimo 11px, tokens --text-*), cor (contraste 4.5:1, semânticas com variantes dark), layout (grade 4/8px, --space-*, margens 20px), shapes (raios 8/10/20/999px), ícones (stroke 1.5–2px) e motion (120/200/300ms, só transform/opacity, reduced-motion). WHEN: triggers "tipografia", "cor", "grade 8px", "radius", "motion", "espaçamento", "ícone", "dark mode", "tokens", "grid". NÃO use para: alerta/modal/confirmação — use hig-alerts; progresso/loading/toast — use hig-feedback; foco/leitor de tela/contraste como recurso de acessibilidade — use hig-accessibility; copy de botões/erros — use hig-writing.
version: 1.0.0
family: apple-hig
target: wpf-webview2
---

# HIG Foundations — Tipografia, Cor, Layout, Shapes, Ícones, Motion

Base visual da UI (checklist 1–25). Esta skill define os **tokens** que as demais skills da família verificam — rode primeiro em qualquer trabalho que mude aparência.

## Quando usar

- Auditar/implementar tipografia, cor, espaçamento, raios, ícones ou motion.
- Criar/alterar o design system (tokens CSS em `:root`) do dashboard ou settings.
- Revisar contraste, dark mode ou grade de layout.

## Quando NÃO usar

- Alerta/modal/confirmação → `hig-alerts`.
- Progresso/loading/toast/empty states → `hig-feedback`.
- Foco, leitor de tela, teclado → `hig-accessibility`.
- Copy de botões e mensagens de erro → `hig-writing`.
- Tabelas ordenáveis, context menus, undo de settings → `hig-settings-navigation`.

## Contexto obrigatório

Leia **references/app-context.md** (mapeamento BackupEmail, contrato de tokens e status semanal) e **references/checklist-master.md** (fatia 1–25). Leia **apenas o reference do domínio afetado**; os references carregam os valores concretos, o corpo desta skill só tem princípios.

## Domínios

| Domínio | Reference | Fatia do checklist |
|---|---|---|
| Tipografia | `references/typography.md` | 1–6 |
| Cor & contraste | `references/color.md` | 7–11 |
| Spacing & Layout | `references/layout.md` | 12–18 |
| Shapes & radius | `references/shapes.md` | 19 |
| Ícones | `references/icons.md` | 20–21 |
| Motion | `references/motion.md` | 22–25 |

## Princípios

- **Tipografia**: nunca abaixo do mínimo legível; hierarquia = peso+tamanho; use estilos semânticos, não fontes hard-coded; escala limitada (5–7 estilos).
- **Cor**: cores descrevem propósito (semânticas), não valor; sempre variantes light+dark; nunca dependa só de cor para estado; dark ≠ inversão.
- **Layout**: alinhe tudo na grade 4/8; consistência = organização + hierarquia; nada crítico no rodapé.
- **Shapes**: cantos contínuos (superellipse); cápsulas para ações de destaque; cantos concêntricos (filho = pai − padding).
- **Ícones**: simples, universais, vetor; peso de stroke consistente; combine peso do ícone com o texto adjacente.
- **Motion**: springs, não easing linear; caráter do app define bounce; Reduce Motion troca zoom/scale por fade — não remove significado.

## Guardrails

- NUNCA inserir font-size/px/hex fora dos tokens do contrato (o `audit-design.mjs` avisa).
- NUNCA `transition: all` — anime só `transform`/`opacity`.
- NUNCA expressar estado (ok/erro/running) só com cor — sempre cor + ícone + texto.
- NUNCA `maximum-scale` / `user-scalable=no` — zoom deve escalar.
- NUNCA hard-code um token: se o valor se repetir, vire variável em `:root`.

## Exemplos

- **Bom**: `color: var(--text-primary); font-size: var(--text-body);` — escala via tokens, dark mode herda automaticamente.
- **Ruim**: `font-size: 14px; color: #444;` — quebra a escala de 5–7 estilos e o tema.
- **Bom**: `transition: transform var(--dur-fast) ease, opacity var(--dur-base) ease;`
- **Ruim**: `transition: all .3s;` — anima layout (thrashing) e viola o item 25.
- **Bom**: chip de status com `● verde + "OK"` (cor + ícone + texto).
- **Ruim**: linha `background: green` sem texto/ícone — inacessível (item 8).

## Checklist do domínio (amostra; fatia completa nos references)

- **[2] Escala tipográfica em tokens (5–7 estilos), sem font-size arbitrário** — PASS: todo `font-size` usa `var(--text-*)` → verificação: `audit-design.mjs` + grep. Fonte: HIG Typography.
- **[7] Textos ≥4.5:1 (AA) em light e dark; grande/bold ≥3:1** — PASS: menor par de cores do tema passa → verificação: medir pares `--text-*` sobre `--bg-*`. Fonte: HIG Color/Accessibility.
- **[12] Grade 4/8px; sem valores arbitrários** — PASS: todo `padding/margin/gap` usa `--space-*` → verificação: `audit-design.mjs`. Fonte: HIG Layout.
- **[19] Raios consistentes (8/10/20px)** — PASS: controles 8px, cards 10px, badges 6px → verificação: grep `border-radius`. Fonte: HIG Shapes.
- **[23] Reduced-motion desativa zoom/scale/spin (mantém fades)** — PASS: `@media (prefers-reduced-motion)` troca transform por opacity → verificação: leitura do media query. Fonte: HIG Motion.
- **[25] Transições transform/opacity** — PASS: nenhum `transition: all` → verificação: `audit-design.mjs` (crítico). Fonte: HIG Motion.

## Failure modes

- Token definido mas não usado (escala morta) → sempre grep de uso real.
- Só medir contraste no tema light → item 7 exige light E dark.
- Tratar dark como "inversão" de cor → deve ser "luzes apagadas", semânticas diferentes.
- Motion "perfeito" ignorando reduced-motion → falha item 23.

## Related Skills

- `apple-hig` — orquestrador; roda esta skill primeiro (define os tokens que as demais verificam).
- `hig-accessibility` — valida os tokens desta skill (contraste AA, alvos, focus-visible).
- `hig-feedback` — usa a paleta/motion aqui definidos para estados e progresso.
