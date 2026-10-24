# MILESTONE 2 / ISSUE 02: `design_lint.py` - port deterministico das ~62 regras (impeccable + huashu)

Status: planned · Source: github.com/pbakaus/impeccable (Apache-2.0, v4.7.0; `cli/engine/registry/antipatterns.mjs`, `scripts/detector/rules/checks.mjs`) + github.com/alchaincyf/huashu-design (MIT; `scripts/design_lint.py`) · Matrix: `.devin/research/MILESTONE_NEXTGEN_MATRIX.md` sec B#4/B#5/C · Blocked-by: none · Blocks: M2_03, M2_05

## Contexto & Valor

- Nossa skill `impeccable` e texto: o detector deterministico upstream NUNCA foi portado. Upstream tem registro `ANTIPATTERNS` de ~62 regras executaveis sem LLM (~32 slop + ~27 quality +3 recentes) com CLI `npx impeccable detect --json`, exit 0/1/2.
- huashu-design tem `design_lint.py` (facts-only: broken images, small text, contraste, console errors) + look-ledger JSONL com `compare` anti-reskin.
- Valor: lint deterministico local de UI - barrar slop de IA sem gastar tokens, base do hook gate (M2_05) e do `audit`/`critique` (M2_03).

## Brain (Skill)

- Nenhuma. Consumo via skill acontece em M2_03.

## Muscle (Extension)

- `extensions/design-intelligence/design_lint.py` (mesma ext de M2_01):
  - `rules_registry.py` - tabela `ANTIPATTERNS` portada (id, category, name, description, scopes), gerada a partir do .mjs com hash de origem registrado.
  - `checks.py` - funcoes puras: `html.parser` + regex CSS para o subconjunto portavel (gradiente purple/cyan-on-dark, overused-font Inter/Roboto/Geist/Fraunces, border-accent-on-rounded, nested-cards, marquee, icon-tile-stack, eyebrow/kicker labels, em-dash-overuse, oversized-h1, low-contrast, tiny-text, skipped-heading, line-length, gray-on-color, design-system token violations...). Regras browser-dependentes (script-error, content-hidden-at-rest) ficam marcadas `scope: browser` e sao skipped no lint estatico.
  - CLI: `design_lint.py <dir|file> [--json] [--list-rules] [--ignore FILE]`; exit 0 clean / 1 erro / 2 findings; `ignores` persistidos.
  - `look_ledger.py` - JSONL ledger + `compare` (hash de estrutura visual: fontes+paleta+grid) para detectar reskin da mesma familia.
- `tests/fixtures/slop_*.html|css|tsx` com findings esperados por regra.

## Step-by-step

0. Extrair registro `ANTIPATTERNS` do upstream (pinned commit) -> `rules_registry.py`; contagem e categorias registradas no header.
1. Portar checks.mjs -> `checks.py` cobrindo primeiro as ~30 regras de estatica pura; marcar o resto `unported` explicitamente.
2. CLI + `--json` + exit codes; `--list-rules` confere contagem.
3. Fixtures: 1 arquivo limpo + N arquivos com 1 regra seedada cada; verde.
4. Gate: `pytest` + `audit.py`; `design_lint.py fixtures/` retorna findings esperados e exit 2; arquivo limpo exit 0.

## Non-goals

Sem execucao de browser/CDP; sem servidor npx; sem analise de screenshots; escopo estatico apenas (regras `scope: browser` ficam para issue futura).
