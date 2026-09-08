# Ledger: Fase 3, Bloco 3 — `verification-before-completion`, `using-skills`, `implement`

## Contrato da sessão

- FASE: 3, Bloco 3
- OBJETIVO: Atualizar `verification-before-completion`, `using-skills` e `implement` com os pontos de `sec-needs.md` e `good-practis.md`.
- DELEGATION: disabled (usuário não autorizou subagentes)
- CHANGE_CLASS: skill-only
- LEDGER_PATH: `ledgers/extraction-3texts-phase3-block3.md` (`.devin/ledgers/*` é ignorado pelo git)

## INPUT_REGISTER

| ID | Input | Origem | Estado | Evidência |
|----|-------|--------|--------|-----------|
| I1 | Prosseguir para o Bloco 3 da Fase 3 | Usuário | pendente | — |
| I2 | Tarefas 3.8-3.10 do `.devin/notes/extraction-3texts/plan.md` | Plano rastreado | pendente | — |
| I3 | Evitar regressões | Resumo da conversa | pendente | — |
| I4 | Não usar subagentes | Resumo da conversa | pendente | — |
| I5 | `verification-before-completion`: incluir verificações de segurança | `improvements.md` | pendente | — |
| I6 | `using-skills`: instruir a invocar `security-audit`, `tdd`, `setup-pre-commit`, `cost-optimization`/`context-window-hygiene`, `docker`, `mcp-context-audit`/`mcp-lazy-enablement` | `improvements.md` | pendente | — |
| I7 | `implement`: exigir mudanças cirúrgicas, input/output/Boundaries, manter PR ~300 linhas, quebrar >500, não deletar testes, `verification-before-completion` antes de finalizar | `improvements.md` | pendente | — |

## SOURCE_REGISTER

| ID | Fonte | Path/URL | Trecho/Linhas | Decisão |
|----|-------|----------|---------------|---------|
| S1 | O mínimo que um dev precisa saber sobre segurança | `.devin/notes/extraction-3texts/sources/sec-needs.md` | L72-84, L85-111, L112-137, L138-169, L170-188, L189-218, L220-234, L235-289, L290-315, L326-352, L354-393, L394-414, L415-450, L451-458, L459-474, L501-586 | accepted |
| S2 | Boas Práticas de IA | `.devin/notes/extraction-3texts/sources/good-practis.md` | L104-123, L124-149, L150-165, L188-205, L206-247, L248-274, L275-288, L336-363, L364-373, L374-415 | accepted |
| S3 | verification-before-completion skill atual | `skills/verification-before-completion/SKILL.md` | a ser lido | accepted |
| S4 | using-skills skill atual | `skills/using-skills/SKILL.md` | a ser lido | accepted |
| S5 | implement skill atual | `skills/implement/SKILL.md` | a ser lido | accepted |

## SCOPE

Arquivos autorizados para alteração nesta fase:

- `skills/verification-before-completion/SKILL.md`
- `skills/using-skills/SKILL.md`
- `skills/implement/SKILL.md`
- Este ledger

## VFS (Verification Functions)

| VF | O que deve ser verdade | Check | Expect | Evidence |
|----|------------------------|-------|--------|----------|
| VF1 | `verification-before-completion` inclui verificações de segurança | `grep 'Security checks' skills/verification-before-completion/SKILL.md` | presença confirmada | seção adicionada |
| VF2 | `using-skills` inclui invocação de `security-audit`, `tdd`, `setup-pre-commit`, `cost-optimization`, `context-window-hygiene`, `docker`, `mcp-context-audit`, `mcp-lazy-enablement` | `grep -E 'security-audit|tdd|setup-pre-commit|cost-optimization|context-window-hygiene|docker|mcp-context-audit|mcp-lazy-enablement' skills/using-skills/SKILL.md` | presença confirmada | cross-skills adicionados |
| VF3 | `implement` inclui mudanças cirúrgicas, input/output, limite de PR, não deletar testes, `verification-before-completion` | `grep -E 'surgical|input and output|~300|~500|Do not delete|verification-before-completion' skills/implement/SKILL.md` | presença confirmada | seção Scope and size adicionada |
| VF4 | `test_skill_format_passes.py` passa | `python -m pytest tests/validation/test_skill_format_passes.py -v` | passa | passou |
| VF5 | `test_audit_passes.py` passa | `python -m pytest tests/validation/test_audit_passes.py -v` | passa | passou |
| VF6 | `test_leo_orchestrator.py` passa | `python -m pytest tests/validation/test_leo_orchestrator.py -v` | passa | passou |
| VF7 | Audit passa sem erros | `python audit.py` | ALL CHECKS PASSED, 0 errors, 0 warnings | ALL 32 CHECKS PASSED - NO ERRORS, NO WARNINGS |
| VF8 | Full test suite passa | `python -m pytest -q` | 264 passed | 264 passed in 30.24s |
| VF9 | Held-out tests passam | `python -m pytest tests/held-out/ -q` | 135 passed | 135 passed in 5.03s |
| VF10 | `git diff --check` e `check-ai-signature.py` passam | ambos | exit code 0 | exit code 0, nenhum output |

## Gates

- [x] G1: ledger criado e contrato registrado
- [x] G2: fontes lidas e registradas
- [x] G3: `verification-before-completion` atualizado
- [x] G4: `using-skills` atualizado
- [x] G5: `implement` atualizado
- [x] G6: `test_skill_format_passes.py`, `test_audit_passes.py` e `test_leo_orchestrator.py` passam
- [x] G7: `python audit.py` passa
- [x] G8: `python -m pytest -q` passa
- [x] G9: `python -m pytest tests/held-out/ -q` passa
- [x] G10: `git diff --check` e `check-ai-signature.py` passam
- [x] G11: commit realizado (se autorizado) e working tree limpo

## Resultado

- Commit: `df95639 feat: add security checks and surgical-change limits to verification, using-skills, implement`
- Working tree: limpa
- Audit: 32/32 checks, 0 erros, 0 warnings
- Tests: 264 passed (full), 135 passed (held-out)
- Diff check: limpo
- AI signature: nenhuma detectada
- Install sync: `implement`, `using-skills`, `verification-before-completion` atualizados
