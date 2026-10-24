# MILESTONE 2 / ISSUE 14: `orchestrator_prompts` v4 - team guards PandaCode + direction contract

Status: planned · Source: github.com/aicodeking/pandacode (guards: silent->fail, 20min kill, <=20 rounds) + M2_03/04 (direction-approved.md) · Matrix: `.devin/research/MILESTONE_NEXTGEN_MATRIX.md` sec B#10/F, C · Blocked-by: M2_03, M2_04 · Blocks: none

## Contexto & Valor

- A DAG v3 (7 personas, asset-driven, upstream_hashes) nao cobre times mistos architect+workers nem o contrato de direcao de design que M2_03/04 introduzem.
- PandaCode prova guards operacionais: worker silencioso => falha reportada ao architect (nao retry cego); turn preso => kill em 20min; turn sem assignment => 1 nudge depois pausa; <=20 rounds; pausa/stop nunca consome retries.
- Valor: template de equipe 1-architect+<=3-workers com guards declarados na spec (nao improvisados), e 03_Art_Director passa a exigir `direction-approved.md` + 5FQ.

## Brain (Prompts/Profiles)

- `.devin/orchestrator_prompts_v3.md` (novo arquivo, supersede v2 - manter changelog como v2->v3 fez):
  - Secao TEAM pattern: architect decompoe em <=3 workers; tabela de guards (silent->fail-to-architect; kill@20min; no-assignment->nudge-once-then-pause; round-cap 20; pause nao consome retry).
  - Queue-vs-steer documentado (Devin CLI enfileira por natureza; "steer" = inject no proximo turno via intent file).
  - 03_Art_Director contract += direction-approved.md (3 real + 3 alt evidence) + 5 Form Questions + frontend-rules citation (espelha M2_03/04).
  - schema_version 3 mantido; `upstream_hashes` sem mudanca estrutural.

## Muscle (Extension)

- Nenhum; guards sao declarativos (executados pelo orquestrador/agente, nao por codigo novo).

## Step-by-step

0. Copiar v2 -> v3 file com changelog; aplicar deltas (team guards, direction contract, steer semantics).
1. Revisao de consistencia com `agents/*.md` (art-director.md ja atualizado em M2_04 - contratos devem casar).
2. Gate: `pytest` (contrato: tokens guards presentes; schema_version==3; referencias a direction-approved consistentes); `audit.py` 0 errors.

## Non-goals

Sem reescrita da DAG; sem novo profile; sem codigo de execucao de guards (declarativos); sem alterar os 7 personas existentes alem do contrato 03.
