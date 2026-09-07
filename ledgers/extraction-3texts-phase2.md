# Ledger: Fase 2 — `leo` / fluxos principais

## Contrato da sessão

- FASE: 2
- OBJETIVO: Atualizar `skills/leo/SKILL.md` com o novo situation router e gate de validação ontológica/Pydantic, aplicando os fluxos extraídos de `sec-needs.md` e `good-practis.md`.
- DELEGATION: disabled (usuário não autorizou subagentes)
- CHANGE_CLASS: skill-only
- LEDGER_PATH: `ledgers/extraction-3texts-phase2.md` (`.devin/ledgers/*` é ignorado pelo git)

## INPUT_REGISTER

| ID | Input | Origem | Estado | Evidência |
|----|-------|--------|--------|-----------|
| I1 | Prosseguir para a Fase 2 | Usuário | pendente | — |
| I2 | Fase 2 do `.devin/notes/extraction-3texts/plan.md` | Plano rastreado | pendente | — |
| I3 | Evitar regressões | Resumo da conversa | pendente | — |
| I4 | Não usar subagentes | Resumo da conversa | pendente | — |
| I5 | `security-audit` gate obrigatório no fluxo Build/Change quando tocar API, DB, secrets, endpoints, infra | `improvements.md` | pendente | — |
| I6 | Roteamento padrão: issue/task -> `grilling` -> `planning-pipeline` -> `implement` + `tdd` -> `code-review` -> `verification-before-completion` | `improvements.md` | pendente | — |
| I7 | `grilling` capturar objetivo final, onde a feature vai e impacto no usuário | `improvements.md` | pendente | — |
| I8 | `planning-pipeline` estimar tamanho de PR e quebrar >500 linhas | `improvements.md` | pendente | — |
| I9 | `tdd` passo padrão, não opcional | `improvements.md` | pendente | — |
| I10 | `setup-pre-commit` como passo de `project-setup` e build flow | `improvements.md` | pendente | — |
| I11 | `docker`/`dev container` recomendado para tarefas destrutivas | `improvements.md` | pendente | — |
| I12 | Paralelismo limitado a 1-3 agentes; alertar se >3 | `improvements.md` | pendente | — |
| I13 | Gate ontológico/Pydantic após execução de ferramentas críticas | `improvements.md` | pendente | — |

## SOURCE_REGISTER

| ID | Fonte | Path/URL | Trecho/Linhas | Decisão |
|----|-------|----------|---------------|---------|
| S1 | O mínimo que um dev precisa saber sobre segurança | `.devin/notes/extraction-3texts/sources/sec-needs.md` | L85-111, L112-137, L220-234, L290-315, L354-393, L394-414, L451-458, L459-474 | accepted |
| S2 | Boas Práticas de IA | `.devin/notes/extraction-3texts/sources/good-practis.md` | L104-123, L124-149, L150-165, L188-205, L206-247, L248-274, L275-288, L336-363, L374-415 | accepted |
| S3 | Why Agentic Systems Need Ontologies | `.devin/notes/extraction-3texts/sources/ontologies-keep-honest.md` | a ser lido | accepted |
| S4 | Leo skill atual | `skills/leo/SKILL.md` | L1-200 | accepted |
| S5 | Teste do leo | `tests/validation/test_leo_orchestrator.py` | L1-37 | accepted |

## SCOPE

Arquivos autorizados para alteração nesta fase:

- `skills/leo/SKILL.md`
- `tests/validation/test_leo_orchestrator.py` (apenas se necessário para refletir novas strings; preferir manter compatível)
- Este ledger

## VFS (Verification Functions)

| VF | O que deve ser verdade | Check | Expect | Evidence |
|----|------------------------|-------|--------|----------|
| VF1 | `leo` router inclui `security-audit` como gate no fluxo Build/Change | `grep 'security-audit.*API, DB, secrets, endpoints, or infrastructure' skills/leo/SKILL.md` | presença confirmada | `security-audit` presente como gate no fluxo |
| VF2 | `leo` router segue fluxo: `grilling` -> `planning-pipeline` -> `implement` + `tdd` -> `code-review` -> `verification-before-completion` | `grep 'grilling.*planning-pipeline.*implement.*tdd.*code-review.*verification-before-completion' skills/leo/SKILL.md` | sequência presente | fluxo padrão registrado |
| VF3 | `leo` inclui gates de intenção, tamanho de PR, TDD, pre-commit, docker e paralelismo | `grep -E 'intent|PR.*size|tdd.*default|pre-commit|docker|parallelism' skills/leo/SKILL.md` | presença confirmada | gates adicionados na seção Build/change flow gates |
| VF4 | `leo` inclui seção de validação ontológica/Pydantic para outputs de ferramentas críticas | `grep 'Tool-output validation' skills/leo/SKILL.md` | presença confirmada | seção adicionada com type/schema, ontology/reasonableness, no side effects |
| VF5 | `test_leo_orchestrator.py` passa | `python -m pytest tests/validation/test_leo_orchestrator.py -v` | 3 passed | 3 passed in 0.06s |
| VF6 | Audit passa sem erros | `python audit.py` | ALL CHECKS PASSED, 0 errors, 0 warnings | ALL 32 CHECKS PASSED - NO ERRORS, NO WARNINGS |
| VF7 | Full test suite passa | `python -m pytest -q` | 264 passed | 264 passed in 36.53s |
| VF8 | Held-out tests passam | `python -m pytest tests/held-out/ -q` | 135 passed | 135 passed in 5.14s |
| VF9 | `git diff --check` e `check-ai-signature.py` passam | ambos | exit code 0 | exit code 0, nenhum output |

## Gates

- [x] G1: ledger criado e contrato registrado
- [x] G2: fontes lidas e registradas
- [x] G3: `skills/leo/SKILL.md` atualizado com router e gates
- [x] G4: `skills/leo/SKILL.md` inclui validação ontológica/Pydantic
- [x] G5: `python -m pytest tests/validation/test_leo_orchestrator.py -v` passa
- [x] G6: `python audit.py` passa
- [x] G7: `python -m pytest -q` passa
- [x] G8: `python -m pytest tests/held-out/ -q` passa
- [x] G9: `git diff --check` e `check-ai-signature.py` passam
- [ ] G10: commit realizado (se autorizado) e working tree limpo
