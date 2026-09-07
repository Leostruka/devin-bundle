# Ledger: Fase 3, Bloco 1 — `security-audit`, `tdd`/`setup-pre-commit`, `planning-pipeline`, `api-design`

## Contrato da sessão

- FASE: 3, Bloco 1
- OBJETIVO: Fortalecer `security-audit`, `tdd`/`setup-pre-commit`, `planning-pipeline` e `api-design` com os pontos de `sec-needs.md` e `good-practis.md`.
- DELEGATION: disabled (usuário não autorizou subagentes)
- CHANGE_CLASS: skill-only
- LEDGER_PATH: `ledgers/extraction-3texts-phase3-block1.md` (`.devin/ledgers/*` é ignorado pelo git)

## INPUT_REGISTER

| ID | Input | Origem | Estado | Evidência |
|----|-------|--------|--------|-----------|
| I1 | Prosseguir para a Fase 3 por blocos | Usuário | pendente | — |
| I2 | Tarefas 3.1-3.4 do `.devin/notes/extraction-3texts/plan.md` | Plano rastreado | pendente | — |
| I3 | Evitar regressões | Resumo da conversa | pendente | — |
| I4 | Não usar subagentes | Resumo da conversa | pendente | — |
| I5 | `security-audit`: checklist dos 5 princípios de `sec-needs.md` | `improvements.md` | pendente | — |
| I6 | `tdd`: handler/script de teste, testes antes de commit, regra de não deletar testes | `improvements.md` | pendente | — |
| I7 | `setup-pre-commit`: configurar Husky + lint-staged + testes | `improvements.md` | pendente | — |
| I8 | `planning-pipeline`: intenção, tamanho estimado (linhas), input/output (boundaries), PRD como gate | `improvements.md` | pendente | — |
| I9 | `api-design`: especificação de input/output/comportamento; gerar/consumir OpenAPI | `improvements.md` | pendente | — |

## SOURCE_REGISTER

| ID | Fonte | Path/URL | Trecho/Linhas | Decisão |
|----|-------|----------|---------------|---------|
| S1 | O mínimo que um dev precisa saber sobre segurança | `.devin/notes/extraction-3texts/sources/sec-needs.md` | L72-84, L85-111, L112-137, L138-169, L220-234, L235-289, L290-315, L326-352, L354-393, L394-414, L415-450, L451-458, L459-474, L501-586 | accepted |
| S2 | Boas Práticas de IA | `.devin/notes/extraction-3texts/sources/good-practis.md` | L188-205, L206-247, L248-274, L275-288, L336-363, L364-373, L374-415 | accepted |
| S3 | security-audit skill atual | `skills/security-audit/SKILL.md` | a ser lido | accepted |
| S4 | tdd skill atual | `skills/tdd/SKILL.md` | a ser lido | accepted |
| S5 | setup-pre-commit skill atual | `skills/setup-pre-commit/SKILL.md` | a ser lido | accepted |
| S6 | planning-pipeline skill atual | `skills/planning-pipeline/SKILL.md` | a ser lido | accepted |
| S7 | api-design skill atual | `skills/api-design/SKILL.md` | a ser lido | accepted |

## SCOPE

Arquivos autorizados para alteração nesta fase:

- `skills/security-audit/SKILL.md`
- `skills/tdd/SKILL.md`
- `skills/setup-pre-commit/SKILL.md`
- `skills/planning-pipeline/SKILL.md`
- `skills/api-design/SKILL.md`
- `skills/leo/SKILL.md` (integração do `setup-pre-commit`/`tdd` no build flow, se necessário)
- Este ledger

## VFS (Verification Functions)

| VF | O que deve ser verdade | Check | Expect | Evidence |
|----|------------------------|-------|--------|----------|
| VF1 | `security-audit` inclui os 5 princípios de `sec-needs.md` | `grep 'Checklist.*5 security principles' skills/security-audit/SKILL.md` | presença confirmada | checklist adicionada |
| VF2 | `tdd` inclui exigência de testes antes de commit e regra de não deletar testes | `grep 'Tests are permanent artifacts' skills/tdd/SKILL.md` | presença confirmada | seção adicionada |
| VF3 | `setup-pre-commit` inclui Husky + lint-staged + testes | `grep 'required step' skills/setup-pre-commit/SKILL.md` | presença confirmada | nota de obrigatoriedade adicionada |
| VF4 | `planning-pipeline` inclui campos de intenção, tamanho estimado e input/output | `grep -E 'Intent|Estimated size|Input / Output' skills/planning-pipeline/SKILL.md` | presença confirmada | campos adicionados ao spec e ticket templates |
| VF5 | `api-design` exige input/output/comportamento e OpenAPI | `grep 'Specify input/output/behavior' skills/api-design/SKILL.md` | presença confirmada | passo adicionado |
| VF6 | `test_skill_format_passes.py` passa | `python -m pytest tests/validation/test_skill_format_passes.py -v` | passa | passou (após install sync) |
| VF7 | `test_audit_passes.py` passa | `python -m pytest tests/validation/test_audit_passes.py -v` | passa | passou (após install sync) |
| VF8 | Audit passa sem erros | `python audit.py` | ALL CHECKS PASSED, 0 errors, 0 warnings | ALL 32 CHECKS PASSED - NO ERRORS, NO WARNINGS |
| VF9 | Full test suite passa | `python -m pytest -q` | 264 passed | 264 passed in 30.37s |
| VF10 | Held-out tests passam | `python -m pytest tests/held-out/ -q` | 135 passed | 135 passed in 5.08s |
| VF11 | `git diff --check` e `check-ai-signature.py` passam | ambos | exit code 0 | exit code 0, nenhum output |

## Gates

- [x] G1: ledger criado e contrato registrado
- [x] G2: fontes lidas e registradas
- [x] G3: `security-audit` atualizado
- [x] G4: `tdd` e `setup-pre-commit` atualizados
- [x] G5: `planning-pipeline` atualizado
- [x] G6: `api-design` atualizado
- [x] G7: `test_skill_format_passes.py` e `test_audit_passes.py` passam
- [x] G8: `python audit.py` passa
- [x] G9: `python -m pytest -q` passa
- [x] G10: `python -m pytest tests/held-out/ -q` passa
- [x] G11: `git diff --check` e `check-ai-signature.py` passam
- [ ] G12: commit realizado (se autorizado) e working tree limpo
