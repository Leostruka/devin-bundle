# MILESTONE 2 / ISSUE 05: `scripts/design-lint-gate.py` - hook PostToolUse em writes de UI

Status: resolved · Source: padrao `npx impeccable detect` (exit codes) + huashu `design_lint.py` (severities) · Matrix: `.devin/research/MILESTONE_NEXTGEN_MATRIX.md` sec C (gate) · Blocked-by: M2_02 · Blocks: none

## Contexto & Valor

- Hoje nada barre slop de UI no ato do write; a deteccao depende do agente lembrar de auditar.
- Valor: gate deterministico e barato (stdlib, <200ms) que sinaliza no PostToolUse - o hook NUNCA bloqueia build/commit, so emite aviso tipado no stderr.

## Brain (Skill)

- Nenhuma; documentar no `impeccable` (M2_03) que o gate existe e como ler `[DESIGN-LINT]` no stderr.

## Muscle (Hook + Extension)

- `scripts/design-lint-gate.py` (stdlib-only per ARCHITECTURE_MANIFEST):
  - stdin = payload do hook; so age em `write|edit` cujo path casa `*.{html,css,tsx,jsx,vue,svelte}` (ou conteudo com markers de UI).
  - Subconjunto ~12 regras baratas via regex/`html.parser` inline (nao importa de extensions/ - forbidden crossing; regras duplicadas minimalistas: purple-gradient hex/hue ranges, `background-clip:text`+gradient, font-family Inter/Roboto/Geist, border-accent>=3px com radius, eyebrow pattern `<small>`/uppercase-label, em-dash density, cards-aninhados heuristico, tailwind slop classes comuns).
  - Saida: `[DESIGN-LINT] <rule-id>: <file>:<line>` em stderr; exit sempre 0 (fail-open per error model).
  - Timeout no hooks.v1.json: <=15s (matcher existente `^(write|edit)$` PostToolUse; adicionar hook na lista).
- `hooks.v1.json`: adicionar entrada PostToolUse para `design-lint-gate.py` (junto de `memory-post-edit`/`compact-gate`).

## Step-by-step

0. Implementar script com ~12 regras; self-test em fixtures.
1. Registrar em `hooks.v1.json` + `manifest.json` script list; rodar `render-user-hooks.py` dry-run.
2. Gate: `pytest` (contrato: hook presente no v1.json; regex casam fixture slop e nao disparam em clean); `audit.py` 0 errors; `bash -n install.sh`; PS tokenize ok.

## Non-goals

Sem blocking (decision:block nunca); sem regras pesadas (AST/parse completo fica no M2_02 CLI); sem rodar em paths fora de UI; sem alterar `pre-write-guard.py`.

## Answer

- `scripts/design-lint-gate.py` - PostToolUse(write|edit) hook, stdlib, fail-open. 12 inline rules (no extension import per spec): ai-color-palette (purple+cyan hex in gradient), gradient-text, side-tab (>=4px accent), overused-font (Inter/Roboto/Geist/Fraunces/Poppins), border-accent-on-rounded, em-dash-overuse (>5), marquee, hero-eyebrow-chip, marketing-buzzword, skipped-heading, hard-offset-shadow, pulsing-dot. Path filter: only .html/.css/.tsx/.jsx/.vue/.svelte; skips node_modules/vendor/dist/build/extensions/fixtures; >400KB skipped. Output `[DESIGN-LINT] rule: file:line` via additionalContext; exit always 0.
- `hooks.v1.json`: added to existing PostToolUse `^(write|edit)$` matcher (timeout 10 <= 15).
- manifest.json: script entry + script_count 39->40; README/TOOLS-MAP/HOOKS-PIPELINE counts + row synced.
- 7 contract tests: registered-in-v1, slop warns (additionalContext), clean silent, non-UI silent, fail-open on garbage/missing, fixtures skipped, em-dash+marquee.

Gates: 7/7; verified end-to-end with real subprocess stdin (3 findings on seeded slop css, silent on clean/non-UI/garbage).
