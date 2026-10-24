# MILESTONE 2 / ISSUE 03: `skills/impeccable` upgrade - PRODUCT/DESIGN spec + protocolo huashu + wiring de musculo

Status: planned · Source: github.com/pbakaus/impeccable (Apache-2.0, v4.7.0; `skill/reference/document.md`) + github.com/alchaincyf/huashu-design (MIT; `references/{workflow,directions,design-context}.md`) · Matrix: `.devin/research/MILESTONE_NEXTGEN_MATRIX.md` sec B#4/B#5/C · Blocked-by: M2_01, M2_02 · Blocks: M2_14

## Contexto & Valor

- Nossa port tem 22 comandos e contexto informal. Upstream tem spec formal: `PRODUCT.md` (verdade duravel: Platform/Users/Purpose/Positioning/Capabilities-and-Constraints, proibe claims inventados) vs `DESIGN.md` (sistema visual, frontmatter YAML de tokens normativo + secoes fixas estilo Google Stitch).
- huashu traz o protocolo de direcao que falta: sec0 fact-verify -> `product-facts.md`; 5 Form Questions; gate de 3 direcoes (6 candidatos -> 3 reais + 3 alternativas) com `direction-approved.md` e isencoes verbatim.
- Valor: brain unica que comanda muscle real (search.py/design_lint.py) e produz artefatos de direcao auditaveis - sem criar skill nova.

## Brain (Skill)

- `skills/impeccable/SKILL.md` update-in-place:
  - Sync de comandos com upstream verificado (22->24; confirmar lista exata antes de escrever - contagem 23/24 divergente nas fontes).
  - `init`/`document`: emitir PRODUCT.md + DESIGN.md conforme spec (YAML tokens normativos, ordem de secoes fixa).
  - `shape`: adiciona sec0 fact-verify (WebSearch sobre produto/versoes -> `product-facts.md`; pergunta ao usuario se nao-verificavel) + 5 Form Questions (papel narrativo, distancia de audiencia, temperatura visual, capacidade/densidade, motivo visual) + gate de direcao com `direction-approved.md`.
  - `audit`/`critique`: chama `design_lint.py` (musculo) como primeiro passo deterministico; LLM so julga o restante.
  - `colorize`/`typeset`/`layout`: consulta `search.py --domain` antes de propor.
  - Boundaries: isencoes do gate de direcao sempre verbatim em `direction-approved.md`.

## Muscle (Extension)

- Nenhum novo - consome `design-intelligence` (M2_01/02).

## Step-by-step

0. Ler `skill/reference/document.md` e `plugin/skills/impeccable/SKILL.md` upstream (commit pinado) -> diff de comandos.
1. Reescrever SKILL.md: spec PRODUCT/DESIGN, sec0, 5FQ, gate de direcao, wiring de musculo.
2. `writing-skills` checklist + `validate-skill-format.py`.
3. Gate: `pytest` + `audit.py`; teste de contrato cobre novos tokens (direction-approved, product-facts, PRODUCT.md); skill simulada end-to-end em 1 surface de exemplo.

## Non-goals

Sem novo skill dir; sem alterar comandos alem do sync verificado; sem acoplar a npx (musculo e o port local M2_02).
