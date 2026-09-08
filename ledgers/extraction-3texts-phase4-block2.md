# Ledger: Fase 4, Bloco 2 — `agent-cost-guard`, `intention-capture`, `api-context-spec`

## Contrato da sessão

- FASE: 4, Bloco 2
- OBJETIVO: Criar novas skills/gates `agent-cost-guard`, `intention-capture` e `api-context-spec` com base nas fontes.
- DELEGATION: disabled (usuário não autorizou subagentes)
- CHANGE_CLASS: new-skill
- LEDGER_PATH: `ledgers/extraction-3texts-phase4-block2.md` (`.devin/ledgers/*` é ignorado pelo git)

## INPUT_REGISTER

| ID | Input | Origem | Estado | Evidência |
|----|-------|--------|--------|-----------|
| I1 | Prosseguir para a Fase 4, Bloco 2 | Usuário | pendente | — |
| I2 | Tarefas 4.4-4.6 do `.devin/notes/extraction-3texts/plan.md` | Plano rastreado | pendente | — |
| I3 | Evitar regressões | Resumo da conversa | pendente | — |
| I4 | Não usar subagentes | Resumo da conversa | pendente | — |
| I5 | `agent-cost-guard`: monitorar tokens por loop, alertar token maxing, limitar subagentes | `improvements.md` | pendente | — |
| I6 | `intention-capture`: capturar e validar campo "intenção" em tickets/specs | `improvements.md` | pendente | — |
| I7 | `api-context-spec`: gerar/manter OpenAPI specs como contexto para IA | `improvements.md` | pendente | — |

## SOURCE_REGISTER

| ID | Fonte | Path/URL | Trecho/Linhas | Decisão |
|----|-------|----------|---------------|---------|
| S1 | Boas Práticas de IA | `.devin/notes/extraction-3texts/sources/good-practis.md` | L124-149, L150-165, L188-205, L206-247, L248-274, L275-288, L336-363, L364-373, L374-415 | accepted |
| S2 | O mínimo que um dev precisa saber sobre segurança | `.devin/notes/extraction-3texts/sources/sec-needs.md` | L170-188, L189-218, L220-234, L235-289, L290-315, L326-352, L354-393, L394-414, L415-450, L451-458, L459-474, L501-586 | accepted |
| S3 | Why Agentic Systems Need Ontologies | `.devin/notes/extraction-3texts/sources/ontologies-keep-honest.md` | L340-360 | accepted |

## SCOPE

Arquivos autorizados para alteração nesta fase:

- `skills/agent-cost-guard/SKILL.md` (novo)
- `skills/intention-capture/SKILL.md` (novo)
- `skills/api-context-spec/SKILL.md` (novo)
- `manifest.json` (registro das novas skills)
- `README.md` (contagem de skills)
- `docs/TOOLS-MAP.md` (contagem de skills)
- `docs/SKILL-TIERS.md` (contagem de skills)
- Este ledger

## VFS (Verification Functions)

| VF | O que deve ser verdade | Check | Expect | Evidence |
|----|------------------------|-------|--------|----------|
| VF1 | `agent-cost-guard` existe e tem frontmatter válido | `python scripts/validate-skill-format.py skills/agent-cost-guard/SKILL.md` | passa | passou |
| VF2 | `intention-capture` existe e tem frontmatter válido | `python scripts/validate-skill-format.py skills/intention-capture/SKILL.md` | passa | passou |
| VF3 | `api-context-spec` existe e tem frontmatter válido | `python scripts/validate-skill-format.py skills/api-context-spec/SKILL.md` | passa | passou |
| VF4 | `manifest.json` registra as 3 novas skills | `grep -E 'agent-cost-guard|intention-capture|api-context-spec' manifest.json` | 3 matches | passou |
| VF5 | `README.md` e docs atualizados | `grep '82 skills' README.md` | presença confirmada | passou |
| VF6 | `test_skill_format_passes.py` passa | `python -m pytest tests/validation/test_skill_format_passes.py -v` | passa | passou |
| VF7 | `test_audit_passes.py` passa | `python -m pytest tests/validation/test_audit_passes.py -v` | passa | passou |
| VF8 | Audit passa sem erros | `python audit.py` | ALL CHECKS PASSED, 0 errors, 0 warnings | ALL 32 CHECKS PASSED - NO ERRORS, NO WARNINGS |
| VF9 | Full test suite passa | `python -m pytest -q` | 264 passed | 264 passed in 33.55s |
| VF10 | Held-out tests passam | `python -m pytest tests/held-out/ -q` | 135 passed | 135 passed in 5.14s |
| VF11 | `git diff --check` e `check-ai-signature.py` passam | ambos | exit code 0 | exit code 0, nenhum output |

## Gates

- [x] G1: ledger criado e contrato registrado
- [x] G2: fontes lidas e registradas
- [x] G3: `agent-cost-guard` criado
- [x] G4: `intention-capture` criado
- [x] G5: `api-context-spec` criado
- [x] G6: `manifest.json` e docs atualizados
- [x] G7: `test_skill_format_passes.py`, `test_audit_passes.py` passam
- [x] G8: `python audit.py` passa
- [x] G9: `python -m pytest -q` passa
- [x] G10: `python -m pytest tests/held-out/ -q` passa
- [x] G11: `git diff --check` e `check-ai-signature.py` passam
- [ ] G12: commit realizado (se autorizado) e working tree limpo
