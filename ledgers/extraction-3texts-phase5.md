# Ledger: Fase 5 — `structured-knowledge-extraction`

## Contrato da sessão

- FASE: 5
- OBJETIVO: Avaliar `structured-knowledge-extraction` para adicionar camada semântica/ontológica mínima ou documentar limitação.
- DELEGATION: disabled (usuário não autorizou subagentes)
- CHANGE_CLASS: skill-only
- LEDGER_PATH: `ledgers/extraction-3texts-phase5.md` (`.devin/ledgers/*` é ignorado pelo git)

## INPUT_REGISTER

| ID | Input | Origem | Estado | Evidência |
|----|-------|--------|--------|-----------|
| I1 | Prosseguir para a Fase 5 | Usuário | pendente | — |
| I2 | Tarefa 5.1 do `.devin/notes/extraction-3texts/plan.md` | Plano rastreado | pendente | — |
| I3 | Evitar regressões | Resumo da conversa | pendente | — |
| I4 | Não usar subagentes | Resumo da conversa | pendente | — |
| I5 | Avaliar se é viável enriquecer `extract.py` para extrair conceitos | `improvements.md` | pendente | — |
| I6 | Alternativa: `ontology-validator` usa `knowledge.json` como ledger | `improvements.md` | pendente | — |
| I7 | Documentar limitação atual no `SKILL.md` | `improvements.md` | pendente | — |

## SOURCE_REGISTER

| ID | Fonte | Path/URL | Trecho/Linhas | Decisão |
|----|-------|----------|---------------|---------|
| S1 | Why Agentic Systems Need Ontologies | `.devin/notes/extraction-3texts/sources/ontologies-keep-honest.md` | L340-360 | accepted |
| S2 | `structured-knowledge-extraction` skill atual | `skills/structured-knowledge-extraction/SKILL.md` | a ser lido | accepted |
| S3 | `structured-knowledge-extraction` script atual | `skills/structured-knowledge-extraction/scripts/extract.py` | a ser lido | accepted |
| S4 | `knowledge.json` atual | `.devin/notes/structured-knowledge-extraction/knowledge.json` | lido | accepted |

## SCOPE

Arquivos autorizados para alteração nesta fase:

- `skills/structured-knowledge-extraction/SKILL.md`
- `skills/structured-knowledge-extraction/scripts/extract.py`
- Este ledger

## VFS (Verification Functions)

| VF | O que deve ser verdade | Check | Expect | Evidence |
|----|------------------------|-------|--------|----------|
| VF1 | `structured-knowledge-extraction` documenta limitação ou adiciona camada semântica | `grep 'Lexical, not semantic' skills/structured-knowledge-extraction/SKILL.md` | presença confirmada | seção Limitations adicionada |
| VF2 | `test_skill_format_passes.py` passa | `python -m pytest tests/validation/test_skill_format_passes.py -v` | passa | passou |
| VF3 | `test_audit_passes.py` passa | `python -m pytest tests/validation/test_audit_passes.py -v` | passa | passou |
| VF4 | `test_structured_knowledge_extraction.py` passa | `python -m pytest tests/validation/test_structured_knowledge_extraction.py -v` | passa | passou |
| VF5 | Audit passa sem erros | `python audit.py` | ALL CHECKS PASSED, 0 errors, 0 warnings | ALL 32 CHECKS PASSED - NO ERRORS, NO WARNINGS |
| VF6 | Full test suite passa | `python -m pytest -q` | 264 passed | 264 passed in 33.79s |
| VF7 | Held-out tests passam | `python -m pytest tests/held-out/ -q` | 135 passed | 135 passed in 5.37s |
| VF8 | `git diff --check` e `check-ai-signature.py` passam | ambos | exit code 0 | exit code 0, nenhum output |

## Gates

- [x] G1: ledger criado e contrato registrado
- [x] G2: fontes lidas e registradas
- [x] G3: `structured-knowledge-extraction` avaliado e atualizado
- [x] G4: `test_skill_format_passes.py`, `test_audit_passes.py` e `test_structured_knowledge_extraction.py` passam
- [x] G5: `python audit.py` passa
- [x] G6: `python -m pytest -q` passa
- [x] G7: `python -m pytest tests/held-out/ -q` passa
- [x] G8: `git diff --check` e `check-ai-signature.py` passam
- [ ] G9: commit realizado (se autorizado) e working tree limpo
