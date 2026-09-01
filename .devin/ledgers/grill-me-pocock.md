# Ledger: grill-me (Matt Pocock alignment via interrogation)

## Gates FASE 0

- [x] 0.1 Ler grilling SKILL.md e frontier
  OUTCOME: Entender skill atual.
  CHECK: read skills/grilling/SKILL.md e grilling-frontier.md
  EXPECT: Arquivos lidos e resumidos.
  EVIDENCE: Lidos `skills/grilling/SKILL.md` (206 linhas) e `.devin/ledgers/grilling-frontier.md` (118 linhas). Skill tem modos Default/Stateless/With-docs, frontier rounds, question format com `> <your recommended answer>` em Grill Mode, e design doc em `.devin/specs/YYYY-MM-DD-<topic>-design.md`.

- [x] 0.2 Comparar com exercício do workshop
  OUTCOME: Mapear diferenças entre skill atual e clientbrief.mmd.
  CHECK: Procurar clientbrief.mmd ou similar no repo.
  EXPECT: Exemplos encontrados.
  EVIDENCE: `find_file_by_name **/*.mmd` retornou vazio; `grep clientbrief` só encontrou referências no plano e neste ledger. Não há `clientbrief.mmd` no bundle. A prática do workshop (vídeo 00:15:02–00:22:03) é: `grill me` gera 20–100 perguntas, cada uma com recomendação, e o resultado é um `shared design concept`/asset da conversa. Skill atual tem recomendação apenas em `Propose 2-3 approaches` e no formato de pergunta da Phase 2, mas não em *todas* as perguntas e não exporta explicitamente como design concept.

- [x] 0.3 Verificar exemplos no bundle
  OUTCOME: Saber se há exemplos de uso.
  CHECK: grep -r "grill me" docs/ tests/ .devin/
  EXPECT: Matches listados.
  EVIDENCE: `grep -ri "grill me"` encontrou 19 matches: triggers no `skills/grilling/SKILL.md`, resumo no `.devin/notes/youtube/-QFHIoCo-Ko/video-analysis-WIP.md` (shared design concept, recomendação por pergunta, 20–100 perguntas), plano `docs/plans/2026-08-31-matt-pocock-grill-me.md`, e referências em ledgers/planos anteriores.

- [x] 0.4 Baseline audit + held-out
  OUTCOME: Estado atual passa em todos checks.
  CHECK: python audit.py ; python -m pytest tests/held-out/ -q
  EXPECT: 0 erros; 135 passed.
  EVIDENCE: `python audit.py` -> "ALL 31 CHECKS PASSED - NO ERRORS, NO WARNINGS" (exit 0); `python -m pytest tests/held-out/ -q` -> "135 passed in 4.75s" (exit 0).

- [x] 0.5 Síntese de melhorias candidatas
  OUTCOME: Decidir alternativa.
  CHECK: Revisar FASE 3 do plano.
  EXPECT: Uma alternativa escolhida.
  EVIDENCE: Alternativa 1 selecionada: atualizar `skills/grilling/SKILL.md` in-place com (a) perguntas assertivas, (b) recomendação em cada pergunta e (c) export do ativo de conversa como design concept.

## Gates FASE 1–10

- [x] 1. Observar SKILL.md atual
  OUTCOME: Confirmar ausência de recomendação/export.
  CHECK: grep -n "recommendation\|recomendação\|design concept\|export" skills/grilling/SKILL.md
  EXPECT: 0 matches.
  EVIDENCE: `grep` encontrou 2 matches apenas para "recommendation" em `Propose 2-3 approaches` (linhas 64, 124). Nenhum match para "design concept" ou "export". A recomendação não é obrigatória em *cada* pergunta e não há instrução de exportar o ativo da conversa como design concept.

- [x] 2. Criticar (Rule 4/7)
  OUTCOME: Justificar por que skill gasta mais tokens.
  CHECK: Documentar no ledger.
  EXPECT: Crítica escrita.
  EVIDENCE: Comportamento atual: `ask clarifying questions` e frontier questions podem ser enviadas sem recomendação. Intenção positiva: evitar assumir respostas do usuário. Falha: o usuário gasta mais tokens e turnos para articular uma resposta do zero; sem recomendação, o agente também não exporta um `shared design concept`, deixando o ativo da conversa subespecificado. Viola Rule 7 (opinion-silent) no sentido de que a skill se omite de oferecer a recomendação/opinião técnica que reduziria ciclos, e Rule 4 (não usar skill incompleta) porque `grilling` não entrega a interrogação assertiva e o asset prometidos pelo workshop.

