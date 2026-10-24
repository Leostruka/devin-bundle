# MILESTONE 2 / ISSUE 08: `self-improvement` PPC upgrade - Propose-Probe-Compose + anti-leakage

Status: planned · Source: github.com/google-research/harness2 (Apache-2.0; `core/{recursion,schedule,tree,library_store}.py`, arXiv:2610.14224) · Matrix: `.devin/research/MILESTONE_NEXTGEN_MATRIX.md` sec B#1/E · Blocked-by: none · Blocks: M2_09

## Contexto & Valor

- Nosso refine/improvement-loop ja tem proposals e held-out, mas nao tem: classe de candidato (INV vs DOM), probe contrastivo na MESMA tarefa, compose de multiplos agregadores, e a regra de retencao `lib.retain(earlier-only)` que impede vazamento temporal entre licoes.
- harness2 formaliza: Propose (k invariantes + k domain), Probe (4k rollouts na mesma tarefa, evidencia comportamental, SEM ground truth), Compose (k composicoes independentes consomem o pool; adocao mantem refined-ou-base).
- Valor: loop de auto-evolucao com disciplina de benchmark real - fecha a lacuna entre "propos melhoria" e "adoto porque probe mostrou contraste".

## Brain (Skill)

- `skills/self-improvement/modes/improvement-loop.md`: adicionar fase PPC explicita - candidatos classificados INV (invariante do harness) vs DOM (dominio); probe = rodar candidatos na mesma tarefa-alvo e coletar evidencia; compose = agregadores independentes; adocao so quando contraste e positivo.
- `modes/refine.md`: proposal queue ganha campos `{class: INV|DOM, probe_evidence: <cmd+output>, contrast: +/-}`; licoes aceitas so com evidencia de contraste (espelha "supported by execution contrasts").
- Regra de retencao anti-leakage: licao/refinamento so pode citar evidencia ANTERIOR a si; adicionar check em `scripts/validate-refinement-evidence.py` (ordenar por ts, rejeitar citacao de evidencia futura/igual).
- `modes/harness-reference.md`: nova linha na tabela - harness2 PPC (adapted: improvement-loop+refine; extension: harness-tree M2_09).

## Muscle (Extension)

- Nenhum aqui; o engine de component-tree e M2_09. `validate-refinement-evidence.py` ganha o check de ordenacao temporal (stdlib).

## Step-by-step

0. Atualizar os 3 mode files + tabela harness-reference.
1. `validate-refinement-evidence.py` += check earlier-only + teste.
2. `validate-skill-format.py`; `writing-skills` checklist.
3. Gate: `pytest` (novo teste anti-leakage falha em cenario forjado); `audit.py` 0 errors; dry-run do loop em 1 proposta real registrando probe_evidence.

## Non-goals

Sem execucao de rollouts automaticos (probe e humano/agente guiado); sem sweep CLI; sem mudar `check-push-green.py`.
