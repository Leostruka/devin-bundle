# MILESTONE 2 / ISSUE 04: brain upgrades - `creative-engineering` + `agents/art-director.md`

Status: planned · Source: github.com/vercel-labs/agent-skills (MIT) + github.com/alchaincyf/huashu-design (MIT) · Matrix: `.devin/research/MILESTONE_NEXTGEN_MATRIX.md` sec B#2/B#4/C · Blocked-by: M2_01 · Blocks: M2_14

## Contexto & Valor

- `creative-engineering` escolhe arquetipo por nome/alias e le o arquivo inteiro; nao ha etapa de retrieval nem mapeamento de intencao de forma.
- `art-director` (perfil 03 da agency DAG) nao tem gate de direcao, nao cita regras de framework e nao responde as 5 Form Questions.
- Valor: retrieval deterministico antes de ler anatomia (contexto menor, selecao auditavel) e contrato de direcao alinhado com M2_03.

## Brain (Skill/Profile)

- `skills/creative-engineering/SKILL.md`:
  - Passo 0: `python extensions/design-intelligence/search.py "<brief>" --domain styles` ANTES de ler arquivo de arquetipo; `index.json` permanece camada de alias.
  - Mapear 5 Form Questions -> corpus: motivo->arquetipo; temperatura->colors.csv; capacidade->density dial; distancia->typography; papel->stacks ruleset.
  - Passo de implementacao web: consultar `data/frontend-rules/` via search para regras React/Next aplicaveis.
- `agents/art-director.md`:
  - `<deep_analysis>` += 5 Form Questions explicitas.
  - Output contract += evidencia de direcao (`direction-approved.md` referenciado ou 3-real+3-alt).
  - Citacao de `frontend-rules` quando stack em docs/02 = React/Next/RN/Expo.
  - Manter contrato v3 (upstream_hashes, DRAFT, rework_cycle) intacto.

## Muscle (Extension)

- Nenhum - consome `design-intelligence` (M2_01).

## Step-by-step

0. Editar os 2 arquivos; manter estilo/frontmatter.
1. `validate-skill-format.py`; revisao `writing-skills`.
2. Gate: `pytest` + `audit.py`; teste de contrato: tokens novos presentes (search step, 5FQ, direction-approved, frontend-rules); art-director profile ainda parseia frontmatter v3.

## Non-goals

Sem mudar persona/modelo dos profiles; sem mover `knowledge_bases/aesthetics/`; sem criar skill nova.
