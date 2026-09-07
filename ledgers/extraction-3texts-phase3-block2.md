# Ledger: Fase 3, Bloco 2 — `cost-optimization`, `context-window-hygiene`, `docker`, `mcp-context-audit`/`mcp-lazy-enablement`

## Contrato da sessão

- FASE: 3, Bloco 2
- OBJETIVO: Atualizar `cost-optimization`, `context-window-hygiene`, `docker`, `mcp-context-audit`/`mcp-lazy-enablement` com os pontos de `good-practis.md` e `ontologies-keep-honest.md`.
- DELEGATION: disabled (usuário não autorizou subagentes)
- CHANGE_CLASS: skill-only
- LEDGER_PATH: `ledgers/extraction-3texts-phase3-block2.md` (`.devin/ledgers/*` é ignorado pelo git)

## INPUT_REGISTER

| ID | Input | Origem | Estado | Evidência |
|----|-------|--------|--------|-----------|
| I1 | Prosseguir para o Bloco 2 da Fase 3 | Usuário | pendente | — |
| I2 | Tarefas 3.5-3.7 do `.devin/notes/extraction-3texts/plan.md` | Plano rastreado | pendente | — |
| I3 | Evitar regressões | Resumo da conversa | pendente | — |
| I4 | Não usar subagentes | Resumo da conversa | pendente | — |
| I5 | `cost-optimization`/`context-window-hygiene`: decisões de contexto (subagentes, token-limit, compact, clear), paralelismo 1-3, custo | `improvements.md` | pendente | — |
| I6 | `docker`: dev container como ambiente padrão recomendado para tarefas destrutivas | `improvements.md` | pendente | — |
| I7 | `mcp-context-audit`/`mcp-lazy-enablement`: medir custo de contexto por ferramenta MCP, desligar tools irrelevantes | `improvements.md` | pendente | — |
| I8 | Loops custam dinheiro (aumento de tokens) | `ontologies-keep-honest.md` | pendente | — |

## SOURCE_REGISTER

| ID | Fonte | Path/URL | Trecho/Linhas | Decisão |
|----|-------|----------|---------------|---------|
| S1 | Boas Práticas de IA | `.devin/notes/extraction-3texts/sources/good-practis.md` | L336-363, L364-373, L374-415 | accepted |
| S2 | Why Agentic Systems Need Ontologies | `.devin/notes/extraction-3texts/sources/ontologies-keep-honest.md` | L340-360 | accepted |
| S3 | cost-optimization skill atual | `skills/cost-optimization/SKILL.md` | a ser lido | accepted |
| S4 | context-window-hygiene skill atual | `skills/context-window-hygiene/SKILL.md` | a ser lido | accepted |
| S5 | docker skill atual | `skills/docker/SKILL.md` | a ser lido | accepted |
| S6 | mcp-context-audit skill atual | `skills/mcp-context-audit/SKILL.md` | a ser lido | accepted |
| S7 | mcp-lazy-enablement skill atual | `skills/mcp-lazy-enablement/SKILL.md` | a ser lido | accepted |

## SCOPE

Arquivos autorizados para alteração nesta fase:

- `skills/cost-optimization/SKILL.md`
- `skills/context-window-hygiene/SKILL.md`
- `skills/docker/SKILL.md`
- `skills/mcp-context-audit/SKILL.md`
- `skills/mcp-lazy-enablement/SKILL.md`
- Este ledger

## VFS (Verification Functions)

| VF | O que deve ser verdade | Check | Expect | Evidence |
|----|------------------------|-------|--------|----------|
| VF1 | `cost-optimization`/`context-window-hygiene` inclui decisões de contexto e limite de paralelismo | `grep -E 'Subagents first|Token limit|Clear vs compact|Parallelism|Loops cost money|Guard against context overflow' skills/cost-optimization/SKILL.md skills/context-window-hygiene/SKILL.md` | presença confirmada | seções adicionadas |
| VF2 | `docker` inclui dev container como recomendação para tarefas destrutivas | `grep 'Dev container for destructive work' skills/docker/SKILL.md` | presença confirmada | seção adicionada |
| VF3 | `mcp-context-audit`/`mcp-lazy-enablement` inclui auditoria de custo de contexto e desligamento de tools | `grep -E 'Audit by tool|Disable tools, not just servers' skills/mcp-context-audit/SKILL.md skills/mcp-lazy-enablement/SKILL.md` | presença confirmada | seções adicionadas |
| VF4 | `test_skill_format_passes.py` passa | `python -m pytest tests/validation/test_skill_format_passes.py -v` | passa | passou (após install sync) |
| VF5 | `test_audit_passes.py` passa | `python -m pytest tests/validation/test_audit_passes.py -v` | passa | passou (após install sync) |
| VF6 | `test_mcp_code_mode.py` passa | `python -m pytest tests/validation/test_mcp_code_mode.py -v` | passa | passou (após install sync) |
| VF7 | Audit passa sem erros | `python audit.py` | ALL CHECKS PASSED, 0 errors, 0 warnings | ALL 32 CHECKS PASSED - NO ERRORS, NO WARNINGS |
| VF8 | Full test suite passa | `python -m pytest -q` | 264 passed | 264 passed in 29.89s |
| VF9 | Held-out tests passam | `python -m pytest tests/held-out/ -q` | 135 passed | 135 passed in 5.14s |
| VF10 | `git diff --check` e `check-ai-signature.py` passam | ambos | exit code 0 | exit code 0, nenhum output |

## Gates

- [x] G1: ledger criado e contrato registrado
- [x] G2: fontes lidas e registradas
- [x] G3: `cost-optimization` e `context-window-hygiene` atualizados
- [x] G4: `docker` atualizado
- [x] G5: `mcp-context-audit`/`mcp-lazy-enablement` atualizados
- [x] G6: `test_skill_format_passes.py`, `test_audit_passes.py` e `test_mcp_code_mode.py` passam
- [x] G7: `python audit.py` passa
- [x] G8: `python -m pytest -q` passa
- [x] G9: `python -m pytest tests/held-out/ -q` passa
- [x] G10: `git diff --check` e `check-ai-signature.py` passam
- [ ] G11: commit realizado (se autorizado) e working tree limpo
