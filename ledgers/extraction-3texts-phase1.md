# Ledger: Fase 1 — Regras e setup de projeto

## Contrato da sessão

- FASE: 1
- OBJETIVO: Atualizar `AGENTS.md` / `global_rules.md` e criar template de `agents.md` de projeto, aplicando pontos extraídos de `sec-needs.md` e `good-practis.md`.
- DELEGATION: disabled (usuário não autorizou subagentes)
- CHANGE_CLASS: doc-only (regras, templates) + script-behavior (se testes de regra forem adicionados/alterados)
- LEDGER_PATH: `ledgers/extraction-3texts-phase1.md` (`.devin/ledgers/*` é ignorado pelo git)

## INPUT_REGISTER

| ID | Input | Origem | Estado | Evidência |
|----|-------|--------|--------|-----------|
| I1 | Prosseguir para a próxima fase do plano | Usuário | pendente | — |
| I2 | Phase 1 do `.devin/notes/extraction-3texts/plan.md` | Plano rastreado | pendente | — |
| I3 | Evitar regressões | Resumo da conversa | pendente | — |
| I4 | Não usar subagentes | Resumo da conversa | pendente | — |
| I5 | Regras: menor código, sanitizar inputs, não logar/outputar secrets, não comitar secrets, não deletar testes sem aprovação, ações destrutivas precisam confirmação, endpoints/S3 públicos precisam justificativa, declarar intenção e impacto antes de codar | `improvements.md` | pendente | — |

## SOURCE_REGISTER

| ID | Fonte | Path/URL | Trecho/Linhas | Decisão |
|----|-------|----------|---------------|---------|
| S1 | O mínimo que um dev precisa saber sobre segurança | `.devin/notes/extraction-3texts/sources/sec-needs.md` | L08-28, L72-84, L85-111, L112-137, L138-169, L220-234, L290-315, L326-352, L354-393, L394-414, L415-450, L451-458, L459-474, L501-586 | accepted |
| S2 | Boas Práticas de IA | `.devin/notes/extraction-3texts/sources/good-practis.md` | L104-123, L124-149, L150-165, L166-187, L188-205, L206-247, L248-274, L275-288, L289-324, L325-331, L336-363, L364-373, L374-415 | accepted |
| S3 | AGENTS.md atual | `AGENTS.md` | L1-220 | accepted |
| S4 | global_rules.md atual | `.devin/global_rules.md` | L1-27 | accepted |
| S5 | project-setup skill | `skills/project-setup/SKILL.md` | L1-217 | accepted |
| S6 | writing-for-agents skill | `skills/writing-for-agents/SKILL.md` | L1-85 | accepted |

## SCOPE

Arquivos autorizados para alteração nesta fase:

- `AGENTS.md`
- `.devin/global_rules.md`
- `audit.py`
- `manifest.json`
- `README.md`
- `skills/project-setup/SKILL.md`
- `skills/writing-for-agents/SKILL.md` (se necessário para template)
- Novo template: `skills/project-setup/templates/agents.md` (se aprovado)
- Testes de regra: `tests/held-out/...` (não editar; apenas executar)
- `tests/validation/` (apenas adicionar testes de contrato se necessário e autorizado)
- Este ledger

## VFS (Verification Functions)

| VF | O que deve ser verdade | Check | Expect | Evidence |
|----|------------------------|-------|--------|----------|
| VF1 | `AGENTS.md` contém as novas regras de segurança e boas práticas | `grep '^\d+\. \*\*' AGENTS.md` | regras 22-27 presentes | Rules found: [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27] |
| VF2 | `global_rules.md` reflete verificação e escopo de projeto | `read .devin/global_rules.md` | seção `Security and project hygiene` adicionada | 9 bullets de segurança/higiene inseridos |
| VF3 | Template de `agents.md` de projeto existe e é gerado pelo `project-setup` | `ls skills/project-setup/templates/agents.md` + `read skills/project-setup/SKILL.md` | template presente e referenciado no passo 2.5 | arquivo criado; skill aponta para `.devin/rules/agents.md` |
| VF4 | Audit passa sem erros | `python audit.py` | ALL CHECKS PASSED, 0 errors, 0 warnings | ALL 32 CHECKS PASSED - NO ERRORS, NO WARNINGS |
| VF5 | Full test suite passa | `python -m pytest -q` | 264 passed | 264 passed in 29.04s |
| VF6 | Held-out tests relevantes passam | `python -m pytest tests/held-out/ -q` | 135 passed | 135 passed in 4.95s |
| VF7 | Nenhuma assinatura de IA no diff | `python scripts/check-ai-signature.py` | nenhuma assinatura detectada | exit code 0, nenhum output |
| VF8 | Diff limpo e sem conflitos | `git diff --check` | vazio / sem erros | exit code 0 |

## Gates

- [x] G1: ledger criado e contrato registrado
- [x] G2: fontes lidas e registradas
- [x] G3: `AGENTS.md` atualizado
- [x] G4: `global_rules.md` atualizado
- [x] G5: template `agents.md` de projeto criado/integrado em `project-setup`
- [x] G6: `python audit.py` passa
- [x] G7: `python -m pytest -q` passa
- [x] G8: `python -m pytest tests/held-out/ -q` passa
- [x] G9: `git diff --check` e `check-ai-signature.py` passam
- [ ] G10: commit realizado (se autorizado) e working tree limpo
