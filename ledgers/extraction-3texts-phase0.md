# GATES: extraction-3texts Phase 0 — continuous-improvement

Objetivo: corrigir o workflow de melhoria contínua antes de aplicar as demais propostas de `improvements.md`, sem usar subagentes e sem regressões.

Nota de localização: a skill documenta `.devin/ledgers/`, mas este bundle mantém os ledgers rastreados em `ledgers/`; o `.gitignore` exclui novos arquivos em `.devin/ledgers/`. Este ledger usa o diretório rastreado do projeto para preservar evidência.

## INPUT_REGISTER

| ID | Origem | Requisito | Estado |
|---|---|---|---|
| IN-01 | Pedido atual | Começar a implementação e evitar regressões | applied |
| IN-02 | `.devin/notes/extraction-3texts/improvements.md` | Preservar o mapeamento completo das melhorias | applied as Phase 0 input |
| IN-03 | `.devin/notes/extraction-3texts/plan.md` | Executar Fase 0 antes das demais fases | applied |
| IN-04 | Pinned constraints + `AGENTS.md` | Sem assinaturas, sem push sem verde, verificar com ferramentas, sem secrets | applied |
| IN-05 | Restrição explícita desta execução | `DELEGATION=disabled`; não usar subagentes | applied |

## SOURCE_REGISTER

| ID | Fonte | Prova lida | Estado |
|---|---|---|---|
| SRC-01 | `skills/continuous-improvement/SKILL.md` | L01-384, antes da edição e diff verificado | applied |
| SRC-02 | `skills/unlazy/SKILL.md` | L01-115 | applied |
| SRC-03 | `skills/verification-before-completion/SKILL.md` | L01-161 | applied |
| SRC-04 | `skills/leo/SKILL.md` | L01-200 | applied |
| SRC-05 | `AGENTS.md`, `.devin/global_rules.md` | regras e gates lidos diretamente | applied |
| SRC-06 | Devin CLI docs | URLs e seções registradas no review L18-22 | applied |

## SCOPE

Arquivos desta Fase 0: `skills/continuous-improvement/SKILL.md`, `skills/unlazy/SKILL.md`, `skills/verification-before-completion/SKILL.md`, `tests/validation/test_continuous_improvement_contract.py`, `.devin/notes/extraction-3texts/continuous-improvement-review.md` e este ledger.

As alterações já presentes em `scripts/context-pressure.py`, `tests/validation/test_task_adaptive_harness.py` e `ledgers/melhoria-continua-glm5-swe17-ciclo2.md` foram encontradas no estado de trabalho após uma invocação automática anterior. Por autorização explícita do usuário, os dois arquivos rastreados foram restaurados ao HEAD e o ledger não rastreado foi removido; nenhum deles pertence ao commit desta Fase 0.

- [x] G1: estado inicial reproduzido
  CHECK: `python audit.py`; `python -m pytest -q`
  EXPECT: `Errors:   0`; `Warnings: 0`; `260 passed`
  EVIDENCE: `audit.py` → `ALL 32 CHECKS PASSED - NO ERRORS, NO WARNINGS`; `pytest` → `260 passed in 33.03s`

- [x] G2: lacunas da skill confirmadas contra fontes primárias locais
  CHECK: leitura de `skills/continuous-improvement/SKILL.md`, `skills/unlazy/SKILL.md`, `skills/verification-before-completion/SKILL.md`, `skills/leo/SKILL.md`, `AGENTS.md` e `.devin/global_rules.md`; registrar cada lacuna com linha e arquivo
  EXPECT: tabela de lacunas com evidência de arquivo/linha e nenhuma afirmação baseada apenas em resumo
  EVIDENCE: leitura direta registrada em `continuous-improvement-review.md` L05-23; matriz CI-01–CI-17 em L24-44; fontes Devin CLI lidas em URLs L20-22.

- [x] G3: review da continuous-improvement documentado
  CHECK: arquivo `.devin/notes/extraction-3texts/continuous-improvement-review.md` existe e contém matriz requisito → comportamento atual → lacuna → correção → gate
  EXPECT: todos os requisitos do plano Fase 0.1 cobertos
  EVIDENCE: arquivo presente; matriz CI-01–CI-17 cobre frontmatter, inputs, fontes, gates, held-out, instalação, métricas, impacto, deliverables, delegação e rastreabilidade.

- [x] G4: workflow corrigido
  CHECK: leitura do diff de `skills/continuous-improvement/SKILL.md` e validação estrutural com `python audit.py`
  EXPECT: gates explícitos por subpasso, fontes verificáveis, modo sem subagente respeitado e completion gate referenciado
  EVIDENCE: `continuous-improvement` frontmatter agora é inline (sem `subagent`/`agent`); contrato contém `INPUT_REGISTER`, `SOURCE_REGISTER`, `VFS`, `SCOPE`, gates `OUTCOME/CHECK/EXPECT/EVIDENCE`, dry-run, estados e cobertura; `audit.py` → `ALL 32 CHECKS PASSED - NO ERRORS, NO WARNINGS`.

- [x] G5: testes da mudança passam
  CHECK: `python -m pytest tests/validation/test_skill_format_passes.py tests/validation/test_audit_passes.py tests/validation/test_continuous_improvement_contract.py -q`
  EXPECT: todos os testes selecionados passam
  EVIDENCE: `8 passed in 1.96s`.

- [x] G6: held-out e suite completa sem regressão
  CHECK: `python -m pytest tests/held-out/ -q`; `python -m pytest -q`
  EXPECT: held-out passa; suite completa passa com 264 testes
  EVIDENCE: held-out → `135 passed in 5.29s`; suite completa → `264 passed in 32.88s`.

- [x] G7a: instalação dry-run revisada
  CHECK: `./install.ps1 -DryRun`
  EXPECT: exit 0; somente os três skills alterados aparecem como diferentes
  EVIDENCE: dry-run exit 0; `continuous-improvement`, `unlazy` e `verification-before-completion` aparecem como `differs`; nenhum arquivo foi escrito.

- [x] G7b: instalação live autorizada e sincronização verificadas
  CHECK: `./install.ps1 -Force -Backup`; `python audit.py`
  EXPECT: instalação termina com exit 0; audit sem erros e warnings
  EVIDENCE: instalação exit 0; 3 skills atualizadas; backup criado em `C:\Users\leand\.devin-import-backup-20260907-162638`; audit → `ALL 32 CHECKS PASSED - NO ERRORS, NO WARNINGS`.

- [x] G8a: higiene do diff e deliverables verificada
  CHECK: `git diff --check`; `git diff --stat`; `python scripts/check-ai-signature.py`
  EXPECT: nenhum erro de whitespace e nenhuma assinatura AI
  EVIDENCE: `git diff --check` exit 0; `check-ai-signature.py` exit 0; tracked diff = `4 files changed, 244 insertions(+), 107 deletions(-)`; no AI signature output.

- [x] G8b: escopo do working tree resolvido
  CHECK: `git status --short`
  EXPECT: somente arquivos intencionais desta Fase 0 permanecem antes de commit
  EVIDENCE: status contém somente `plan.md`, as três skills atualizadas, o review, este ledger e o teste de contrato; os três itens autorizados foram removidos.

ABANDON: nenhum
