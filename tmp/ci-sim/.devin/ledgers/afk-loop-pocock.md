# Ledger: afk-loop (Ralph / issues locais + TDD)

## Gates FASE 0

- [x] 0.1 Ler executing-plans e dispatching-parallel-agents
  OUTCOME: Entender skills existentes.
  CHECK: read skills/executing-plans/SKILL.md e skills/dispatching-parallel-agents/SKILL.md
  EXPECT: Resumo.
  EVIDENCE: Lidos `skills/executing-plans/SKILL.md` e `skills/dispatching-parallel-agents/SKILL.md`. Resumo: `executing-plans` executa planos com checkpoints, nao loop autonomo; `dispatching-parallel-agents` lanca subagentes por tarefa independente, nao itera sobre issues locais.

- [x] 0.2 Verificar using-git-worktrees
  OUTCOME: Saber como isolar loop.
  CHECK: read skills/using-git-worktrees/SKILL.md
  EXPECT: Uso de worktree documentado.
  EVIDENCE: Lido `skills/using-git-worktrees/SKILL.md`. Documenta deteccao de worktree, criacao via ferramenta nativa ou fallback `git worktree add`, verificacao de `.gitignore` e baseline tests.

- [x] 0.3 Pesquisar Sand Castle / once.sh / afk.sh
  OUTCOME: Referencias de Pocock mapeadas.
  CHECK: web_search "Matt Pocock once.sh afk.sh Ralph" e/ou Inspecionar video
  EXPECT: Links/fontes listadas.
  EVIDENCE: Nenhuma ferramenta de web search disponivel neste ambiente. Fontes identificadas no plano: video `https://www.youtube.com/watch?v=-QFHIoCo-Ko` (timestamps 00:53:15.839-01:02:20.240), conceitos `once.sh`, `afk.sh` e `Ralph loop`, DAG de issues.

- [x] 0.4 Baseline audit + held-out
  OUTCOME: Estado atual passa.
  CHECK: python audit.py ; python -m pytest tests/held-out/ -q
  EXPECT: 0 erros; 135 passed.
  EVIDENCE: `python audit.py`: "ALL 31 CHECKS PASSED - NO ERRORS, NO WARNINGS". `python -m pytest tests/held-out/ -q`: "135 passed in 4.81s".

- [x] 0.5 Sintese de melhorias candidatas
  OUTCOME: Decidir criacao de skill afk-loop.
  CHECK: Revisar FASE 3 do plano.
  EXPECT: Decisao registrada.
  EVIDENCE: Decisao: implementar alternativa 1 — criar `skills/afk-loop/SKILL.md` com prompt/workflow para agente AFK. Nao modificar `executing-plans` (alternativa 2) nem adicionar script opcional (alternativa 3) nesta iteracao.

## Gates FASE 1-10

- [x] 1. Observar ausencia de skill AFK
  OUTCOME: Confirmar nao existe skill para issues locais.
  CHECK: grep -r "AFK\|Ralph\|issues.*md.*loop" skills/
  EXPECT: 0 matches relevantes.
  EVIDENCE: `grep` encontrou 10 matches: `triage` e `diagnosing-bugs` mencionam "AFK" em contexto de labels/estado; `wayfinder`, `ask-matt` e `setup-matt-pocock-skills` falam de tarefas AFK. Nenhuma skill consome `.devin/scratch/<feature>/issues/*.md` em loop autonomo.

- [x] 2. Criticar (Rule 4/10)
  OUTCOME: Justificar necessidade do loop noturno.
  CHECK: Documentar no ledger.
  EXPECT: Critica escrita.
  EVIDENCE: Regra 4 (skill discovery) e Regra 10 (planejar/verificar) sao atendidas manualmente, mas nao ha skill para "turno da noite". O agente so implementa quando coordenado; isso deixa de fora o padrao AFK (Ralph) de Pocock, perdendo produtividade de issues ja triadas.

- [x] 3. Gerar 3 alternativas
  OUTCOME: 3 alternativas listadas.
  CHECK: Revisar FASE 3 do plano.
  EXPECT: 3 alternativas.
  EVIDENCE: (1) Criar `skills/afk-loop/SKILL.md` com prompt de Ralph; (2) Adicionar secao "AFK mode" em `executing-plans`; (3) Criar script `.ps1`/`.sh` no repo para orquestrar o loop.

- [x] 4. Revisar e selecionar alternativa
  OUTCOME: Criar skill afk-loop separada.
  CHECK: Decisao no ledger.
  EXPECT: Escopo definido.
  EVIDENCE: Escolhida a alternativa 1: skill separada `afk-loop` para nao poluir `executing-plans` e manter o workflow autocontido, invocavel por `/afk-loop`.

- [x] 5. Validar com codigo
  OUTCOME: skills/afk-loop/SKILL.md criado.
  CHECK: python audit.py ; python -m pytest tests/held-out/ -q
  EXPECT: 0 erros; 135 passed.
  EVIDENCE: `skills/afk-loop/SKILL.md` criado. `python audit.py`: "ALL 31 CHECKS PASSED - NO ERRORS, NO WARNINGS". `python -m pytest tests/held-out/ -q`: "135 passed in 4.75s". `python scripts/validate-skill-format.py`: afk-loop score 100.

- [x] 6. Future pace
  OUTCOME: 3 cenarios avaliados.
  CHECK: Revisar FASE 6 do plano.
  EXPECT: Sim/Nao.
  EVIDENCE: (1) Usuario dorme enquanto agente trabalha — Sim. (2) Issues vem de PRD gerado no dia — Sim. (3) Paralelizacao com multiplos worktrees — Sim.

- [x] 7. Ecological check
  OUTCOME: Loop nao commita na main sem confirmacao; nao exige Docker.
  CHECK: Revisar skill.
  EXPECT: Garantias presentes.
  EVIDENCE: Skill `afk-loop/SKILL.md` possui secoes "Stop conditions" e "Safety rules" que proibem `git commit`/`git push` em `main`/`master` sem confirmacao humana, exigem worktree isolado, e proibem requisitar Docker.

- [x] 8. Simular
  OUTCOME: Criar issues de teste e invocar /afk-loop em worktree.
  CHECK: Testar com subagente ou script.
  EXPECT: Processa issues e para em issue vazia.
  EVIDENCE: Criado worktree em `$env:TEMP\afk-loop-sim` (branch `afk-loop-sim`), gerados `.devin/scratch/afk-demo/issues/01-base.md` e `02-depend.md` com `Blocked by: 01`. Script Python verificou: frontier inicial `['01']`; apos resolver 01, frontier `['02']`; apos resolver 02, frontier `[]` e "All issues resolved; loop stops as expected." Worktree removido e branch deletada.

- [x] 9. Classificar
  OUTCOME: Classificacao final.
  CHECK: Comparar baseline.
  EXPECT: MELHOROU / NEUTRO / PIOROU / INCONCLUSIVO.
  EVIDENCE: MELHOROU. Baseline (0 erros / 135 passed) mantido; adiciona skill `afk-loop` que preenche lacuna de loop AFK sobre issues locais.

- [x] 10. Commit e PR
  OUTCOME: Commit no branch.
  CHECK: git log --oneline -3
  EXPECT: Commit sem AI signature.
  EVIDENCE: SHA 0a2061d — `git log --oneline -3` confirma commit "add afk-loop skill and update counts" sem AI signature.