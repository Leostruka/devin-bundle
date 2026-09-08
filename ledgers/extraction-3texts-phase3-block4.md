# Ledger: Fase 3, Bloco 4 — `grilling`, `code-review`, `project-memory`, `effort-calibration`/`model-interface-preflight`

## Contrato da sessão

- FASE: 3, Bloco 4
- OBJETIVO: Fortalecer `grilling`, `code-review`, `project-memory` e `effort-calibration`/`model-interface-preflight` com os pontos de `good-practis.md` e `ontologies-keep-honest.md`.
- DELEGATION: disabled (usuário não autorizou subagentes)
- CHANGE_CLASS: skill-only
- LEDGER_PATH: `ledgers/extraction-3texts-phase3-block4.md` (`.devin/ledgers/*` é ignorado pelo git)

## INPUT_REGISTER

| ID | Input | Origem | Estado | Evidência |
|----|-------|--------|--------|-----------|
| I1 | Prosseguir para o Bloco 4 da Fase 3 | Usuário | pendente | — |
| I2 | Tarefas 3.10-3.12 do `.devin/notes/extraction-3texts/plan.md` | Plano rastreado | pendente | — |
| I3 | Evitar regressões | Resumo da conversa | pendente | — |
| I4 | Não usar subagentes | Resumo da conversa | pendente | — |
| I5 | `grilling`: capturar intenção (objetivo, onde a feature vai, impacto no usuário); transformar em PRD | `improvements.md` | pendente | — |
| I6 | `code-review`: integrar Code Rabbit (config `.coderabbit.yaml`) para automação de revisão | `improvements.md` | pendente | — |
| I7 | `project-memory`: capturar intenção/estado após implementação e antes de `clear`/`compact` | `improvements.md` | pendente | — |
| I8 | `effort-calibration`/`model-interface-preflight`: paralelismo 1-3, limite de tamanho (300 linhas/PR, 500 split), custo | `improvements.md` | pendente | — |

## SOURCE_REGISTER

| ID | Fonte | Path/URL | Trecho/Linhas | Decisão |
|----|-------|----------|---------------|---------|
| S1 | Boas Práticas de IA | `.devin/notes/extraction-3texts/sources/good-practis.md` | L124-149, L150-165, L188-205, L206-247, L248-274, L275-288, L336-363, L364-373, L374-415 | accepted |
| S2 | Why Agentic Systems Need Ontologies | `.devin/notes/extraction-3texts/sources/ontologies-keep-honest.md` | L340-360 | accepted |
| S3 | grilling skill atual | `skills/grilling/SKILL.md` | a ser lido | accepted |
| S4 | code-review skill atual | `skills/code-review/SKILL.md` | a ser lido | accepted |
| S5 | project-memory skill atual | `skills/project-memory/SKILL.md` | a ser lido | accepted |
| S6 | effort-calibration skill atual | `skills/effort-calibration/SKILL.md` | a ser lido | accepted |
| S7 | model-interface-preflight skill atual | `skills/model-interface-preflight/SKILL.md` | a ser lido | accepted |

## SCOPE

Arquivos autorizados para alteração nesta fase:

- `skills/grilling/SKILL.md`
- `skills/code-review/SKILL.md`
- `skills/project-memory/SKILL.md`
- `skills/effort-calibration/SKILL.md`
- `skills/model-interface-preflight/SKILL.md`
- Este ledger

## VFS (Verification Functions)

| VF | O que deve ser verdade | Check | Expect | Evidence |
|----|------------------------|-------|--------|----------|
| VF1 | `grilling` inclui captura de intenção e transformação em PRD | `grep 'Intent capture' skills/grilling/SKILL.md` | presença confirmada | seção adicionada |
| VF2 | `code-review` inclui integração Code Rabbit | `grep 'Code Rabbit' skills/code-review/SKILL.md` | presença confirmada | seção adicionada |
| VF3 | `project-memory` inclui captura de intenção/estado após implementação e antes de clear/compact | `grep 'Post-implementation capture' skills/project-memory/SKILL.md` | presença confirmada | seção adicionada |
| VF4 | `effort-calibration` inclui paralelismo e tamanho | `grep 'Parallelism and size guards' skills/effort-calibration/SKILL.md` | presença confirmada | seção adicionada |
| VF5 | `validate-tool-args.py` inclui limite de paralelismo | `grep 'max_parallel' scripts/validate-tool-args.py` | presença confirmada | check adicionado |
| VF6 | `test_skill_format_passes.py` passa | `python -m pytest tests/validation/test_skill_format_passes.py -v` | passa | passou |
| VF7 | `test_audit_passes.py` passa | `python -m pytest tests/validation/test_audit_passes.py -v` | passa | passou |
| VF8 | `test_model_interface_preflight.py` passa | `python -m pytest tests/validation/test_model_interface_preflight.py -v` | passa | passou |
| VF9 | Audit passa sem erros | `python audit.py` | ALL CHECKS PASSED, 0 errors, 0 warnings | ALL 32 CHECKS PASSED - NO ERRORS, NO WARNINGS |
| VF10 | Full test suite passa | `python -m pytest -q` | 264 passed | 264 passed in 33.70s |
| VF11 | Held-out tests passam | `python -m pytest tests/held-out/ -q` | 135 passed | 135 passed in 5.01s |
| VF12 | `git diff --check` e `check-ai-signature.py` passam | ambos | exit code 0 | exit code 0, nenhum output |

## Gates

- [x] G1: ledger criado e contrato registrado
- [x] G2: fontes lidas e registradas
- [x] G3: `grilling` atualizado
- [x] G4: `code-review` atualizado
- [x] G5: `project-memory` atualizado
- [x] G6: `effort-calibration`/`validate-tool-args.py` atualizados
- [x] G7: `test_skill_format_passes.py`, `test_audit_passes.py` e `test_model_interface_preflight.py` passam
- [x] G8: `python audit.py` passa
- [x] G9: `python -m pytest -q` passa
- [x] G10: `python -m pytest tests/held-out/ -q` passa
- [x] G11: `git diff --check` e `check-ai-signature.py` passam
- [x] G12: commit realizado (se autorizado) e working tree limpo

## Resultado

- Commit: `aabfc57 feat: add intent capture, code-rabbit integration, post-impl memory, and parallelism guards`
- Working tree: limpa
- Audit: 32/32 checks, 0 erros, 0 warnings
- Tests: 264 passed (full), 135 passed (held-out)
- Diff check: limpo
- AI signature: nenhuma detectada
- Install sync: `code-review`, `effort-calibration`, `grilling`, `project-memory`, `scripts/validate-tool-args.py` atualizados