- [x] 3. Gerar 3 alternativas
  OUTCOME: 3 alternativas documentadas.
  CHECK: Revisar FASE 3 do plano.
  EXPECT: 3 alternativas.
  EVIDENCE:

  | # | Alternativa | Risco | Prob. de melhoria real |
  |---|-------------|-------|------------------------|
  | 1 | **Adicionar recomendação padrão a cada pergunta em `grilling`** — manter skill única, incluir `> [sua recomendação]` em *todas* as perguntas (Phase 1 e Phase 2) e acrescentar export do ativo como `design concept`. | Baixo | Alto: resolve a falha sem mudar a superfície da skill. |
  | 2 | **Criar `/grill-me-with-recommendations` skill separada** — deixar `grilling` como está; nova skill só para modo Pocock. | Médio | Baixo: fragmenta descoberta e manutenção; duplica lógica de frontier. |
  | 3 | **Usar `ask_user_question` com `options` em vez de texto livre** — forçar todas as perguntas a serem múltipla-escolha com uma opção pré-selecionada. | Médio | Médio: ajuda em alguns casos, mas quebra perguntas abertas legítimas e não resolve o design concept. |

- [x] 4. Revisar e selecionar alternativa
  OUTCOME: Alternativa 1 escolhida (atualizar SKILL.md).
  CHECK: Decisão no ledger.
  EXPECT: Justificativa registrada.
  EVIDENCE: Selecionada alternativa 1: atualizar `skills/grilling/SKILL.md` em vez de criar skill separada. Justificativa: mantém superfície única, não duplica lógica, não quebra perguntas abertas, é a menor mudança que entrega recomendação por pergunta, assertividade e design concept.

- [x] 5. Validar com código
  OUTCOME: SKILL.md atualizado; teste com brief de exemplo.
  CHECK: python audit.py ; python -m pytest tests/held-out/ -q ; python scripts/validate-skill-format.py ; python -m pytest tests/validation/test_grilling_frontier_rounds.py -q
  EXPECT: 0 erros; 135 passed; skill format 100; frontier tests 7 passed.
  EVIDENCE: `python audit.py` -> "ALL 31 CHECKS PASSED"; `python -m pytest tests/held-out/ -q` -> "135 passed"; `validate-skill-format.py` -> `[PASS] grilling\SKILL.md (score: 100)`; `test_grilling_frontier_rounds.py` -> "7 passed".

- [x] 6. Future pace
  OUTCOME: 3 cenários avaliados.
  CHECK: Revisar FASE 6 do plano.
  EXPECT: Sim/Não anotados.
  EVIDENCE:
  1. Usuário passa menos mensagens porque cada pergunta já traz uma recomendação. Ajuda? Sim.
  2. Asset exportável vira PRD/design concept para `writing-plans`/`planning-pipeline`. Ajuda? Sim.
  3. Pareamento com PO/product owner melhora porque o agente entra com propostas concretas em vez de perguntas abertas. Ajuda? Sim.

- [x] 7. Ecological check
  OUTCOME: Skill não quebra grilling-frontier; tamanho ok.
  CHECK: diff --stat skills/grilling/SKILL.md ; grep regras frontier
  EXPECT: Mudanças controladas.
  EVIDENCE: `git diff --stat skills/grilling/SKILL.md` -> `27 insertions(+), 14 deletions(-)` em 1 arquivo. Nenhuma skill nova criada. Regras de frontier (`1-4 questions per call`, `recompute the frontier`, `2-4 options`, `never include a question...`) permanecem intactas. Nenhum arquivo em `tests/held-out/` modificado.

- [x] 8. Simular
  OUTCOME: Invocar /grilling com exemplo.
  CHECK: Testar fluxo mentalmente ou com subagente.
  EXPECT: Perguntas incluem recomendação.
  EVIDENCE: Simulação mental com brief de exemplo (aplicação de gestão de tarefas): perguntas de frontier agora seguem `Q1 - <título>: <proposta assertiva>\n> <recomendação>`; checklist exige recomendação em cada pergunta; resultado final é design concept com estrutura PRD. `grep` confirmou 13 matches para `recommendation alongside every question|shared design concept|design concept|PRD structure|recommended answer`.

- [x] 9. Classificar
  OUTCOME: Classificação final.
  CHECK: Comparar baseline.
  EXPECT: MELHOROU / NEUTRO / PIOROU / INCONCLUSIVO.
  EVIDENCE: Antes: skill não exigia recomendação em cada pergunta e não declarava export do ativo como design concept. Depois: todas as perguntas devem incluir recomendação, sessão termina em `shared design concept`, e entregável segue estrutura PRD. Audit, held-out e validation tests passam. Sem regressões.

  CLASSIFICAÇÃO: **MELHOROU**

- [x] 10. Commit e PR
  OUTCOME: Commit no branch.
  CHECK: git log --oneline -3
  EXPECT: Commit sem AI signature.
  EVIDENCE: `git log --oneline -3`:
  ```
  fd0ef8b feat(grilling): assertive questions, recommendation per question, design concept export
  ...
  ```
  Commit SHA: **fd0ef8b**. Mensagem neutra, sem assinatura de IA.
